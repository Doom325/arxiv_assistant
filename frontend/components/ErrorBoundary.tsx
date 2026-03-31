"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";

interface Props {
    children?: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="flex flex-col items-center justify-center min-h-[400px] p-8 bg-surface-card border border-border-default rounded-xl text-center">
                    <AlertTriangle className="h-12 w-12 text-amber-500 mb-4" />
                    <h2 className="text-xl font-bold text-foreground mb-2">Something went wrong</h2>
                    <p className="text-foreground-secondary max-w-md mx-auto mb-6">
                        An error occurred while rendering this section of the app. This could be due to unexpected data format.
                    </p>
                    <button
                        onClick={() => {
                            this.setState({ hasError: false });
                            window.location.reload();
                        }}
                        className="inline-flex items-center px-4 py-2 bg-accent hover:bg-accent/90 text-white rounded-md transition-colors"
                    >
                        <RefreshCcw className="h-4 w-4 mr-2" />
                        Reload Page
                    </button>

                    {process.env.NODE_ENV === "development" && this.state.error && (
                        <div className="mt-8 text-left bg-black p-4 rounded border border-border-default overflow-auto max-w-full">
                            <p className="text-red-400 font-mono text-xs">{this.state.error.toString()}</p>
                        </div>
                    )}
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
