"use client";

import { Suspense } from "react";
import DashboardContent from "../../components/DashboardContent";

export default function DashboardPage() {
    return (
        <Suspense
            fallback={
                <div className="text-center text-foreground-muted py-12">
                    Loading dashboard...
                </div>
            }
        >
            <DashboardContent />
        </Suspense>
    );
}
