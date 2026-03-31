'use client'

// Different decorative patterns for hero sections
const patterns = {
  topographic: (
    <svg className="absolute inset-0 w-full h-full opacity-[0.04]" xmlns="http://www.w3.org/2000/svg">
      <pattern id="topo" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
        <circle cx="50" cy="50" r="40" fill="none" stroke="white" strokeWidth="0.5"/>
        <circle cx="50" cy="50" r="30" fill="none" stroke="white" strokeWidth="0.5"/>
        <circle cx="50" cy="50" r="20" fill="none" stroke="white" strokeWidth="0.5"/>
      </pattern>
      <rect width="100%" height="100%" fill="url(#topo)"/>
    </svg>
  ),
  dots: (
    <svg className="absolute inset-0 w-full h-full opacity-[0.06]" xmlns="http://www.w3.org/2000/svg">
      <pattern id="dots" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
        <circle cx="10" cy="10" r="1" fill="white"/>
      </pattern>
      <rect width="100%" height="100%" fill="url(#dots)"/>
    </svg>
  ),
  diagonal: (
    <svg className="absolute inset-0 w-full h-full opacity-[0.04]" xmlns="http://www.w3.org/2000/svg">
      <pattern id="diag" x="0" y="0" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <line x1="0" y1="0" x2="0" y2="16" stroke="white" strokeWidth="0.5"/>
      </pattern>
      <rect width="100%" height="100%" fill="url(#diag)"/>
    </svg>
  ),
  grid: (
    <svg className="absolute inset-0 w-full h-full opacity-[0.03]" xmlns="http://www.w3.org/2000/svg">
      <pattern id="grid" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
        <path d="M 24 0 L 0 0 0 24" fill="none" stroke="white" strokeWidth="0.5"/>
      </pattern>
      <rect width="100%" height="100%" fill="url(#grid)"/>
    </svg>
  ),
}

export default function HeroDecoration({ variant = 'topographic' }: { variant?: keyof typeof patterns }) {
  return <div className="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none">{patterns[variant]}</div>
}
