"""Shared text utilities for sanitization and section extraction."""

import re


def sanitize_text(text: str) -> str:
    """Remove null bytes and UTF-16 surrogates that cause encoding/API errors."""
    if not text:
        return ""
    text = text.replace("\x00", "")
    return "".join(c for c in text if not (0xD800 <= ord(c) <= 0xDFFF))


def extract_sections(full_text: str) -> dict:
    """Extract Abstract and Introduction sections using regex heuristics."""
    lower_text = full_text.lower()

    # --- ABSTRACT ---
    abstract_start_match = re.search(r'(^|\n)\s*abstract[:.]?\s*', lower_text)
    if not abstract_start_match:
        abstract_text = ""
    else:
        abstract_start_idx = abstract_start_match.start()
        intro_start_match = re.search(
            r'(^|\n)\s*(1\.?|i\.?|I\.?)?\s*introduction[:.]?\s*',
            lower_text[abstract_start_idx:]
        )
        if intro_start_match:
            abstract_end_idx = abstract_start_idx + intro_start_match.start()
            abstract_text = full_text[abstract_start_idx:abstract_end_idx]
        else:
            abstract_text = full_text[abstract_start_idx:abstract_start_idx + 2000]

        abstract_text = re.sub(
            r'^\s*abstract[:.]?\s*', '', abstract_text.strip(), flags=re.IGNORECASE
        )

    # --- INTRODUCTION ---
    intro_text = ""
    intro_start_match = re.search(
        r'(^|\n)\s*(1\.?|i\.?|I\.?)?\s*introduction[:.]?\s*', lower_text
    )
    if intro_start_match:
        intro_start_idx = intro_start_match.end()
        search_region = lower_text[intro_start_idx:intro_start_idx + 5000]
        next_section_pattern = (
            r'(^|\n)\s*(2\.?|ii\.?|II\.?|related work|background|method|model|preliminaries)'
        )
        next_section_match = re.search(next_section_pattern, search_region)
        if next_section_match:
            intro_end_idx = intro_start_idx + next_section_match.start()
            intro_text = full_text[intro_start_idx:intro_end_idx]
        else:
            intro_text = full_text[intro_start_idx:intro_start_idx + 3000]
        intro_text = intro_text.strip()

    return {"abstract": abstract_text, "introduction": intro_text}


def extract_all_sections(full_text: str) -> list[dict]:
    """Extract all sections from a full paper text using regex heuristics.

    Two-pass strategy:
      1. Find section header positions via numbered, roman, and well-known patterns.
      2. Slice text between consecutive headers.

    Returns a list of dicts with keys: title, level, content, order.
    Falls back to a single "Full Text" entry when fewer than 2 headers are found.
    """
    if not full_text:
        return [{"title": "Full Text", "level": 1, "content": "", "order": 0}]

    MAX_SECTION_CHARS = 30_000
    REFERENCES_MAX_CHARS = 500

    # Well-known top-level headers (unnumbered)
    WELL_KNOWN = (
        r"Abstract|Conclusion|Conclusions|References|Acknowledgements"
        r"|Acknowledgments|Appendix|Bibliography|Related Work|Discussion"
    )

    # --- Pass 1: find all section header positions ---
    headers: list[tuple[int, int, str, int]] = []  # (start, end, title, level)

    # Numbered sections: 1. Introduction, 2 Methods, 3.1 Dataset
    for m in re.finditer(
        r'\n\s*(\d+(?:\.\d+)*)\s*\.?\s+([A-Z][^\n]{0,100})', full_text
    ):
        num_part = m.group(1)
        title_text = m.group(2).strip().rstrip(".")
        level = 1 if "." not in num_part else 2
        full_title = f"{num_part} {title_text}"
        headers.append((m.start(), m.end(), full_title, level))

    # Roman numeral sections: III. Results, IV Discussion
    for m in re.finditer(
        r'\n\s*(I{1,3}|IV|VI{0,3}|IX|X{0,3})\s*\.?\s+([A-Z][^\n]{0,100})',
        full_text,
    ):
        roman = m.group(1)
        title_text = m.group(2).strip().rstrip(".")
        full_title = f"{roman} {title_text}"
        headers.append((m.start(), m.end(), full_title, 1))

    # Unnumbered well-known headers
    for m in re.finditer(
        rf'\n\s*({WELL_KNOWN})\s*\n', full_text, re.IGNORECASE
    ):
        title_text = m.group(1).strip()
        headers.append((m.start(), m.end(), title_text, 1))

    # --- Fallback ---
    if len(headers) < 2:
        return [
            {
                "title": "Full Text",
                "level": 1,
                "content": sanitize_text(full_text[:100_000]),
                "order": 0,
            }
        ]

    # --- Pass 2: sort by position and slice ---
    headers.sort(key=lambda h: h[0])

    sections: list[dict] = []
    for idx, (start, end, title, level) in enumerate(headers):
        # Content runs from end of this header to start of the next header
        if idx + 1 < len(headers):
            content = full_text[end : headers[idx + 1][0]]
        else:
            content = full_text[end:]

        content = sanitize_text(content.strip())

        # Truncate references section
        if re.match(r"(?i)references|bibliography", title):
            content = content[:REFERENCES_MAX_CHARS]

        # Cap individual sections
        content = content[:MAX_SECTION_CHARS]

        sections.append(
            {
                "title": title,
                "level": level,
                "content": content,
                "order": idx,
            }
        )

    return sections
