export default function SkeletonCard() {
    return (
        <div className="bg-surface-card border border-border-default glass-card rounded-2xl p-6 h-full flex flex-col">
            {/* Date + category badges */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                    <div className="skeleton h-4 w-4 rounded-full" />
                    <div className="skeleton h-4 w-24" />
                </div>
                <div className="flex space-x-2">
                    <div className="skeleton h-6 w-14 rounded-full" />
                    <div className="skeleton h-6 w-14 rounded-full" />
                </div>
            </div>

            {/* Title */}
            <div className="mb-2 space-y-2">
                <div className="skeleton h-6 w-full" />
                <div className="skeleton h-6 w-3/4" />
            </div>

            {/* Summary */}
            <div className="flex-grow mb-4 space-y-2">
                <div className="skeleton h-4 w-full" />
                <div className="skeleton h-4 w-11/12" />
                <div className="skeleton h-4 w-2/3" />
            </div>

            {/* Footer */}
            <div className="pt-4 border-t border-border-default">
                <div className="skeleton h-4 w-20" />
            </div>
        </div>
    );
}

export function SkeletonList() {
    return (
        <div className="bg-surface-card border border-border-default rounded-lg overflow-hidden">
            <div className="divide-y divide-border-default">
                {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="px-6 py-4 flex items-center justify-between">
                        <div className="skeleton h-5 w-2/3" />
                        <div className="skeleton h-4 w-24" />
                    </div>
                ))}
            </div>
        </div>
    );
}

export function SkeletonGrid({ count = 6 }: { count?: number }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: count }).map((_, i) => (
                <SkeletonCard key={i} />
            ))}
        </div>
    );
}

export function SkeletonStatsTile() {
    return (
        <div className="bg-surface-card border border-border-default glass-card rounded-2xl p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3">
                <div className="skeleton h-9 w-9 rounded-xl" />
                <div className="skeleton h-5 w-8 rounded-full" />
            </div>
            <div>
                <div className="skeleton h-8 w-16 mb-1" />
                <div className="skeleton h-3 w-24" />
            </div>
        </div>
    );
}

export function SkeletonSparkline() {
    return (
        <div className="bg-surface-card border border-border-default glass-card rounded-2xl p-5">
            <div className="flex items-center justify-between mb-3">
                <div className="skeleton h-3 w-32" />
                <div className="skeleton h-4 w-16" />
            </div>
            <div className="skeleton h-[80px] w-full rounded-lg" />
        </div>
    );
}

export function SkeletonHeroCard() {
    return (
        <div className="bg-surface-card border border-border-default glass-card rounded-2xl p-8 flex flex-col">
            <div className="flex items-center gap-3 mb-4">
                <div className="skeleton h-3 w-16" />
                <div className="skeleton h-6 w-14 rounded-full" />
                <div className="skeleton h-6 w-14 rounded-full" />
            </div>
            <div className="skeleton h-8 w-full mb-2" />
            <div className="skeleton h-8 w-3/4 mb-4" />
            <div className="skeleton h-4 w-48 mb-4" />
            <div className="space-y-2 flex-grow mb-6">
                <div className="skeleton h-4 w-full" />
                <div className="skeleton h-4 w-full" />
                <div className="skeleton h-4 w-11/12" />
                <div className="skeleton h-4 w-4/5" />
            </div>
            <div className="skeleton h-4 w-24" />
        </div>
    );
}

export function SkeletonBentoGrid() {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="md:col-span-2 md:row-span-2">
                <SkeletonHeroCard />
            </div>
            <SkeletonStatsTile />
            <SkeletonStatsTile />
            <div className="lg:col-span-2">
                <SkeletonSparkline />
            </div>
        </div>
    );
}
