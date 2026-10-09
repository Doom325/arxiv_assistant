import React from "react";
import type { Components } from "react-markdown";

/**
 * Normalizes markdown content so that tables following list items, headers,
 * or paragraphs without a blank line are properly formatted for CommonMark / GFM parsing.
 */
export function formatMarkdownTables(content?: string | null): string {
  if (!content) return "";
  let text = content.replace(/\r\n/g, "\n");

  // Ensure blank line before tables (matches table header + delimiter rows)
  text = text.replace(
    /([^\n])\n([ \t]*\|?[^\n]+\|[^\n]*\n[ \t]*\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)+)/g,
    "$1\n\n$2"
  );

  // Ensure blank line after tables if followed immediately by non-table text
  text = text.replace(
    /(\|[^\n]+\|[ \t]*)\n([^\n|])/g,
    "$1\n\n$2"
  );

  return text;
}

/**
 * Custom ReactMarkdown components for rendering responsive, well-styled GFM tables
 * that integrate with the theme's surface, border, and typography tokens.
 */
export const markdownTableComponents: Components = {
  table: ({ children, ...props }: React.ComponentPropsWithoutRef<"table">) => (
    <div className="my-6 w-full overflow-x-auto rounded-xl border border-foreground/15 bg-surface-card shadow-sm">
      <table className="w-full text-left text-xs sm:text-sm border-collapse" {...props}>
        {children}
      </table>
    </div>
  ),
  thead: ({ children, ...props }: React.ComponentPropsWithoutRef<"thead">) => (
    <thead
      className="bg-surface-inset/60 border-b border-foreground/15 text-foreground font-semibold"
      {...props}
    >
      {children}
    </thead>
  ),
  tbody: ({ children, ...props }: React.ComponentPropsWithoutRef<"tbody">) => (
    <tbody
      className="divide-y divide-foreground/10 text-foreground-secondary"
      {...props}
    >
      {children}
    </tbody>
  ),
  tr: ({ children, ...props }: React.ComponentPropsWithoutRef<"tr">) => (
    <tr
      className="transition-colors hover:bg-surface-inset/30"
      {...props}
    >
      {children}
    </tr>
  ),
  th: ({ children, ...props }: React.ComponentPropsWithoutRef<"th">) => (
    <th
      className="px-4 py-3 font-semibold text-foreground tracking-wide border-r border-foreground/10 last:border-r-0"
      {...props}
    >
      {children}
    </th>
  ),
  td: ({ children, ...props }: React.ComponentPropsWithoutRef<"td">) => (
    <td
      className="px-4 py-3 align-top border-r border-foreground/10 last:border-r-0 leading-relaxed text-foreground-secondary"
      {...props}
    >
      {children}
    </td>
  ),
};
