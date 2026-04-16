"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { generateSummary, addBookmark, removeBookmark, getBookmarkedIds, Paper, getPaper, getSimilarPapers, getPaperPatterns, PaperPattern, emailPaperSummary } from "../../../lib/api";
import { showSummaryCompleteNotification, requestNotificationPermission } from "../../../lib/notifications";
import { ArrowLeft } from "lucide-react";
import ErrorBoundary from "../../../components/ErrorBoundary";
import PaperHero from "@/components/paper/PaperHero";
import PaperActionFooter from "@/components/paper/PaperActionFooter";
import RecommendedResearch from "@/components/paper/RecommendedResearch";
import PaperTOC from "@/components/paper/PaperTOC";
import PaperTabBar from "@/components/paper/PaperTabBar";
import FullPaperReader from "@/components/paper/FullPaperReader";
import AIAnalysisTab from "@/components/paper/AIAnalysisTab";

export default function PaperDetail() {
    const params = useParams();
    const router = useRouter();
    const id = params.id as string;
    const [paper, setPaper] = useState<Paper | null>(null);
    const [similarPapers, setSimilarPapers] = useState<Paper[]>([]);
    const [loading, setLoading] = useState(true);
    const [summarizing, setSummarizing] = useState(false);
    const [isBookmarked, setIsBookmarked] = useState(false);
    const [isMounted, setIsMounted] = useState(false);
    const [paperPatterns, setPaperPatterns] = useState<PaperPattern | null>(null);
    const [emailStatus, setEmailStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
    const [activeTab, setActiveTab] = useState<"full-paper" | "ai-analysis">("full-paper");

    useEffect(() => {
        setIsMounted(true);
    }, []);

    useEffect(() => {
        if (id && isMounted) {
            loadPaper();
        }
    }, [id, isMounted]);

    const transformPaper = (data: any): Paper => ({
        ...data,
        id: data.arxiv_id,
        db_id: data.id,
        categories: [data.category || "cs.AI"],
    });

    const loadPaper = async () => {
        try {
            const data = await getPaper(id);
            const transformed = transformPaper(data);
            setPaper(transformed);

            const similar = await getSimilarPapers(id);
            setSimilarPapers(similar.map(transformPaper));

            if (data.id) {
                checkBookmark(data.id);
            }

            // Load pattern classification
            try {
                const patterns = await getPaperPatterns(data.arxiv_id || id);
                setPaperPatterns(patterns);
            } catch (e) {
                console.log("[PAPER DETAIL] No patterns found for this paper");
            }
        } catch (e) {
            console.error("[PAPER DETAIL] Error loading paper:", e);
        } finally {
            setLoading(false);
        }
    };

    const checkBookmark = async (db_id: number) => {
        try {
            const ids = await getBookmarkedIds();
            setIsBookmarked(ids.includes(db_id));
        } catch (e) {
            console.error(e);
        }
    };

    const handleGenerateSummary = async () => {
        if (!paper?.db_id) return;
        const isRegenerate = !!paper.generated_summary;
        setSummarizing(true);
        try {
            await generateSummary(paper.db_id, isRegenerate);

            requestNotificationPermission();

            const pollInterval = setInterval(async () => {
                try {
                    const updatedPaper = await getPaper(id);
                    if (updatedPaper.generated_summary) {
                        // Check if backend returned an error
                        if (updatedPaper.generated_summary.startsWith("__ERROR__")) {
                            const errorMsg = updatedPaper.generated_summary.replace("__ERROR__: ", "");
                            console.error("Summarization error:", errorMsg);
                            setSummarizing(false);
                            clearInterval(pollInterval);
                            setPaper(transformPaper({ ...updatedPaper, generated_summary: null }));
                            alert(`Summarization failed: ${errorMsg}`);
                            return;
                        }
                        setPaper(transformPaper(updatedPaper));
                        setSummarizing(false);
                        clearInterval(pollInterval);

                        void showSummaryCompleteNotification(
                            updatedPaper.title,
                            updatedPaper.arxiv_id ?? updatedPaper.id,
                        );
                    }
                } catch (e) {
                    console.error("Polling error:", e);
                }
            }, 3000);

            setTimeout(() => {
                clearInterval(pollInterval);
                if (summarizing) {
                    setSummarizing(false);
                    alert("Summarization timed out. Check backend logs for details.");
                }
            }, 1800000);
        } catch (e) {
            console.error(e);
            setSummarizing(false);
        }
    };

    const toggleBookmark = async () => {
        if (!paper?.db_id) return;
        try {
            if (isBookmarked) {
                await removeBookmark(paper.db_id);
                setIsBookmarked(false);
            } else {
                await addBookmark(paper.db_id);
                setIsBookmarked(true);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleEmailSummary = async () => {
        if (!paper?.db_id) return;
        setEmailStatus("sending");
        try {
            const result = await emailPaperSummary(paper.db_id);
            const allSent = result.results.every((r: any) => r.sent);
            if (allSent) {
                setEmailStatus("sent");
            } else {
                console.error("Email failures:", result.results);
                setEmailStatus("error");
            }
            setTimeout(() => setEmailStatus("idle"), 3000);
        } catch (e) {
            console.error("Email error:", e);
            setEmailStatus("error");
            setTimeout(() => setEmailStatus("idle"), 3000);
        }
    };

    if (!isMounted || loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
                <p className="text-foreground-muted animate-pulse italic" style={{ fontFamily: 'var(--font-display)' }}>
                    Loading paper details...
                </p>
            </div>
        );
    }

    if (!paper) {
        return (
            <div className="text-center py-24">
                <h2 style={{ fontFamily: 'var(--font-display)' }} className="text-3xl font-extralight text-foreground mb-2">Paper</h2>
                <h2 style={{ fontFamily: 'var(--font-display)' }} className="text-4xl font-black italic text-foreground mb-6">not found.</h2>
                <p className="text-foreground-secondary text-sm mb-8 italic" style={{ fontFamily: 'var(--font-display)' }}>
                    We couldn&apos;t find the paper you&apos;re looking for.
                </p>
                <button onClick={() => router.back()} className="text-accent hover:text-accent-hover transition-colors">
                    &larr; Go back
                </button>
            </div>
        );
    }

    return (
        <ErrorBoundary>
            <div className="max-w-6xl mx-auto px-8 lg:px-12 py-8">
                <button onClick={() => router.back()} className="inline-flex items-center text-foreground-secondary hover:text-foreground mb-8 transition-all hover:-translate-x-1">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back
                </button>

                <div className="flex gap-12">
                    {/* Main content column */}
                    <div className="flex-1 max-w-4xl space-y-16">
                        <PaperHero
                            paper={paper}
                            isBookmarked={isBookmarked}
                            onBookmark={toggleBookmark}
                            emailStatus={emailStatus}
                            onEmail={handleEmailSummary}
                        />

                        <PaperTabBar activeTab={activeTab} onTabChange={setActiveTab} />

                        {activeTab === "full-paper" ? (
                            <FullPaperReader paperId={id} pdfUrl={paper.pdf_url} />
                        ) : (
                            <AIAnalysisTab
                                paper={paper}
                                paperPatterns={paperPatterns}
                                summarizing={summarizing}
                                onGenerate={handleGenerateSummary}
                            />
                        )}

                        <PaperActionFooter
                            paperId={paper.db_id}
                            pdfUrl={paper.pdf_url}
                            emailStatus={emailStatus}
                            onEmail={handleEmailSummary}
                        />

                        <section id="recommendations">
                            <RecommendedResearch papers={similarPapers} />
                        </section>
                    </div>

                    {/* TOC sidebar */}
                    <PaperTOC
                        sections={
                            activeTab === "ai-analysis"
                                ? [
                                      { id: "abstract", label: "Abstract" },
                                      { id: "ai-synthesis", label: "AI Analysis" },
                                      { id: "references", label: "References" },
                                      { id: "patterns", label: "Patterns" },
                                      { id: "recommendations", label: "Recommendations" },
                                  ]
                                : [{ id: "recommendations", label: "Recommendations" }]
                        }
                    />
                </div>
            </div>
        </ErrorBoundary>
    );
}
