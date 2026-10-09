"use client";

import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { getSummarizationModels } from "@/lib/api";

interface AISynthesisSectionProps {
  summary: string | null | undefined;
  isSummarizing: boolean;
  onGenerate: (
    model?: string,
    temperature?: number,
    provider?: string,
    endpoint?: string
  ) => void;
  hasExistingSummary: boolean;
}

const DEFAULT_TEMPERATURE = 0.3;
const CUSTOM_CONFIG_KEY = "arxiv_custom_summarization_config";

function getInitialCustomConfig(): {
  isCustomMode: boolean;
  customProvider: "gemini" | "nvidia" | "local";
  customModel: string;
  customEndpoint: string;
} {
  if (typeof window === "undefined") {
    return {
      isCustomMode: false,
      customProvider: "nvidia",
      customModel: "meta/llama-3.3-70b-instruct",
      customEndpoint: "https://integrate.api.nvidia.com/v1",
    };
  }
  try {
    const saved = localStorage.getItem(CUSTOM_CONFIG_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      return {
        isCustomMode: Boolean(parsed.isCustomMode),
        customProvider:
          parsed.customProvider === "gemini" ||
          parsed.customProvider === "nvidia" ||
          parsed.customProvider === "local"
            ? parsed.customProvider
            : "nvidia",
        customModel: parsed.customModel || "meta/llama-3.3-70b-instruct",
        customEndpoint: parsed.customEndpoint || "https://integrate.api.nvidia.com/v1",
      };
    }
  } catch {
    // Ignore error
  }
  return {
    isCustomMode: false,
    customProvider: "nvidia",
    customModel: "meta/llama-3.3-70b-instruct",
    customEndpoint: "https://integrate.api.nvidia.com/v1",
  };
}

export default function AISynthesisSection({
  summary,
  isSummarizing,
  onGenerate,
  hasExistingSummary,
}: AISynthesisSectionProps) {
  type ModelEntry = { id: string; provider: "gemini" | "local" | "nvidia" | string };
  const [models, setModels] = useState<ModelEntry[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [temperature, setTemperature] = useState<number>(DEFAULT_TEMPERATURE);

  // Custom configuration mode initialized from localStorage or defaults
  const [initialConfig] = useState(getInitialCustomConfig);
  const [isCustomMode, setIsCustomMode] = useState<boolean>(initialConfig.isCustomMode);
  const [customProvider, setCustomProvider] = useState<"gemini" | "nvidia" | "local">(initialConfig.customProvider);
  const [customModel, setCustomModel] = useState<string>(initialConfig.customModel);
  const [customEndpoint, setCustomEndpoint] = useState<string>(initialConfig.customEndpoint);
  const [endpointError, setEndpointError] = useState<string | null>(null);

  // Load models from API
  useEffect(() => {
    let cancelled = false;
    getSummarizationModels()
      .then((res) => {
        if (cancelled) return;
        setModels(res.models);
        if (!selectedModel) {
          setSelectedModel(res.default ?? res.models[0]?.id ?? "");
        }
      })
      .catch((e) => {
        if (cancelled) return;
        console.error("Failed to load models:", e);
        setModelsError("Could not load model list");
      });
    return () => {
      cancelled = true;
    };
  }, [selectedModel]);

  // Save custom configuration when modified
  const updateCustomConfig = (
    prov: "gemini" | "nvidia" | "local",
    mod: string,
    ep: string,
    active: boolean
  ) => {
    try {
      localStorage.setItem(
        CUSTOM_CONFIG_KEY,
        JSON.stringify({
          isCustomMode: active,
          customProvider: prov,
          customModel: mod,
          customEndpoint: ep,
        })
      );
    } catch {
      // Ignore localStorage write errors
    }
  };

  const handleProviderChange = (newProvider: "gemini" | "nvidia" | "local") => {
    setCustomProvider(newProvider);
    setEndpointError(null);
    let newModel = customModel;
    let newEndpoint = customEndpoint;

    if (newProvider === "gemini") {
      newModel = "gemini-3.8-flash";
      newEndpoint = "";
    } else if (newProvider === "nvidia") {
      newModel = "meta/llama-3.3-70b-instruct";
      newEndpoint = "https://integrate.api.nvidia.com/v1";
    } else if (newProvider === "local") {
      newModel = "nemotron3:nano";
      newEndpoint = "http://192.168.1.32:4000/v1";
    }

    setCustomModel(newModel);
    setCustomEndpoint(newEndpoint);
    updateCustomConfig(newProvider, newModel, newEndpoint, isCustomMode);
  };

  const handleEndpointChange = (newEndpoint: string) => {
    setCustomEndpoint(newEndpoint);
    if (newEndpoint.trim() && !/^https?:\/\//i.test(newEndpoint.trim())) {
      setEndpointError("Endpoint must start with http:// or https://");
    } else {
      setEndpointError(null);
    }
    updateCustomConfig(customProvider, customModel, newEndpoint, isCustomMode);
  };

  const handleCustomModelChange = (newModel: string) => {
    setCustomModel(newModel);
    updateCustomConfig(customProvider, newModel, customEndpoint, isCustomMode);
  };

  const handleTriggerGenerate = () => {
    if (isCustomMode) {
      if ((customProvider === "nvidia" || customProvider === "local") && customEndpoint.trim()) {
        if (!/^https?:\/\//i.test(customEndpoint.trim())) {
          setEndpointError("Endpoint must start with http:// or https://");
          return;
        }
      }
      setEndpointError(null);
      onGenerate(
        customModel.trim() || undefined,
        temperature,
        customProvider,
        customEndpoint.trim() || undefined
      );
    } else {
      const found = models.find((m) => m.id === selectedModel);
      onGenerate(selectedModel || undefined, temperature, found?.provider, undefined);
    }
  };

  const buttonText = isSummarizing
    ? "Generating..."
    : hasExistingSummary
      ? "Regenerate Analysis"
      : "Generate Analysis";

  return (
    <section
      id="ai-synthesis"
      className="bg-surface-card rounded-2xl shadow-warm-sm p-6 md:p-8 space-y-4"
    >
      {/* Header controls row */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-accent" />
          <span className="text-[10px] font-bold uppercase tracking-widest text-foreground">
            AI Synthesis
          </span>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Preset vs Custom toggle pill */}
          <div className="inline-flex rounded-lg border border-foreground/10 p-0.5 bg-surface text-xs">
            <button
              type="button"
              onClick={() => {
                setIsCustomMode(false);
                updateCustomConfig(customProvider, customModel, customEndpoint, false);
              }}
              disabled={isSummarizing}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                !isCustomMode
                  ? "bg-accent text-on-accent shadow-sm"
                  : "text-foreground-secondary hover:text-foreground"
              }`}
            >
              Presets
            </button>
            <button
              type="button"
              onClick={() => {
                setIsCustomMode(true);
                updateCustomConfig(customProvider, customModel, customEndpoint, true);
              }}
              disabled={isSummarizing}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                isCustomMode
                  ? "bg-accent text-on-accent shadow-sm"
                  : "text-foreground-secondary hover:text-foreground"
              }`}
            >
              Custom
            </button>
          </div>

          {!isCustomMode ? (
            <label className="flex items-center gap-2 text-xs text-foreground-secondary">
              <span className="uppercase tracking-widest text-[10px] font-bold text-foreground-muted">
                Model
              </span>
              <select
                value={selectedModel}
                onChange={(e) => {
                  if (e.target.value === "__custom__") {
                    setIsCustomMode(true);
                    updateCustomConfig(customProvider, customModel, customEndpoint, true);
                  } else {
                    setSelectedModel(e.target.value);
                  }
                }}
                disabled={isSummarizing || models.length === 0}
                className="bg-surface border border-foreground/10 rounded-md px-2 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/40 disabled:opacity-50"
                title={modelsError ?? "Choose a model for summary generation"}
              >
                {models.length === 0 ? (
                  <option value="">{modelsError ?? "Loading..."}</option>
                ) : (
                  <>
                    {models.some((m) => m.provider === "gemini") && (
                      <optgroup label="Google Gemini (Cloud)">
                        {models
                          .filter((m) => m.provider === "gemini")
                          .map((m) => (
                            <option key={m.id} value={m.id}>
                              {m.id}
                            </option>
                          ))}
                      </optgroup>
                    )}
                    {models.some((m) => m.provider === "nvidia") && (
                      <optgroup label="NVIDIA NIM (Cloud)">
                        {models
                          .filter((m) => m.provider === "nvidia")
                          .map((m) => (
                            <option key={m.id} value={m.id}>
                              {m.id}
                            </option>
                          ))}
                      </optgroup>
                    )}
                    {models.some((m) => m.provider === "local") && (
                      <optgroup label="Local (LiteLLM Gateway)">
                        {models
                          .filter((m) => m.provider === "local")
                          .map((m) => (
                            <option key={m.id} value={m.id}>
                              {m.id}
                            </option>
                          ))}
                      </optgroup>
                    )}
                    <optgroup label="Custom Endpoint">
                      <option value="__custom__">⚙️ Provide Custom Endpoint / Model...</option>
                    </optgroup>
                  </>
                )}
              </select>
            </label>
          ) : null}

          {/* Temperature control */}
          <label className="flex items-center gap-2 text-xs text-foreground-secondary">
            <span className="uppercase tracking-widest text-[10px] font-bold text-foreground-muted">
              Temp
            </span>
            <input
              type="number"
              min={0}
              max={2}
              step={0.1}
              value={temperature}
              onChange={(e) => {
                const v = parseFloat(e.target.value);
                if (!Number.isNaN(v)) setTemperature(Math.min(2, Math.max(0, v)));
              }}
              disabled={isSummarizing}
              className="w-16 bg-surface border border-foreground/10 rounded-md px-2 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/40 disabled:opacity-50"
              title="Sampling temperature (0 = deterministic, 2 = very random). Default 0.3."
            />
          </label>

          {/* Action button */}
          <button
            onClick={handleTriggerGenerate}
            disabled={isSummarizing}
            className="bg-accent text-on-accent rounded-full px-5 py-2 text-sm font-medium transition-colors hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed shadow-warm-sm"
          >
            {buttonText}
          </button>
        </div>
      </div>

      {/* Custom configuration panel */}
      {isCustomMode && (
        <div className="rounded-xl border border-accent/20 bg-accent/5 p-4 space-y-3 text-xs text-foreground animate-in fade-in duration-200">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="font-semibold text-foreground flex items-center gap-2">
              <span>Custom Model & Endpoint Settings</span>
            </div>
            <span className="text-[11px] text-foreground-muted">
              Configuration is remembered for future papers
            </span>
          </div>

          {/* Provider selector pills */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-foreground-secondary font-medium">Provider:</span>
            <div className="flex gap-1.5 flex-wrap">
              <button
                type="button"
                onClick={() => handleProviderChange("nvidia")}
                className={`px-3 py-1 rounded-md border text-xs font-medium transition-all ${
                  customProvider === "nvidia"
                    ? "bg-accent text-on-accent border-accent"
                    : "bg-surface text-foreground-secondary border-foreground/10 hover:border-foreground/30"
                }`}
              >
                NVIDIA Cloud (NIM)
              </button>
              <button
                type="button"
                onClick={() => handleProviderChange("gemini")}
                className={`px-3 py-1 rounded-md border text-xs font-medium transition-all ${
                  customProvider === "gemini"
                    ? "bg-accent text-on-accent border-accent"
                    : "bg-surface text-foreground-secondary border-foreground/10 hover:border-foreground/30"
                }`}
              >
                Google Gemini
              </button>
              <button
                type="button"
                onClick={() => handleProviderChange("local")}
                className={`px-3 py-1 rounded-md border text-xs font-medium transition-all ${
                  customProvider === "local"
                    ? "bg-accent text-on-accent border-accent"
                    : "bg-surface text-foreground-secondary border-foreground/10 hover:border-foreground/30"
                }`}
              >
                Local / Gateway
              </button>
            </div>
          </div>

          {/* Form fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            {/* Model input */}
            <div>
              <label className="block text-[11px] font-semibold text-foreground-secondary mb-1">
                Model Name
              </label>
              <input
                type="text"
                value={customModel}
                onChange={(e) => handleCustomModelChange(e.target.value)}
                placeholder={
                  customProvider === "gemini"
                    ? "e.g. gemini-2.0-flash-exp"
                    : customProvider === "nvidia"
                      ? "e.g. meta/llama-3.3-70b-instruct"
                      : "e.g. nemotron3:nano"
                }
                list="preset-models-datalist"
                className="w-full bg-surface border border-foreground/15 rounded-md px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-accent/40"
              />
              <datalist id="preset-models-datalist">
                {models.map((m) => (
                  <option key={m.id} value={m.id} />
                ))}
              </datalist>
            </div>

            {/* Endpoint input (Nvidia & Local) */}
            {customProvider !== "gemini" ? (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-[11px] font-semibold text-foreground-secondary">
                    {customProvider === "nvidia" ? "NVIDIA NIM Endpoint URL" : "Gateway Endpoint URL"}
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      handleEndpointChange(
                        customProvider === "nvidia"
                          ? "https://integrate.api.nvidia.com/v1"
                          : "http://192.168.1.32:4000/v1"
                      )
                    }
                    className="text-[10px] text-accent hover:underline"
                  >
                    Reset default
                  </button>
                </div>
                <input
                  type="url"
                  value={customEndpoint}
                  onChange={(e) => handleEndpointChange(e.target.value)}
                  placeholder={
                    customProvider === "nvidia"
                      ? "https://integrate.api.nvidia.com/v1"
                      : "http://192.168.1.32:4000/v1"
                  }
                  className={`w-full bg-surface border ${
                    endpointError ? "border-red-500" : "border-foreground/15"
                  } rounded-md px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-accent/40`}
                />
                {endpointError && (
                  <p className="text-[10px] text-red-500 mt-1">{endpointError}</p>
                )}
              </div>
            ) : (
              <div className="flex items-end pb-1.5 text-foreground-muted text-[11px]">
                <span>Uses Google GenAI cloud service with server-configured GEMINI_API_KEY.</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Content area */}
      {summary ? (
        <>
          <div className="prose max-w-none prose-p:text-foreground-secondary prose-p:leading-relaxed prose-headings:text-foreground prose-strong:text-foreground prose-a:text-accent prose-a:no-underline hover:prose-a:underline prose-blockquote:border-accent/30">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex]}
            >
              {summary}
            </ReactMarkdown>
          </div>
          <p className="text-foreground-muted text-xs mt-6">
            Analysis completed
          </p>
        </>
      ) : isSummarizing ? (
        <div className="flex items-center gap-3 py-4">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
          </span>
          <p
            className="italic text-foreground-muted"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Reasoning through the paper... this may take 30-60 seconds.
          </p>
        </div>
      ) : (
        <p
          className="italic text-foreground-muted py-4"
          style={{ fontFamily: "var(--font-display)" }}
        >
          No AI analysis generated yet. Click Generate Analysis to start.
        </p>
      )}
    </section>
  );
}
