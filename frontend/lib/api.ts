const API_URL = typeof window === 'undefined'
    ? (process.env.INTERNAL_API_URL || "http://backend:8000")
    : "/api"; // Forced relative path for stability

export interface Citation {
    title?: string | null;
    authors: string[];
    url?: string | null;
    raw: string;
    resolved_id?: string | null;
}

export type SummaryStatus = "pending" | "running" | "succeeded" | "failed";

export interface SummaryError {
    code: string;
    message: string;
    attempted_at?: string | null;
    attempt_count?: number;
}

export interface Paper {
    id: string; // This is arxiv_id in the frontend transformation
    db_id?: number; // Numeric PK from database
    arxiv_id: string;
    title: string;
    summary?: string;
    published_date: string;
    categories: string[];
    pdf_url: string;
    generated_summary?: string;
    sources?: string[];
    list_name?: string;
    citations?: Citation[];
    added_at?: string;
    summary_status?: SummaryStatus | null;
    summary_error?: SummaryError | null;
    summary_attempted_at?: string | null;
}

export interface UserConfig {
    email: string;
    keywords: string[];
    categories: string[];
}

// ─────────────────────────────────────────────────────
// Pattern Library Interfaces
// ─────────────────────────────────────────────────────

export interface PatternDetail {
    category: string;
    name: string;
    confidence: number;
    evidence?: string | null;
}

export interface PaperPattern {
    arxiv_id: string;
    title: string;
    published_date?: string | null;
    category?: string | null;
    is_agentic?: boolean | null;
    primary_pattern_category?: string | null;
    patterns: PatternDetail[];
    reasoning?: string | null;
}

export interface PatternCount {
    name: string;
    label: string;
    paper_count: number;
}

export interface CategoryOverview {
    category: string;
    label: string;
    paper_count: number;
    is_agentic_category: boolean;
    patterns: PatternCount[];
}

export interface PatternOverview {
    total_classified: number;
    total_agentic: number;
    categories: CategoryOverview[];
}

// ─────────────────────────────────────────────────────
// Timeline Interfaces
// ─────────────────────────────────────────────────────

export interface TimelineNode {
    paper_id: number | null;
    arxiv_id: string;
    title: string;
    authors?: string[] | object | null;
    summary?: string | null;
    published_date?: string | null;
    category?: string | null;
    citation_count: number;
    is_seminal: boolean;
    is_in_library: boolean;
    is_ghost: boolean;
    branch_id: number;
    x_position: number;
    y_position: number;
}

export interface TimelineEdge {
    source_paper_id: number;
    target_paper_id: number;
    edge_type: string;
}

export interface TimelineResponse {
    nodes: TimelineNode[];
    edges: TimelineEdge[];
    query?: string | null;
    seed_paper_id?: number | null;
}

// ─────────────────────────────────────────────────────
// Reading Queue Interfaces
// ─────────────────────────────────────────────────────

export interface QueueItem {
    paper_id: number;
    arxiv_id: string;
    title: string;
    authors?: string[] | null;
    summary?: string | null;
    published_date?: string | null;
    category: string;
    pdf_url: string;
    generated_summary?: string | null;
    priority_score: number;
    interest_similarity: number;
    citation_impact: number;
    freshness_score: number;
    category_score: number;
    entity_overlap: number;
    peer_reads_score: number;
    read_status: string;
    source: string;
    best_match_paper_id?: number | null;
    best_match_score?: number | null;
    best_match_title?: string | null;
    manual_priority?: number | null;
    added_at?: string | null;
    scored_at?: string | null;
    read_at?: string | null;
}

export interface QueueStats {
    total_unread: number;
    total_reading: number;
    total_read: number;
    total_skipped: number;
    discovery_unread: number;
    bookmark_unread: number;
    avg_priority: number;
    high_priority_count: number;
    estimated_reading_hours: number;
    // Optional fields added for FeaturedStatBlock (REQ-039 resolution)
    estimated_reading_time_minutes?: number;
}

// Helper to extract descriptive error messages from backend responses
async function handleApiError(res: Response, fallback: string): Promise<never> {
    let message = fallback;
    try {
        const errorData = await res.json();
        if (errorData?.detail) {
            if (typeof errorData.detail === "string") {
                message = errorData.detail;
            } else if (Array.isArray(errorData.detail)) {
                message = errorData.detail
                    .map((e: unknown) => {
                        if (typeof e === "object" && e !== null && "msg" in e) {
                            return String((e as { msg: unknown }).msg);
                        }
                        return JSON.stringify(e);
                    })
                    .join("; ");
            } else {
                message = JSON.stringify(errorData.detail);
            }
        } else if (errorData?.error) {
            message = typeof errorData.error === "string" ? errorData.error : JSON.stringify(errorData.error);
        } else if (errorData?.message) {
            message = errorData.message;
        }
    } catch {
        try {
            const text = await res.text();
            if (text && text.trim().length > 0 && text.length < 200) {
                message = text.trim();
            }
        } catch {
            // Keep fallback
        }
    }
    throw new Error(message);
}

// ─────────────────────────────────────────────────────
// Unified API object
// ─────────────────────────────────────────────────────

export const api = {
    // Papers
    getPapers: async (skip = 0, limit = 1000, filters?: { category?: string; startDate?: string; endDate?: string }): Promise<Paper[]> => {
        let url = `${API_URL}/papers/?skip=${skip}&limit=${limit}`;
        if (filters) {
            if (filters.category) url += `&category=${encodeURIComponent(filters.category)}`;
            if (filters.startDate) url += `&start_date=${encodeURIComponent(filters.startDate)}`;
            if (filters.endDate) url += `&end_date=${encodeURIComponent(filters.endDate)}`;
        }
        const res = await fetch(url);
        if (!res.ok) await handleApiError(res, "Failed to fetch papers");
        return res.json();
    },

    getPaper: async (id: string) => {
        const response = await fetch(`${API_URL}/papers/${id}`);
        if (!response.ok) await handleApiError(response, "Failed to fetch paper");
        return response.json();
    },

    getSimilarPapers: async (id: string | number): Promise<Paper[]> => {
        const response = await fetch(`${API_URL}/papers/${id}/similar`);
        if (!response.ok) await handleApiError(response, "Failed to fetch similar papers");
        return response.json();
    },

    addPaper: async (query: string): Promise<Paper> => {
        const response = await fetch(`${API_URL}/papers/add`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query }),
        });
        if (!response.ok) {
            await handleApiError(response, "Failed to add paper");
        }
        return response.json();
    },

    generateSummary: async (paperId: number, force: boolean = false, model?: string, temperature?: number) => {
        const params = new URLSearchParams();
        if (force) params.set("force", "true");
        if (model) params.set("model", model);
        if (temperature !== undefined) params.set("temperature", String(temperature));
        const qs = params.toString();
        const url = qs
            ? `${API_URL}/papers/${paperId}/summarize?${qs}`
            : `${API_URL}/papers/${paperId}/summarize`;
        const response = await fetch(url, {
            method: "POST",
        });
        if (!response.ok) await handleApiError(response, "Failed to start summarization");
        return response.json();
    },

    getSummarizationModels: async (): Promise<{
        default_provider: string;
        default: string | null;
        models: { id: string; provider: "gemini" | "local" }[];
    }> => {
        const response = await fetch(`${API_URL}/models/summarization`);
        if (!response.ok) await handleApiError(response, "Failed to fetch models");
        return response.json();
    },

    emailPaperSummary: async (paperId: number, recipient?: string): Promise<{ message: string; results: { email: string; sent: boolean }[] }> => {
        const response = await fetch(`${API_URL}/papers/${paperId}/email`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(recipient ? { recipient } : {}),
        });
        if (!response.ok) await handleApiError(response, "Failed to send email");
        return response.json();
    },

    // Search & Chat
    searchPapers: async (query: string, skip = 0, limit = 1000, sortBy = "relevance", filters?: { category?: string; startDate?: string; endDate?: string }): Promise<Paper[]> => {
        let url = `${API_URL}/papers/search?query=${encodeURIComponent(query)}&skip=${skip}&limit=${limit}&sort_by=${sortBy}`;
        if (filters) {
            if (filters.category) url += `&category=${encodeURIComponent(filters.category)}`;
            if (filters.startDate) url += `&start_date=${encodeURIComponent(filters.startDate)}`;
            if (filters.endDate) url += `&end_date=${encodeURIComponent(filters.endDate)}`;
        }
        const res = await fetch(url, {
            method: "POST",
        });
        if (!res.ok) {
            await handleApiError(res, `Search request failed (${res.status})`);
        }
        return res.json();
    },

    chat: async (query: string): Promise<{ response: string; sources: string[] }> => {
        const res = await fetch(`${API_URL}/papers/chat?query=${encodeURIComponent(query)}`, {
            method: "POST",
        });
        if (!res.ok) throw new Error("Chat request failed");
        return res.json();
    },

    // User Config
    getUserConfig: async (email: string): Promise<UserConfig> => {
        const res = await fetch(`${API_URL}/users/config/${email}`);
        if (!res.ok) {
            if (res.status === 404) {
                return { email, keywords: [], categories: [] };
            }
            throw new Error("Failed to fetch user config");
        }
        return res.json();
    },

    updateUserConfig: async (config: UserConfig): Promise<UserConfig> => {
        const res = await fetch(`${API_URL}/users/config`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(config),
        });
        if (!res.ok) throw new Error("Failed to update user config");
        return res.json();
    },

    // Library
    addBookmark: async (paperId: number, listName?: string) => {
        let url = `${API_URL}/library/${paperId}`;
        if (listName) url += `?list_name=${encodeURIComponent(listName)}`;
        const response = await fetch(url, {
            method: "POST",
        });
        if (!response.ok) throw new Error("Failed to add bookmark");
        return response.json();
    },

    removeBookmark: async (paperId: number, listName?: string) => {
        let url = `${API_URL}/library/${paperId}`;
        if (listName) url += `?list_name=${encodeURIComponent(listName)}`;
        const response = await fetch(url, {
            method: "DELETE",
        });
        if (!response.ok) throw new Error("Failed to remove bookmark");
        return response.json();
    },

    getBookmarkedIds: async (listName?: string): Promise<number[]> => {
        let url = `${API_URL}/library/ids`;
        if (listName) url += `?list_name=${encodeURIComponent(listName)}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to fetch bookmarks");
        return response.json();
    },

    createList: async (listName: string) => {
        const response = await fetch(`${API_URL}/library/lists/${encodeURIComponent(listName)}`, {
            method: "POST",
        });
        if (!response.ok) throw new Error("Failed to create list");
        return response.json();
    },

    getLibraryLists: async (): Promise<string[]> => {
        const response = await fetch(`${API_URL}/library/lists`);
        if (!response.ok) throw new Error("Failed to fetch library lists");
        return response.json();
    },

    getLibrary: async (listName?: string): Promise<Paper[]> => {
        let url = `${API_URL}/library`;
        if (listName) url += `?list_name=${encodeURIComponent(listName)}`;
        const response = await fetch(url, { cache: 'no-store' });
        if (!response.ok) throw new Error("Failed to fetch library");
        return response.json();
    },

    exportToGDrive: async (listName: string, folderName?: string) => {
        let url = `${API_URL}/library/export/gdrive?list_name=${encodeURIComponent(listName)}`;
        if (folderName) url += `&custom_folder_name=${encodeURIComponent(folderName)}`;
        const response = await fetch(url, {
            method: "POST",
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Failed to export to Google Drive");
        }
        return response.json();
    },

    gdriveAuthConfirm: async (code: string) => {
        const response = await fetch(`${API_URL}/library/export/gdrive/auth?code=${encodeURIComponent(code)}`, {
            method: "POST",
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Failed to authenticate with Google Drive");
        }
        return response.json();
    },

    // Citations
    getTopCitations: async (filters?: { category?: string; limit?: number; startDate?: string; endDate?: string }): Promise<any[]> => {
        let url = `${API_URL}/citations/top/?limit=${filters?.limit || 50}`;
        if (filters?.category) url += `&category=${encodeURIComponent(filters.category)}`;
        if (filters?.startDate) url += `&start_date=${encodeURIComponent(filters.startDate)}`;
        if (filters?.endDate) url += `&end_date=${encodeURIComponent(filters.endDate)}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to fetch top citations");
        return res.json();
    },

    // Patterns
    getPatternOverview: async (filters?: { is_agentic?: boolean; startDate?: string; endDate?: string }): Promise<PatternOverview> => {
        let url = `${API_URL}/patterns/overview`;
        const params: string[] = [];
        if (filters?.is_agentic !== undefined) params.push(`is_agentic=${filters.is_agentic}`);
        if (filters?.startDate) params.push(`start_date=${encodeURIComponent(filters.startDate)}`);
        if (filters?.endDate) params.push(`end_date=${encodeURIComponent(filters.endDate)}`);
        if (params.length) url += `?${params.join("&")}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to fetch pattern overview");
        return response.json();
    },

    getPatternPapers: async (filters: {
        category?: string;
        pattern?: string;
        is_agentic?: boolean;
        startDate?: string;
        endDate?: string;
        skip?: number;
        limit?: number;
    }): Promise<PaperPattern[]> => {
        let url = `${API_URL}/patterns/papers`;
        const params: string[] = [];
        if (filters.category) params.push(`category=${encodeURIComponent(filters.category)}`);
        if (filters.pattern) params.push(`pattern=${encodeURIComponent(filters.pattern)}`);
        if (filters.is_agentic !== undefined) params.push(`is_agentic=${filters.is_agentic}`);
        if (filters.startDate) params.push(`start_date=${encodeURIComponent(filters.startDate)}`);
        if (filters.endDate) params.push(`end_date=${encodeURIComponent(filters.endDate)}`);
        if (filters.skip !== undefined) params.push(`skip=${filters.skip}`);
        if (filters.limit !== undefined) params.push(`limit=${filters.limit}`);
        if (params.length) url += `?${params.join("&")}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to fetch pattern papers");
        return response.json();
    },

    getPaperPatterns: async (arxivId: string): Promise<PaperPattern | null> => {
        const response = await fetch(`${API_URL}/patterns/paper/${encodeURIComponent(arxivId)}`);
        if (response.status === 404) return null;
        if (!response.ok) throw new Error("Failed to fetch paper patterns");
        return response.json();
    },

    // ── Reading Queue ─────────────────────────────────

    getQueue: async (status?: string, limit = 50, offset = 0, source?: string): Promise<QueueItem[]> => {
        const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
        if (status) params.set("status", status);
        if (source) params.set("source", source);
        const response = await fetch(`${API_URL}/queue?${params}`);
        if (!response.ok) throw new Error("Failed to fetch queue");
        return response.json();
    },

    getQueueStats: async (): Promise<QueueStats> => {
        const response = await fetch(`${API_URL}/queue/stats`);
        if (!response.ok) throw new Error("Failed to fetch queue stats");
        return response.json();
    },

    markRead: async (paperId: number) => {
        const response = await fetch(`${API_URL}/queue/${paperId}/read`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to mark as read");
        return response.json();
    },

    markReading: async (paperId: number) => {
        const response = await fetch(`${API_URL}/queue/${paperId}/reading`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to mark as reading");
        return response.json();
    },

    markSkipped: async (paperId: number) => {
        const response = await fetch(`${API_URL}/queue/${paperId}/skip`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to mark as skipped");
        return response.json();
    },

    setManualPriority: async (paperId: number, priority: number | null) => {
        const response = await fetch(`${API_URL}/queue/${paperId}/priority`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ priority }),
        });
        if (!response.ok) throw new Error("Failed to set priority");
        return response.json();
    },

    discoverQueue: async (sinceDays = 7) => {
        const response = await fetch(`${API_URL}/queue/discover?since_days=${sinceDays}`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to run discovery");
        return response.json();
    },

    rescoreQueue: async () => {
        const response = await fetch(`${API_URL}/queue/rescore`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to rescore queue");
        return response.json();
    },

    removeFromQueue: async (paperId: number) => {
        const response = await fetch(`${API_URL}/queue/${paperId}`, { method: "DELETE" });
        if (!response.ok) throw new Error("Failed to remove from queue");
        return response.json();
    },

    // ── Analytics ──────────────────────────────────────

    getAnalyticsPapersOverTime: async (
        granularity: "day" | "week" | "month" = "day",
        days: number = 14,
        category?: string,
    ): Promise<{ date: string; count: number }[]> => {
        const params = new URLSearchParams({ granularity, days: String(days) });
        if (category) params.set("category", category);
        const response = await fetch(
            `${API_URL}/analytics/papers-over-time?${params}`,
        );
        if (!response.ok) throw new Error("Failed to fetch papers-over-time");
        return response.json();
    },

    getAnalyticsCategoryDist: async (
        days: number = 30,
        category?: string,
    ): Promise<{ category: string; count: number }[]> => {
        const params = new URLSearchParams({ days: String(days) });
        if (category) params.set("category", category);
        const response = await fetch(
            `${API_URL}/analytics/category-distribution?${params}`,
        );
        if (!response.ok) throw new Error("Failed to fetch category distribution");
        return response.json();
    },

    getAnalyticsSummaryStats: async (category?: string): Promise<{
        total_papers: number;
        today_count: number;
        yesterday_count: number;
        library_count: number;
        category_count: number;
    }> => {
        const params = category ? `?category=${encodeURIComponent(category)}` : "";
        const response = await fetch(`${API_URL}/analytics/summary-stats${params}`);
        if (!response.ok) throw new Error("Failed to fetch summary stats");
        return response.json();
    },

    // ── Timeline ──────────────────────────────────────
    getTimelineByTopic: async (query: string, limit: number = 50, libraryOnly: boolean = false): Promise<TimelineResponse> => {
        const params = new URLSearchParams({ q: query, limit: String(limit) });
        if (libraryOnly) params.set("library_only", "true");
        const response = await fetch(`${API_URL}/timeline/topic?${params}`);
        if (!response.ok) throw new Error("Failed to fetch timeline");
        return response.json();
    },

    getTimelineByPaper: async (paperId: number, hops: number = 2): Promise<TimelineResponse> => {
        const response = await fetch(`${API_URL}/timeline/paper/${paperId}?hops=${hops}`);
        if (!response.ok) throw new Error("Failed to fetch timeline");
        return response.json();
    },
};

// ─────────────────────────────────────────────────────
// Full-Text Interfaces
// ─────────────────────────────────────────────────────

export interface PaperSection {
    title: string
    level: number
    content: string
    order: number
}

export interface PaperImage {
    filename: string
    page: number
    width: number
    height: number
}

export interface PaperFullText {
    arxiv_id: string
    title: string
    sections: PaperSection[]
    images: PaperImage[]
    word_count: number
    estimated_reading_minutes: number
}

export async function getFullText(id: string): Promise<PaperFullText> {
    const res = await fetch(`/api/papers/${id}/full-text`)
    if (!res.ok) throw new Error(`Failed to fetch full text: ${res.status}`)
    return res.json()
}

// ─────────────────────────────────────────────────────
// Backward-compatible standalone re-exports
// ─────────────────────────────────────────────────────

export const addBookmark = api.addBookmark;
export const removeBookmark = api.removeBookmark;
export const getBookmarkedIds = api.getBookmarkedIds;
export const createList = api.createList;
export const getLibraryLists = api.getLibraryLists;
export const getLibrary = api.getLibrary;
export const getPaper = api.getPaper;
export const generateSummary = api.generateSummary;
export const getSummarizationModels = api.getSummarizationModels;
export const addPaper = api.addPaper;
export const getSimilarPapers = api.getSimilarPapers;
export const exportToGDrive = api.exportToGDrive;
export const gdriveAuthConfirm = api.gdriveAuthConfirm;
export const getPatternOverview = api.getPatternOverview;
export const getPatternPapers = api.getPatternPapers;
export const getPaperPatterns = api.getPaperPatterns;
export const emailPaperSummary = api.emailPaperSummary;
