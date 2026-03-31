"use client";

import { motion, type Variants } from "framer-motion";

const container: Variants = {
    hidden: {},
    show: {
        transition: {
            staggerChildren: 0.05,
        },
    },
};

const item: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: {
        opacity: 1,
        y: 0,
        transition: { type: "spring", stiffness: 200, damping: 20 },
    },
};

export function StaggerGrid({
    children,
    className = "",
}: {
    children: React.ReactNode;
    className?: string;
}) {
    return (
        <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className={className}
        >
            {children}
        </motion.div>
    );
}

export function StaggerItem({ children }: { children: React.ReactNode }) {
    return <motion.div variants={item}>{children}</motion.div>;
}
