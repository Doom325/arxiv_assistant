"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "../../lib/api";
import { TrendingUp } from "lucide-react";
import AnalyticsHero from "../../components/analytics/AnalyticsHero";
import PapersOverTimeChart from "../../components/analytics/PapersOverTimeChart";
import CategoryDistChart from "../../components/analytics/CategoryDistChart";
import CitationFilterBar from "../../components/analytics/CitationFilterBar";
import CitationCard from "../../components/analytics/CitationCard";

interface TopCitation {
  arxiv_id: string | null;
  title: string | null;
  count: number;
  resolved_id: string | null;
  paper: {
    id: number | null;
    arxiv_id: string | null;
    title: string | null;
    authors: string[];
    category: string;
    published_date: string | null;
    url?: string;
  } | null;
}

interface SummaryStats {
  total_papers: number;
  today_count: number;
  yesterday_count: number;
  library_count: number;
  category_count: number;
}

export default function AnalyticsPage() {
  const [isMounted, setIsMounted] = useState(false);

  // Summary stats
  const [summaryStats, setSummaryStats] = useState<SummaryStats | null>(null);

  // Charts
  const [papersOverTime, setPapersOverTime] = useState<
    Array<{ date: string; count: number }>
  >([]);
  const [granularity, setGranularity] = useState<"day" | "week" | "month">(
    "day"
  );
  const [categoryDist, setCategoryDist] = useState<
    Array<{ category: string; count: number }>
  >([]);

  // Citations
  const [topCitations, setTopCitations] = useState<TopCitation[]>([]);
  const [citationCategory, setCitationCategory] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Loading states
  const [statsLoading, setStatsLoading] = useState(true);
  const [chartsLoading, setChartsLoading] = useState(true);
  const [citationsLoading, setCitationsLoading] = useState(true);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Load summary stats once
  useEffect(() => {
    if (!isMounted) return;
    (async () => {
      setStatsLoading(true);
      try {
        const data = await api.getAnalyticsSummaryStats();
        setSummaryStats(data);
      } catch (e) {
        console.error("Error loading summary stats:", e);
      } finally {
        setStatsLoading(false);
      }
    })();
  }, [isMounted]);

  // Load papers-over-time when granularity changes
  useEffect(() => {
    if (!isMounted) return;
    (async () => {
      setChartsLoading(true);
      try {
        const [timeData, catData] = await Promise.all([
          api.getAnalyticsPapersOverTime(granularity, 30),
          api.getAnalyticsCategoryDist(30),
        ]);
        setPapersOverTime(timeData);
        setCategoryDist(catData);
      } catch (e) {
        console.error("Error loading chart data:", e);
      } finally {
        setChartsLoading(false);
      }
    })();
  }, [isMounted, granularity]);

  // Load citations when filters change
  useEffect(() => {
    if (!isMounted) return;
    (async () => {
      setCitationsLoading(true);
      try {
        const data = await api.getTopCitations({
          category: citationCategory || undefined,
          startDate: startDate || undefined,
          endDate: endDate || undefined,
          limit: 20,
        });
        setTopCitations(data);
      } catch (e) {
        console.error("Error loading citations:", e);
      } finally {
        setCitationsLoading(false);
      }
    })();
  }, [isMounted, citationCategory, startDate, endDate]);

  const handleGranularityChange = useCallback(
    (g: "day" | "week" | "month") => {
      setGranularity(g);
    },
    []
  );

  if (!isMounted) return null;

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-12 pt-8 pb-24 space-y-12">
      {/* Hero stats (featured surface) */}
      {statsLoading ? (
        <div className="bg-surface-featured rounded-2xl p-10 shadow-warm animate-pulse">
          <div className="h-10 w-48 bg-on-featured/10 rounded-lg mb-8" />
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="text-center py-4">
                <div className="h-8 w-16 mx-auto bg-on-featured/10 rounded-lg mb-2" />
                <div className="h-3 w-20 mx-auto bg-on-featured/10 rounded" />
              </div>
            ))}
          </div>
        </div>
      ) : summaryStats ? (
        <AnalyticsHero
          totalPapers={summaryStats.total_papers}
          todayCount={summaryStats.today_count}
          yesterdayCount={summaryStats.yesterday_count}
          libraryCount={summaryStats.library_count}
          categoryCount={summaryStats.category_count}
        />
      ) : null}

      {/* Charts row */}
      {chartsLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {[0, 1].map((i) => (
            <div
              key={i}
              className="bg-surface-card rounded-2xl p-6 shadow-warm-sm animate-pulse"
            >
              <div className="h-5 w-40 bg-surface-inset rounded mb-2" />
              <div className="h-3 w-56 bg-surface-inset rounded mb-6" />
              <div className="h-48 bg-surface-inset rounded-xl" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <PapersOverTimeChart
            data={papersOverTime}
            granularity={granularity}
            onGranularityChange={handleGranularityChange}
          />
          <CategoryDistChart data={categoryDist} />
        </div>
      )}

      {/* Top Citations section */}
      <section className="space-y-6">
        <div>
          <h2 className="font-display text-2xl font-bold text-foreground">
            Top Citations
          </h2>
          <p className="text-foreground-muted text-sm mt-1">
            Most referenced papers across your library
          </p>
        </div>

        <CitationFilterBar
          category={citationCategory}
          onCategoryChange={setCitationCategory}
          startDate={startDate}
          onStartDateChange={setStartDate}
          endDate={endDate}
          onEndDateChange={setEndDate}
        />

        {citationsLoading ? (
          <div className="flex flex-col items-center justify-center py-24 space-y-4">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-accent" />
            <p className="text-foreground-muted animate-pulse font-display italic text-sm">
              Analyzing citation networks...
            </p>
          </div>
        ) : topCitations.length === 0 ? (
          <div className="text-center py-24 bg-surface-card rounded-2xl shadow-warm-sm">
            <TrendingUp className="h-14 w-14 mx-auto text-foreground-muted mb-4" />
            <h3 className="font-display text-xl font-bold text-foreground mb-2">
              No Citation Data Available
            </h3>
            <p className="text-foreground-muted text-sm max-w-md mx-auto">
              Processing the library index. Run a paper analysis to see citation
              trends here.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {topCitations.map((item, idx) => (
              <CitationCard
                key={item.arxiv_id ?? `ext-${idx}`}
                rank={idx + 1}
                arxivId={item.arxiv_id}
                title={item.paper?.title || item.title}
                count={item.count}
                resolvedId={item.resolved_id}
                category={item.paper?.category || null}
                authors={item.paper?.authors || null}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
