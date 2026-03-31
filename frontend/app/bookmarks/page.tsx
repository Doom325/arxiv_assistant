"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Paper } from "@/lib/api";
import { toast } from "sonner";
import { useLibrary } from "@/components/LibraryContext";
import LibraryHero from "@/components/library/LibraryHero";
import LibraryControls from "@/components/library/LibraryControls";
import LibraryPaperCard from "@/components/library/LibraryPaperCard";
import { LibraryEmptyState, LibraryEmptyList } from "@/components/library/LibraryEmptyStates";
import GDriveAuthPanel, { ExportStatusBanner } from "@/components/library/GDriveAuthPanel";

export default function BookmarksPage() {
    const router = useRouter();
    const { lists, bookmarkedMap, refreshLibrary, createList } = useLibrary();
    const [papers, setPapers] = useState<Paper[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedList, setSelectedList] = useState<string>("All");
    const [isCreatingList, setIsCreatingList] = useState(false);
    const [newListName, setNewListName] = useState("");
    const [isExporting, setIsExporting] = useState(false);
    const [exportStatus, setExportStatus] = useState<{ message: string, isError: boolean } | null>(null);
    const [authUrl, setAuthUrl] = useState<string | null>(null);
    const [codeVerifier, setCodeVerifier] = useState<string | null>(null);
    const [authCode, setAuthCode] = useState("");
    const [isAuthenticating, setIsAuthenticating] = useState(false);
    const [sortBy, setSortBy] = useState<string>("added_desc");

    const sortedPapers = [...papers].sort((a, b) => {
        switch (sortBy) {
            case "added_desc":
                return new Date(b.added_at || 0).getTime() - new Date(a.added_at || 0).getTime();
            case "added_asc":
                return new Date(a.added_at || 0).getTime() - new Date(b.added_at || 0).getTime();
            case "date_desc":
                return new Date(b.published_date || 0).getTime() - new Date(a.published_date || 0).getTime();
            case "date_asc":
                return new Date(a.published_date || 0).getTime() - new Date(b.published_date || 0).getTime();
            case "title_asc":
                return (a.title || "").localeCompare(b.title || "");
            case "title_desc":
                return (b.title || "").localeCompare(a.title || "");
            default:
                return 0;
        }
    });

    const handleCreateList = async () => {
        if (!newListName.trim()) return;
        try {
            await createList(newListName.trim());
            setNewListName("");
            setIsCreatingList(false);
            setSelectedList(newListName.trim());
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        loadLibrary();
    }, [selectedList, bookmarkedMap]);

    const loadLibrary = async () => {
        setLoading(true);
        try {
            const apiBase = "/api";
            let url = `${apiBase}/library`;
            if (selectedList !== "All") url += `?list_name=${encodeURIComponent(selectedList)}`;
            const res = await fetch(url);
            const data = await res.json();
            const transformed = data.map((p: any) => ({
                ...p,
                id: p.arxiv_id,
                db_id: p.id,
                categories: Array.isArray(p.categories) ? p.categories : [p.category || "cs.AI"],
                list_name: p.list_name,
                added_at: p.added_at,
            }));
            setPapers(transformed);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteList = async () => {
        if (selectedList === "All") return;
        if (!confirm(`Are you sure you want to clear all papers from "${selectedList}"?`)) return;

        try {
            const apiBase = "/api";
            for (const paper of papers) {
                await fetch(`${apiBase}/library/${paper.db_id}?list_name=${encodeURIComponent(selectedList)}`, {
                    method: "DELETE"
                });
            }
            refreshLibrary();
            setSelectedList("All");
        } catch (e) {
            console.error(e);
        }
    };

    const handleExportToGDrive = async () => {
        if (selectedList === "All") {
            toast.warning("Please select a specific list to export.");
            return;
        }

        setIsExporting(true);
        setExportStatus(null);
        setAuthUrl(null);

        try {
            const apiBase = "/api";
            const response = await fetch(`${apiBase}/library/export/gdrive?list_name=${encodeURIComponent(selectedList)}`, {
                method: "POST"
            });
            const result = await response.json();

            if (result.status === "need_auth") {
                setAuthUrl(result.auth_url);
                setCodeVerifier(result.code_verifier);
                setExportStatus({
                    message: "Authentication required to access Google Drive.",
                    isError: false
                });
            } else {
                setExportStatus({
                    message: result.message,
                    isError: false
                });
                setTimeout(() => setExportStatus(null), 5000);
            }
        } catch (e: any) {
            console.error(e);
            setExportStatus({
                message: e.message || "Failed to export to Google Drive",
                isError: true
            });
        } finally {
            setIsExporting(false);
        }
    };

    const handleConfirmAuth = async () => {
        if (!authCode.trim()) return;
        setIsAuthenticating(true);
        try {
            const apiBase = "/api";
            let url = `${apiBase}/library/export/gdrive/auth?code=${encodeURIComponent(authCode.trim())}`;
            if (codeVerifier) url += `&code_verifier=${encodeURIComponent(codeVerifier)}`;

            const response = await fetch(url, {
                method: "POST"
            });
            const result = await response.json();

            if (response.ok) {
                setExportStatus({ message: result.message, isError: false });
                setAuthUrl(null);
                setAuthCode("");
                handleExportToGDrive();
            } else {
                throw new Error(result.detail || "Authentication failed");
            }
        } catch (e: any) {
            console.error(e);
            toast.error(e.message || "Failed to authenticate");
        } finally {
            setIsAuthenticating(false);
        }
    };

    const handleAddToQueue = async (paper: Paper) => {
        try {
            await fetch(`/api/batch/queue/${paper.db_id}`, { method: 'POST' });
            toast.success(`Added "${paper.title}" to queue`);
        } catch (e) {
            toast.error('Failed to add to queue');
        }
    };

    return (
        <div className="px-8 lg:px-12 py-8 space-y-10">
            <LibraryHero totalPapers={papers.length} totalLists={lists.length} />

            <LibraryControls
                lists={lists}
                selectedList={selectedList}
                onSelectList={setSelectedList}
                isCreatingList={isCreatingList}
                onStartCreateList={() => setIsCreatingList(true)}
                newListName={newListName}
                onNewListNameChange={setNewListName}
                onCreateList={handleCreateList}
                onCancelCreate={() => setIsCreatingList(false)}
                sortBy={sortBy}
                onSortChange={setSortBy}
                onExport={handleExportToGDrive}
                isExporting={isExporting}
                onDeleteList={handleDeleteList}
            />

            {authUrl && (
                <GDriveAuthPanel
                    authUrl={authUrl}
                    authCode={authCode}
                    onAuthCodeChange={setAuthCode}
                    onConfirmAuth={handleConfirmAuth}
                    isAuthenticating={isAuthenticating}
                    onClose={() => setAuthUrl(null)}
                />
            )}

            {exportStatus && !authUrl && (
                <ExportStatusBanner
                    message={exportStatus.message}
                    isError={exportStatus.isError}
                    onDismiss={() => setExportStatus(null)}
                />
            )}

            {loading ? (
                <div className="flex flex-col items-center justify-center py-16">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
                    <p className="text-foreground-muted mt-4 italic" style={{ fontFamily: 'var(--font-display)' }}>Loading your library...</p>
                </div>
            ) : papers.length === 0 ? (
                selectedList === "All"
                    ? <LibraryEmptyState onBrowse={() => router.push('/dashboard')} />
                    : <LibraryEmptyList listName={selectedList} />
            ) : (
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-6">
                    {sortedPapers.map((paper) => (
                        <LibraryPaperCard
                            key={`${paper.id}-${paper.list_name}`}
                            paper={paper}
                            listMemberships={paper.db_id != null ? (bookmarkedMap[paper.db_id] || []) : []}
                            onAddToQueue={handleAddToQueue}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
