"use client";

import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";
import RippleButton from "./RippleButton";
import Link from "next/link";

interface EmptyStateProps {
    icon: LucideIcon;
    title: string;
    description: string;
    actionLabel?: string;
    actionHref?: string;
    onAction?: () => void;
}

export default function EmptyState({ icon: Icon, title, description, actionLabel, actionHref, onAction }: EmptyStateProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="text-center py-16 bg-surface-card rounded-xl border border-border-default border-dashed"
        >
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-surface-inset mb-4">
                <Icon className="h-8 w-8 text-foreground-muted" />
            </div>
            <h3 className="text-xl font-medium text-foreground mb-2">{title}</h3>
            <p className="text-foreground-secondary max-w-md mx-auto mb-6">{description}</p>
            {actionLabel && actionHref && (
                <Link
                    href={actionHref}
                    className="inline-flex items-center px-4 py-2 bg-accent hover:bg-accent/90 text-white text-sm font-medium rounded-lg transition-colors"
                >
                    {actionLabel}
                </Link>
            )}
            {actionLabel && onAction && !actionHref && (
                <RippleButton
                    onClick={onAction}
                    className="inline-flex items-center px-4 py-2 bg-accent hover:bg-accent/90 text-white text-sm font-medium rounded-lg transition-colors"
                >
                    {actionLabel}
                </RippleButton>
            )}
        </motion.div>
    );
}
