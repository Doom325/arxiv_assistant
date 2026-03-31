"use client";

import HeroDecoration from "../HeroDecoration";

interface LibraryHeroProps {
  totalPapers: number;
  totalLists: number;
}

export default function LibraryHero({ totalPapers, totalLists }: LibraryHeroProps) {
  return (
    <section className="bg-surface-featured rounded-2xl p-8 md:p-10 relative overflow-hidden">
      <HeroDecoration variant="diagonal" />
      {/* Decorative orbs */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-white/[0.03] rounded-full -translate-y-1/2 translate-x-1/4" />
      <div className="absolute bottom-0 left-1/2 w-96 h-48 bg-white/[0.02] rounded-full translate-y-1/2" />

      <div className="relative z-10">
        {/* Label */}
        <p className="text-[10px] font-bold uppercase tracking-widest text-white/60 mb-3">
          Your Library
        </p>

        {/* Mixed-weight headline */}
        <h1
          className="text-3xl md:text-4xl text-white leading-tight mb-3"
          style={{ fontFamily: "var(--font-display)" }}
        >
          <span className="font-extralight italic">Your personal</span>{" "}
          <span className="font-bold">research library.</span>
        </h1>

        {/* Stats subtitle */}
        <p
          className="text-white/80 text-sm italic"
          style={{ fontFamily: "var(--font-display)" }}
        >
          {totalPapers} papers across {totalLists} collections
        </p>
      </div>
    </section>
  );
}
