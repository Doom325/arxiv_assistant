"use client";

import Link from "next/link";
import { Mail, GitBranch, ExternalLink, Check, AlertCircle } from "lucide-react";

interface PaperActionFooterProps {
  paperId: number | undefined;
  pdfUrl: string;
  emailStatus: "idle" | "sending" | "sent" | "error";
  onEmail: () => void;
}

export default function PaperActionFooter({
  paperId,
  pdfUrl,
  emailStatus,
  onEmail,
}: PaperActionFooterProps) {
  return (
    <div className="mt-16 flex flex-col sm:flex-row justify-center items-center gap-4">
      {/* Email Summary — secondary */}
      <button
        onClick={onEmail}
        disabled={emailStatus === "sending"}
        className={`px-6 py-3 rounded-xl font-medium transition-colors flex items-center justify-center shadow-warm-sm ${
          emailStatus === "sent"
            ? "bg-emerald-500 text-white"
            : emailStatus === "error"
              ? "bg-red-500 text-white"
              : "bg-surface-card text-foreground hover:bg-surface-inset"
        }`}
      >
        {emailStatus === "sending" ? (
          <>
            <div className="h-5 w-5 border-2 border-foreground-muted/30 border-t-foreground rounded-full animate-spin mr-2" />
            Sending...
          </>
        ) : emailStatus === "sent" ? (
          <>
            <Check className="h-5 w-5 mr-2" />
            Email Sent!
          </>
        ) : emailStatus === "error" ? (
          <>
            <AlertCircle className="h-5 w-5 mr-2" />
            Failed
          </>
        ) : (
          <>
            <Mail className="h-5 w-5 mr-2" />
            Email Summary
          </>
        )}
      </button>

      {/* Show Timeline — secondary */}
      <Link
        href={`/timeline?paper=${paperId}`}
        className="bg-surface-card text-foreground rounded-xl px-6 py-3 font-medium shadow-warm-sm hover:bg-surface-inset transition-colors flex items-center justify-center"
      >
        <GitBranch className="h-5 w-5 mr-2" />
        Show Timeline
      </Link>

      {/* Read Full PDF — primary accent */}
      <a
        href={pdfUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="bg-accent text-on-accent rounded-full px-8 py-3 font-medium shadow-warm-sm hover:bg-accent-hover transition-colors flex items-center justify-center"
      >
        Read Full PDF
        <ExternalLink className="h-4 w-4 ml-2" />
      </a>
    </div>
  );
}
