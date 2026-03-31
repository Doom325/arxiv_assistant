"use client";

import { Suspense } from "react";
import QueuePage from "./queue/page";

export default function Home() {
    return (
        <Suspense
            fallback={
                <div className="text-center text-foreground-muted py-12">
                    Loading...
                </div>
            }
        >
            <QueuePage />
        </Suspense>
    );
}
