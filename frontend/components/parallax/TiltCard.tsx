"use client";

import { useRef, useState, ReactNode } from "react";
import { motion, useSpring, useTransform, useMotionValue } from "framer-motion";

interface TiltCardProps {
    children: ReactNode;
    className?: string;
    /** Max tilt angle in degrees (default 6) */
    maxTilt?: number;
    /** Perspective distance in px (default 800) */
    perspective?: number;
    /** Glare highlight on hover (default true) */
    glare?: boolean;
}

function GlareOverlay({ glareX, glareY }: { glareX: ReturnType<typeof useSpring>; glareY: ReturnType<typeof useSpring> }) {
    const background = useTransform(
        [glareX, glareY] as any,
        ([x, y]: number[]) =>
            `radial-gradient(circle at ${x}% ${y}%, rgba(255,255,255,0.06) 0%, transparent 60%)`
    );
    return (
        <motion.div
            className="absolute inset-0 rounded-2xl pointer-events-none z-10"
            style={{ background }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        />
    );
}

export default function TiltCard({
    children,
    className = "",
    maxTilt = 6,
    perspective = 800,
    glare = true,
}: TiltCardProps) {
    const ref = useRef<HTMLDivElement>(null);
    const [isHovered, setIsHovered] = useState(false);

    const springConfig = { stiffness: 150, damping: 20 };
    const rotateX = useSpring(0, springConfig);
    const rotateY = useSpring(0, springConfig);
    const glareX = useSpring(50, springConfig);
    const glareY = useSpring(50, springConfig);

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!ref.current) return;
        const rect = ref.current.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const mouseX = e.clientX - centerX;
        const mouseY = e.clientY - centerY;

        // Normalize to -1..1
        const normX = mouseX / (rect.width / 2);
        const normY = mouseY / (rect.height / 2);

        rotateX.set(-normY * maxTilt);
        rotateY.set(normX * maxTilt);

        // Glare position (percentage)
        glareX.set(((e.clientX - rect.left) / rect.width) * 100);
        glareY.set(((e.clientY - rect.top) / rect.height) * 100);
    };

    const handleMouseLeave = () => {
        setIsHovered(false);
        rotateX.set(0);
        rotateY.set(0);
        glareX.set(50);
        glareY.set(50);
    };

    return (
        <motion.div
            ref={ref}
            className={`relative ${className}`}
            style={{
                perspective: `${perspective}px`,
                transformStyle: "preserve-3d",
            }}
            onMouseMove={handleMouseMove}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={handleMouseLeave}
        >
            <motion.div
                style={{
                    rotateX,
                    rotateY,
                    transformStyle: "preserve-3d",
                }}
                className="relative w-full h-full"
            >
                {children}
                {/* Glare overlay */}
                {glare && isHovered && (
                    <GlareOverlay glareX={glareX} glareY={glareY} />
                )}
            </motion.div>
        </motion.div>
    );
}
