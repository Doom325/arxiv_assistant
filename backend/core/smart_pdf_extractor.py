"""Adaptive PDF text extraction using pymupdf (fitz).

Two-pass approach:
  1. Profile the document to discover body font, section header styles,
     page header/footer zones, and figure/caption fonts.
  2. Walk every line and emit structured sections based on the profile.

Falls back gracefully — callers should wrap in try/except and use the old
regex pipeline (text_utils.extract_all_sections) on failure.
"""

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import fitz  # pymupdf

from core.text_utils import sanitize_text

logger = logging.getLogger(__name__)

MAX_SECTION_CHARS = 30_000
REFERENCES_MAX_CHARS = 500

# Well-known top-level section names (case-insensitive match)
WELL_KNOWN_SECTIONS = {
    "abstract", "introduction", "background", "related work",
    "related works", "methods", "method", "methodology",
    "approach", "model", "experiments", "experiment",
    "experimental setup", "experimental results", "results",
    "evaluation", "discussion", "analysis", "conclusion",
    "conclusions", "future work", "limitations",
    "acknowledgements", "acknowledgments", "acknowledgement",
    "references", "bibliography", "appendix", "appendices",
    "supplementary material", "supplementary materials",
    "impact statement", "ethics statement", "broader impact",
}

# Pattern for numbered section headers like "1", "1.", "3.1", "A.2", "A."
NUMBERED_PATTERN = re.compile(
    r"^([A-Z]?\d+(?:\.\d+)*\.?)\s+(.+)$"
)

# Roman numeral pattern for headers like "III. Results"
ROMAN_PATTERN = re.compile(
    r"^(I{1,3}|IV|V|VI{0,3}|IX|X{0,3})\.?\s+(.+)$"
)


@dataclass
class SpanInfo:
    """Lightweight record for a single text span."""
    font: str
    size: float  # rounded to 0.5pt
    bold: bool
    y: float
    text: str
    page: int
    block_no: int
    line_no: int
    x0: float = 0.0
    x1: float = 0.0


@dataclass
class LineInfo:
    """Aggregated info for one line (all spans merged)."""
    spans: list[SpanInfo]
    page: int
    block_no: int
    line_no: int
    bbox: tuple  # (x0, y0, x1, y1)

    @property
    def text(self) -> str:
        return " ".join(s.text for s in self.spans)

    @property
    def dominant_size(self) -> float:
        if not self.spans:
            return 0
        # Size of the span with most text
        return max(self.spans, key=lambda s: len(s.text)).size

    @property
    def dominant_bold(self) -> bool:
        if not self.spans:
            return False
        total = sum(len(s.text) for s in self.spans)
        bold_chars = sum(len(s.text) for s in self.spans if s.bold)
        return bold_chars > total * 0.6

    @property
    def all_bold(self) -> bool:
        return all(s.bold for s in self.spans)

    @property
    def char_count(self) -> int:
        return sum(len(s.text) for s in self.spans)


@dataclass
class DocumentProfile:
    """Formatting profile discovered during pass 1."""
    body_font: str = ""
    body_size: float = 10.0
    body_bold: bool = False
    # Each entry: (font, size, bold) for styles used as section headers
    header_styles: list = field(default_factory=list)
    page_header_zones: list = field(default_factory=list)  # (y_min, y_max)
    figure_fonts: set = field(default_factory=set)
    page_count: int = 0
    page_heights: list = field(default_factory=list)
    page_widths: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _font_families_match(family_a: str, family_b: str) -> bool:
    """Check if two font family roots likely belong to the same family.

    Handles variants like NimbusRomNo9L-Regu vs NimbusRomNo9L-Medi.
    Also handles common patterns where the bold/italic variant has a
    slightly different root (e.g., "arial" vs "arialmt").
    """
    if family_a == family_b:
        return True
    # Check if one is a prefix of the other (handles "arial" vs "arialmt")
    if family_a.startswith(family_b) or family_b.startswith(family_a):
        return True
    # Strip common suffixes
    for suffix in ("mt", "ps", "lt", "ce"):
        a = family_a.rstrip(suffix) if family_a.endswith(suffix) else family_a
        b = family_b.rstrip(suffix) if family_b.endswith(suffix) else family_b
        if a == b:
            return True
    return False


def _round_size(size: float) -> float:
    """Round font size to nearest 0.5pt."""
    return round(size * 2) / 2


def _is_bold(font_name: str, flags: int) -> bool:
    """Heuristic bold detection from font name and span flags."""
    if flags & (1 << 4):  # fitz bold flag
        return True
    name_lower = font_name.lower()
    return any(tag in name_lower for tag in ("bold", "demi", "heavy", "black"))


def _collect_lines(doc: fitz.Document) -> list[LineInfo]:
    """Collect all lines from the document, each with its constituent spans."""
    lines: list[LineInfo] = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for block in blocks:
            if block["type"] != 0:  # skip image blocks
                continue
            for line_idx, line in enumerate(block["lines"]):
                spans_in_line: list[SpanInfo] = []
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    spans_in_line.append(SpanInfo(
                        font=span["font"],
                        size=_round_size(span["size"]),
                        bold=_is_bold(span["font"], span["flags"]),
                        y=span["bbox"][1],
                        text=text,
                        page=page_num,
                        block_no=block["number"],
                        line_no=line_idx,
                        x0=span["bbox"][0],
                        x1=span["bbox"][2],
                    ))
                if spans_in_line:
                    lines.append(LineInfo(
                        spans=spans_in_line,
                        page=page_num,
                        block_no=block["number"],
                        line_no=line_idx,
                        bbox=tuple(line["bbox"]),
                    ))
    return lines


def _strip_section_number(text: str) -> str:
    """Strip leading section number from text for name matching."""
    m = NUMBERED_PATTERN.match(text.strip())
    if m:
        return m.group(2).strip()
    m = ROMAN_PATTERN.match(text.strip())
    if m:
        return m.group(2).strip()
    return text.strip()


# ---------------------------------------------------------------------------
# Pass 1: Profile
# ---------------------------------------------------------------------------

def profile_document(doc: fitz.Document) -> DocumentProfile:
    """Analyze the PDF to discover formatting patterns."""
    profile = DocumentProfile()
    profile.page_count = len(doc)
    profile.page_heights = [doc[i].rect.height for i in range(len(doc))]
    profile.page_widths = [doc[i].rect.width for i in range(len(doc))]

    lines = _collect_lines(doc)
    if not lines:
        return profile

    # Flatten all spans for frequency analysis
    all_spans = [s for ln in lines for s in ln.spans]

    # --- 1. Body text style: most frequent (font, size, bold) combo ---
    style_counter: Counter = Counter()
    for s in all_spans:
        style_counter[(s.font, s.size, s.bold)] += len(s.text)

    body_style = style_counter.most_common(1)[0][0]
    profile.body_font = body_style[0]
    profile.body_size = body_style[1]
    profile.body_bold = body_style[2]

    # --- 2. Page header/footer detection ---
    y_groups: dict[int, list[SpanInfo]] = defaultdict(list)
    for s in all_spans:
        y_bucket = round(s.y / 5) * 5
        y_groups[y_bucket].append(s)

    avg_page_height = sum(profile.page_heights) / len(profile.page_heights)

    for y_bucket, bucket_spans in y_groups.items():
        unique_pages = set(s.page for s in bucket_spans)
        threshold = min(3, max(2, int(profile.page_count * 0.3)))
        if len(unique_pages) < threshold:
            continue

        # Must be at top or bottom of page
        if y_bucket > 80 and y_bucket < (avg_page_height - 60):
            continue

        # Check content similarity: running headers/footers repeat similar text
        # across pages. If the text varies significantly, it's content, not a header.
        texts = [s.text.strip().lower() for s in bucket_spans]
        text_counter = Counter(texts)
        most_common_text, most_common_count = text_counter.most_common(1)[0]

        # Require either:
        # - The most common text appears on 40%+ of pages with this zone, OR
        # - The text is very short (page numbers, etc.) and appears on many pages
        is_repetitive = most_common_count >= len(unique_pages) * 0.4
        is_page_number = most_common_text.isdigit() or len(most_common_text) <= 3
        is_very_frequent = len(unique_pages) >= profile.page_count * 0.5

        if not (is_repetitive or (is_page_number and is_very_frequent)):
            continue

        y_min = y_bucket - 8
        y_max = y_bucket + 8
        profile.page_header_zones.append((y_min, y_max))

    # --- 3. Section header styles ---
    # Look at lines that are short (not full paragraphs), bolder/larger than body,
    # and appear as isolated lines in their block.
    header_candidates: Counter = Counter()
    for ln in lines:
        # Headers are typically short lines
        if ln.char_count > 100 or ln.char_count < 2:
            continue

        dom_size = ln.dominant_size
        dom_bold = ln.dominant_bold

        if dom_size < profile.body_size:
            continue

        is_larger = dom_size > profile.body_size
        is_bolder = dom_bold and not profile.body_bold

        if not (is_larger or is_bolder):
            continue

        # Record the dominant style of this candidate header line
        for s in ln.spans:
            if s.size >= profile.body_size and (s.bold or s.size > profile.body_size):
                style_key = (s.font, s.size, s.bold)
                header_candidates[style_key] += 1

    # Extract the font family root from body font for comparison
    # e.g. "NimbusRomNo9L-Regu" -> "nimbusromno9l"
    body_family = profile.body_font.split("-")[0].lower().rstrip("0123456789")

    for style_key, count in header_candidates.most_common():
        if count < 2:
            break
        font, size, bold = style_key
        # Only accept fonts from the same family as body text
        # This filters out figure/diagram fonts (ComicSans, Calibri, etc.)
        cand_family = font.split("-")[0].lower().rstrip("0123456789")
        if cand_family != body_family and not _font_families_match(body_family, cand_family):
            continue
        profile.header_styles.append(style_key)

    # --- 4. Figure/table text: different font family, smaller than body ---
    font_families: Counter = Counter()
    for s in all_spans:
        font_families[s.font] += len(s.text)

    body_char_count = font_families.get(profile.body_font, 0)
    for font_name, char_count in font_families.items():
        if font_name == profile.body_font:
            continue
        if char_count < body_char_count * 0.05:
            font_spans = [s for s in all_spans if s.font == font_name]
            if font_spans and all(s.size < profile.body_size for s in font_spans):
                profile.figure_fonts.add(font_name)

    return profile


# ---------------------------------------------------------------------------
# Pass 2: Extract structured sections (line-level decisions)
# ---------------------------------------------------------------------------

def _in_header_zone(y: float, profile: DocumentProfile) -> bool:
    """Check if a y-position falls in a detected page header/footer zone."""
    for y_min, y_max in profile.page_header_zones:
        if y_min <= y <= y_max:
            return True
    return False


def _classify_line_as_header(ln: LineInfo, profile: DocumentProfile) -> tuple[bool, int, str]:
    """Decide if an entire line is a section header.

    Key principle: a section header is a SHORT, standalone line where the
    dominant style is distinctly different from body text (larger and/or bolder).
    Lines that mix header-styled spans with body-styled spans are NOT headers
    (they are paragraphs with inline bold).

    Returns (is_header, level, title_text).
    """
    text = ln.text.strip()
    if not text:
        return False, 0, ""

    # Length filter: headers are short
    if len(text) > 100:
        return False, 0, ""
    if len(text) < 2:
        return False, 0, ""

    dom_size = ln.dominant_size
    dom_bold = ln.dominant_bold

    # Must be at least body size
    if dom_size < profile.body_size:
        return False, 0, ""

    is_larger = dom_size > profile.body_size
    is_bolder = dom_bold and not profile.body_bold

    # Check if line style matches a known header style
    style_match = False
    for s in ln.spans:
        if (s.font, s.size, s.bold) in profile.header_styles:
            style_match = True
            break

    if not style_match and not (is_larger or is_bolder):
        return False, 0, ""

    # Font family check: reject lines from non-body font families entirely
    # (these are figure/diagram text, not section headers)
    body_family = profile.body_font.split("-")[0].lower().rstrip("0123456789")
    for s in ln.spans:
        span_family = s.font.split("-")[0].lower().rstrip("0123456789")
        if span_family != body_family and not _font_families_match(body_family, span_family):
            return False, 0, ""

    # Critical check: if the line has a mix of header-styled and body-styled
    # spans, it's likely a paragraph line with inline bold, not a header.
    # For a header, we want ALL or nearly all chars in header style.
    if ln.char_count > 0:
        header_chars = 0
        for s in ln.spans:
            if (s.font, s.size, s.bold) in profile.header_styles:
                header_chars += len(s.text)
            elif s.bold and s.size >= profile.body_size:
                header_chars += len(s.text)
        # At least 70% of the line must be in header style
        if header_chars < ln.char_count * 0.7:
            return False, 0, ""

    # Structural pattern checks
    stripped = _strip_section_number(text)
    m_num = NUMBERED_PATTERN.match(text)
    m_rom = ROMAN_PATTERN.match(text)
    is_well_known = stripped.lower().rstrip(".") in WELL_KNOWN_SECTIONS
    is_numbered = m_num is not None
    is_roman = m_rom is not None

    # For numbered patterns, require the number part to look like a section
    # number (e.g. "3.", "3.1", "A.2") not a step number (e.g. "1. Step 1")
    if is_numbered and not is_well_known:
        num_part = m_num.group(1).rstrip(".")
        title_part = m_num.group(2).strip()
        # Reject if it looks like a numbered list item rather than a section
        # (e.g., "1. Step 1 : Input action..." or "2. Main Annotation:")
        # Real section headers: "1. Introduction", "3.1. Preliminaries"
        # Heuristic: if the title part contains ":" mid-text, it's likely a label
        if ":" in title_part and not title_part.endswith(":"):
            return False, 0, ""

    # If same size as body, apply stricter rules
    if dom_size == profile.body_size:
        # Must be bold (and body is not bold)
        if not is_bolder:
            if not (is_well_known or is_numbered or is_roman):
                return False, 0, ""

        # For body-sized bold text, require structural evidence:
        # - Well-known section name, OR
        # - Numbered/roman pattern, OR
        # - Short label that ends with "." (subsection label like "Overview.")
        #   but NOT labels ending with ":" (those are field labels like "Tips:")
        text_clean = text.rstrip()
        ends_with_colon = text_clean.endswith(":")
        ends_with_period = text_clean.endswith(".")
        has_numbered_prefix = is_numbered and "." in m_num.group(1) if is_numbered else False

        if is_well_known or has_numbered_prefix or is_roman:
            pass  # accept
        elif is_numbered:
            # Top-level numbered like "1. Introduction" — accept only if title
            # part looks like a real section name (starts with uppercase, no colon)
            title_part = m_num.group(2).strip()
            if ends_with_colon or len(title_part) > 60:
                return False, 0, ""
        elif ends_with_period and len(text) <= 50:
            pass  # short bold label ending with period (e.g. "Overview.")
        elif ends_with_colon:
            return False, 0, ""  # field label like "Tips:", "Available Actions:"
        elif len(text) <= 40 and text[0].isupper():
            pass  # short bold title like "Comparison of Strategies"
        else:
            return False, 0, ""

    # Reject lines that start with bullet markers
    if text.startswith("•") or text.startswith("-") or text.startswith("–"):
        return False, 0, ""

    # Determine level
    if dom_size >= profile.body_size + 1.5:
        level = 1
    elif dom_size > profile.body_size:
        level = 1
    else:
        level = 2  # same size as body, just bold

    # Numbered sections: top-level if "3", subsection if "3.1"
    if m_num:
        num_part = m_num.group(1).rstrip(".")
        if "." in num_part:
            level = 2
        else:
            level = 1

    if m_rom:
        level = 1

    # Well-known top-level names override to level 1
    if is_well_known and not (m_num and "." in m_num.group(1).rstrip(".")):
        level = 1

    return True, level, text


def extract_sections_smart(doc: fitz.Document, profile: DocumentProfile) -> list[dict]:
    """Extract structured sections using the document profile."""
    sections: list[dict] = []
    current_title = "Preamble"
    current_level = 1
    current_content_parts: list[str] = []
    current_page_start = 0
    section_order = 0

    prev_y = -1.0
    prev_page = -1
    prev_block = -1

    def _flush_section():
        nonlocal section_order
        content = "\n".join(current_content_parts).strip()
        # Collapse multiple blank lines into one
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = sanitize_text(content)

        # Truncate references
        if re.match(r"(?i)^\s*(references|bibliography)", current_title):
            content = content[:REFERENCES_MAX_CHARS]

        content = content[:MAX_SECTION_CHARS]

        sections.append({
            "title": current_title,
            "level": current_level,
            "content": content,
            "order": section_order,
            "page_start": current_page_start,
        })
        section_order += 1

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

        for block in blocks:
            if block["type"] != 0:
                continue

            block_no = block["number"]

            for line_idx, line in enumerate(block["lines"]):
                # Build spans for this line, filtering out header zones and figure fonts
                filtered_spans: list[SpanInfo] = []
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue

                    si = SpanInfo(
                        font=span["font"],
                        size=_round_size(span["size"]),
                        bold=_is_bold(span["font"], span["flags"]),
                        y=span["bbox"][1],
                        text=text,
                        page=page_num,
                        block_no=block_no,
                        line_no=line_idx,
                        x0=span["bbox"][0],
                        x1=span["bbox"][2],
                    )

                    # Skip page header/footer zones
                    if _in_header_zone(si.y, profile):
                        continue

                    # Skip figure/caption fonts smaller than body
                    if si.font in profile.figure_fonts and si.size < profile.body_size:
                        continue

                    filtered_spans.append(si)

                if not filtered_spans:
                    continue

                ln = LineInfo(
                    spans=filtered_spans,
                    page=page_num,
                    block_no=block_no,
                    line_no=line_idx,
                    bbox=tuple(line["bbox"]),
                )

                # Check if this line is a section header
                is_hdr, lvl, hdr_text = _classify_line_as_header(ln, profile)

                if is_hdr:
                    _flush_section()
                    current_title = hdr_text
                    current_level = lvl
                    current_content_parts = []
                    current_page_start = page_num + 1
                    prev_y = -1.0
                    prev_page = page_num
                    prev_block = block_no
                    continue

                # Regular content line
                joined = " ".join(s.text for s in filtered_spans)

                # Detect paragraph breaks
                new_block = (block_no != prev_block and prev_block >= 0)
                new_page = (page_num != prev_page and prev_page >= 0)
                big_y_gap = False
                if prev_y >= 0 and page_num == prev_page:
                    y_current = line["bbox"][1]
                    gap = y_current - prev_y
                    line_height = profile.body_size * 1.4
                    if gap > line_height * 1.8:
                        big_y_gap = True

                if (new_block or new_page or big_y_gap) and current_content_parts:
                    current_content_parts.append("")  # paragraph break

                current_content_parts.append(joined)
                prev_y = line["bbox"][3]  # bottom-y
                prev_page = page_num
                prev_block = block_no

    # Flush final section
    _flush_section()

    return sections


# ---------------------------------------------------------------------------
# Pass 3: Deduplicate and clean
# ---------------------------------------------------------------------------

def deduplicate_sections(sections: list[dict], paper_title: str = "") -> list[dict]:
    """Remove empty sections, merge page-break duplicates, remove leaked headers."""
    if not sections:
        return sections

    # 1. Remove sections with empty content and generic/empty title
    cleaned = []
    for s in sections:
        if not s["content"].strip() and s["title"] in ("", "Preamble"):
            continue
        cleaned.append(s)
    sections = cleaned

    # 2. Merge consecutive sections with same title (page-break artifacts)
    merged: list[dict] = []
    for s in sections:
        if merged and merged[-1]["title"].strip().lower() == s["title"].strip().lower():
            sep = "\n\n" if merged[-1]["content"] else ""
            merged[-1]["content"] = (merged[-1]["content"] + sep + s["content"])[:MAX_SECTION_CHARS]
        else:
            merged.append(dict(s))  # copy
    sections = merged

    # 3. Remove sections whose title appears 3+ times (likely leaked page header)
    title_counts: Counter = Counter()
    for s in sections:
        title_counts[s["title"].strip().lower()] += 1
    sections = [
        s for s in sections
        if title_counts[s["title"].strip().lower()] < 3
    ]

    # 4. Also check against paper title
    if paper_title:
        title_lower = paper_title.lower().strip()
        sections = [
            s for s in sections
            if not (
                title_counts.get(s["title"].strip().lower(), 0) >= 2
                and s["title"].strip().lower() in title_lower
            )
        ]

    # 5. Split sections that contain embedded References
    # This happens when the References header was in a page header zone and
    # got filtered, so references text bleeds into the preceding section.
    new_sections = []
    for s in sections:
        content = s["content"]
        if re.match(r"(?i)^\s*(references|bibliography)", s["title"]):
            new_sections.append(s)
            continue

        # Strategy A: look for explicit "References" or "Bibliography" heading in text
        ref_match = re.search(
            r"\n\s*(References|Bibliography)\s*\n",
            content, re.IGNORECASE,
        )
        if ref_match:
            before = content[:ref_match.start()].strip()
            after = content[ref_match.end():].strip()[:REFERENCES_MAX_CHARS]
            s_copy = dict(s)
            s_copy["content"] = before
            new_sections.append(s_copy)
            new_sections.append({
                "title": ref_match.group(1).strip(),
                "level": 1,
                "content": after,
                "order": 0,
            })
            continue

        # Strategy B: detect bibliography entries pattern [1], [2], etc.
        # Look for a run of 5+ bibliography entries in quick succession
        bib_pattern = re.compile(r"^\[(\d+)\]\s", re.MULTILINE)
        bib_matches = list(bib_pattern.finditer(content))
        if len(bib_matches) >= 5:
            # Find where the bibliography starts (first entry [1] or similar)
            # Look for the first entry where numbers are sequential
            for i, m in enumerate(bib_matches):
                num = int(m.group(1))
                if num <= 2:  # bibliography likely starts at [1] or [2]
                    split_pos = m.start()
                    before = content[:split_pos].strip()
                    after = content[split_pos:].strip()[:REFERENCES_MAX_CHARS]
                    if before:  # only split if there's content before
                        s_copy = dict(s)
                        s_copy["content"] = before
                        new_sections.append(s_copy)
                        new_sections.append({
                            "title": "References",
                            "level": 1,
                            "content": after,
                            "order": 0,
                        })
                        break
            else:
                new_sections.append(s)
        else:
            new_sections.append(s)
    sections = new_sections

    # 6. Remove very short single-word "sections" that are likely table cells
    # (e.g., "Environment", "Action", "Description" from table headers)
    sections = [
        s for s in sections
        if not (
            not s["content"].strip()
            and len(s["title"].split()) <= 2
            and s["title"].strip().lower() not in WELL_KNOWN_SECTIONS
            and not NUMBERED_PATTERN.match(s["title"].strip())
            and not ROMAN_PATTERN.match(s["title"].strip())
        )
    ]

    # 5. Re-number orders
    for i, s in enumerate(sections):
        s["order"] = i

    # 6. Strip page_start from output (not in original schema)
    for s in sections:
        s.pop("page_start", None)

    return sections


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def extract_paper_smart(pdf_path: str) -> list[dict]:
    """Full adaptive extraction pipeline.

    Returns a list of section dicts compatible with PaperSection:
        {"title": str, "level": int, "content": str, "order": int}
    """
    doc = fitz.open(pdf_path)
    try:
        profile = profile_document(doc)
        logger.info(
            "PDF profile: body=%s@%.1fpt, %d header styles, %d header zones, %d figure fonts",
            profile.body_font, profile.body_size, len(profile.header_styles),
            len(profile.page_header_zones), len(profile.figure_fonts),
        )
        sections = extract_sections_smart(doc, profile)
        sections = deduplicate_sections(sections)
    finally:
        doc.close()

    return sections
