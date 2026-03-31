"use client";

import { useState, useEffect } from "react";
import { Save } from "lucide-react";
import { toast } from "sonner";
import { api } from "../../lib/api";
import RippleButton from "../../components/RippleButton";

export default function SettingsPage() {
    const [keywords, setKeywords] = useState("");
    const [email, setEmail] = useState("");
    const [frequency, setFrequency] = useState("daily");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Load config for a default user (or from auth context if we had one)
        // For now, we'll assume a default email or just let the user type it
        const loadConfig = async () => {
            // In a real app, we'd get the email from the session
        };
        loadConfig();
    }, []);

    const handleSave = async () => {
        setLoading(true);
        try {
            await api.updateUserConfig({
                email,
                keywords: keywords.split(",").map(k => k.trim()).filter(k => k),
                categories: ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO", "cs.MA", "cs.NE", "cs.IR", "cs.SI", "cs.HC", "cs.CY"]
            });
            toast.success("Settings saved successfully!");
        } catch (error) {
            console.error(error);
            toast.error("Failed to save settings.");
        } finally {
            setLoading(false);
        }
    };

    const handleLoad = async () => {
        if (!email) return;
        setLoading(true);
        try {
            const config = await api.getUserConfig(email);
            setKeywords(config.keywords.join(", "));
            // setCategories(config.categories);
        } catch (error) {
            console.error(error);
            // Don't show error if it's just a 404 (new user)
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="max-w-2xl space-y-6">
            {/* Page Header */}
            <div>
                <h1 className="font-display text-3xl font-light text-foreground">Settings</h1>
                <p className="text-foreground-secondary mt-2">Manage your preferences and notifications.</p>
            </div>

            {/* Research Interests Section */}
            <div className="bg-surface-card rounded-xl border border-[#D5CFC4] shadow-warm-sm p-6">
                <h2 className="font-display text-xl text-foreground mb-4">Research Interests</h2>
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-foreground-secondary">
                        Keywords (comma separated)
                    </label>
                    <input
                        type="text"
                        value={keywords}
                        onChange={(e) => setKeywords(e.target.value)}
                        placeholder="e.g. transformers, reinforcement learning, NLP"
                        className="w-full bg-surface-inset border border-[#D5CFC4] rounded-lg px-4 py-2.5 text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-accent"
                    />
                    <p className="text-xs text-foreground-muted">
                        We will prioritize papers matching these keywords in your daily summary.
                    </p>
                </div>
            </div>

            {/* Notifications Section */}
            <div className="bg-surface-card rounded-xl border border-[#D5CFC4] shadow-warm-sm p-6 space-y-5">
                <h2 className="font-display text-xl text-foreground mb-4">Notifications</h2>
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-foreground-secondary">
                        Email Address
                    </label>
                    <div className="flex gap-2">
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com"
                            className="w-full bg-surface-inset border border-[#D5CFC4] rounded-lg px-4 py-2.5 text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-accent"
                        />
                        <button
                            onClick={handleLoad}
                            className="bg-surface-inset border border-[#D5CFC4] text-foreground hover:bg-[#DDD8CD] px-4 py-2.5 rounded-lg text-sm transition-colors"
                        >
                            Load
                        </button>
                    </div>
                </div>
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-foreground-secondary">
                        Frequency
                    </label>
                    <select
                        value={frequency}
                        onChange={(e) => setFrequency(e.target.value)}
                        className="w-full bg-surface-inset border border-[#D5CFC4] rounded-lg px-4 py-2.5 text-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                    >
                        <option value="daily">Daily Digest</option>
                        <option value="weekly">Weekly Summary</option>
                        <option value="realtime">Real-time (High Volume)</option>
                    </select>
                </div>
            </div>

            {/* Save Button */}
            <RippleButton
                onClick={handleSave}
                disabled={loading}
                className="flex items-center justify-center w-full bg-accent hover:bg-accent-hover text-on-accent px-4 py-3 rounded-lg font-display font-medium transition-colors shadow-warm-sm disabled:opacity-50"
            >
                <Save className="h-4 w-4 mr-2" />
                {loading ? "Saving..." : "Save Changes"}
            </RippleButton>
        </div>
    );
}
