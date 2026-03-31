"use client";

import { ButtonHTMLAttributes, MouseEvent, useCallback, useRef, useState } from "react";

interface Ripple {
    x: number;
    y: number;
    id: number;
}

interface RippleButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    /** Set to className of the <a> if you want a link-styled ripple (not used here) */
}

export default function RippleButton({ children, className = "", onClick, ...props }: RippleButtonProps) {
    const [ripples, setRipples] = useState<Ripple[]>([]);
    const nextId = useRef(0);

    const handleClick = useCallback(
        (e: MouseEvent<HTMLButtonElement>) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const id = nextId.current++;

            setRipples((prev) => [...prev, { x, y, id }]);
            setTimeout(() => {
                setRipples((prev) => prev.filter((r) => r.id !== id));
            }, 500);

            onClick?.(e);
        },
        [onClick]
    );

    return (
        <button className={`relative overflow-hidden ${className}`} onClick={handleClick} {...props}>
            {ripples.map((r) => (
                <span
                    key={r.id}
                    className="absolute rounded-full bg-white/10 animate-ripple pointer-events-none"
                    style={{ left: r.x, top: r.y, transform: "translate(-50%, -50%)" }}
                />
            ))}
            {children}
        </button>
    );
}
