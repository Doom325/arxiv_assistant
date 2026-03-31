"use client";

import { Cloud, ExternalLink, X, AlertCircle, Check } from "lucide-react";

interface GDriveAuthPanelProps {
  authUrl: string;
  authCode: string;
  onAuthCodeChange: (code: string) => void;
  onConfirmAuth: () => void;
  isAuthenticating: boolean;
  onClose: () => void;
}

export default function GDriveAuthPanel({
  authUrl,
  authCode,
  onAuthCodeChange,
  onConfirmAuth,
  isAuthenticating,
  onClose,
}: GDriveAuthPanelProps) {
  return (
    <div className="bg-surface-card rounded-2xl p-6 shadow-warm-sm">
      <div className="flex items-start gap-4">
        {/* Cloud icon */}
        <div className="bg-accent/15 rounded-xl p-2 shrink-0">
          <Cloud className="h-6 w-6 text-accent" />
        </div>

        <div className="flex-1 space-y-4">
          {/* Title */}
          <div>
            <h3 className="text-lg font-bold text-foreground mb-1">
              Google Drive Authentication
            </h3>
            <p className="text-foreground-secondary text-sm">
              To sync your papers, authorize the assistant to access your Google
              Drive. Follow the steps below:
            </p>
          </div>

          {/* Steps */}
          <div className="space-y-4 max-w-2xl">
            {/* Step 1 */}
            <div className="flex items-center gap-3 bg-surface-inset p-3 rounded-xl">
              <div className="bg-surface-inset rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold text-foreground-muted shrink-0">
                1
              </div>
              <a
                href={authUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-accent hover:text-accent-hover font-medium transition-colors"
              >
                Click here to authenticate with Google
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>

            {/* Step 2 */}
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className="bg-surface-inset rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold text-foreground-muted shrink-0">
                  2
                </div>
                <p className="text-foreground-secondary text-sm">
                  After approving, copy the{" "}
                  <span className="text-foreground font-medium">
                    &ldquo;code&rdquo; parameter
                  </span>{" "}
                  from the redirect URL and paste it below.
                </p>
              </div>

              <div className="ml-9 flex flex-col sm:flex-row gap-2">
                <input
                  type="text"
                  value={authCode}
                  onChange={(e) => onAuthCodeChange(e.target.value)}
                  placeholder="Paste the authorization code here..."
                  className="flex-1 bg-surface-inset text-foreground rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-accent/30 focus:outline-none"
                />
                <button
                  onClick={onConfirmAuth}
                  disabled={!authCode.trim() || isAuthenticating}
                  className="bg-accent text-on-accent rounded-full px-6 py-2 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAuthenticating ? "Verifying..." : "Complete Auth"}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Close button */}
        <button
          onClick={onClose}
          className="text-foreground-muted hover:text-foreground transition-colors shrink-0"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}

export function ExportStatusBanner({
  message,
  isError,
  onDismiss,
}: {
  message: string;
  isError: boolean;
  onDismiss: () => void;
}) {
  return (
    <div
      className={`p-4 rounded-xl flex items-center justify-between ${
        isError ? "bg-red-50 text-red-700" : "bg-green-50 text-green-700"
      }`}
    >
      <div className="flex items-center gap-2">
        {isError ? <AlertCircle size={16} /> : <Check size={16} />}
        <span className="text-sm font-medium">{message}</span>
      </div>
      <button onClick={onDismiss} className="text-sm hover:underline">
        Dismiss
      </button>
    </div>
  );
}
