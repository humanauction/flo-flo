"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
    getAdminJobStatus,
    getAdminStats,
    triggerGenerateJob,
    triggerScrapeJob,
} from "@/lib/api";
import type { AdminJob, AdminStats } from "@/types";

const POLL_MS = 1200;
const MAX_COUNT = 50;

export default function AdminPage() {
    const [countInput, setCountInput] = useState("1");
    const [stats, setStats] = useState<AdminStats | null>(null);
    const [job, setJob] = useState<AdminJob | null>(null);
    const [loadingStats, setLoadingStats] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const parsedCount = useMemo(() => Number(countInput), [countInput]);
    const countIsValid =
        Number.isInteger(parsedCount) &&
        parsedCount >= 1 &&
        parsedCount <= MAX_COUNT;

    const loadStats = useCallback(async () => {
        setLoadingStats(true);
        try {
            const data = await getAdminStats();
            setStats(data);
        } catch (err) {
            setError("Failed to load admin stats.");
            console.error(err);
        } finally {
            setLoadingStats(false);
        }
    }, []);

    useEffect(() => {
        void loadStats();
    }, [loadStats]);

    useEffect(() => {
        if (!job) return;
        if (job.status === "completed" || job.status === "failed") return;

        let canceled = false;
        const timer = window.setInterval(async () => {
            try {
                const next = await getAdminJobStatus(job.job_id);
                if (canceled) return;
                setJob(next);

                if (next.status === "completed" || next.status === "failed") {
                    setSubmitting(false);
                    void loadStats();
                }
            } catch (err) {
                if (canceled) return;
                setSubmitting(false);
                setError("Failed to refresh job status.");
                console.error(err);
            }
        }, POLL_MS);

        return () => {
            canceled = true;
            window.clearInterval(timer);
        };
    }, [job, loadStats]);

    const startJob = async (jobType: "scrape" | "generate") => {
        setError(null);

        if (!countIsValid) {
            setError(`Count must be an integer between 1 and ${MAX_COUNT}.`);
            return;
        }

        setSubmitting(true);

        try {
            const queued =
                jobType === "scrape"
                    ? await triggerScrapeJob(parsedCount)
                    : await triggerGenerateJob(parsedCount);

            setJob(queued);
        } catch (err) {
            setSubmitting(false);
            setError(
                jobType === "scrape"
                    ? "Failed to queue scrape job."
                    : "Failed to queue generate job.",
            );
            console.error(err);
        }
    };

    return (
        <main className="min-h-screen bg-gradient-to-b from-blue-900 to-blue-950 px-4 py-8">
            <section className="mx-auto w-full max-w-3xl rounded-xl border border-blue-300/25 bg-black/25 p-6">
                <div className="mb-6 flex items-center justify-between">
                    <h1 className="text-2xl font-semibold text-white">Admin Jobs</h1>
                    <Link
                        href="/"
                        className="rounded-md border border-blue-300 px-3 py-1 text-sm text-blue-100 hover:bg-blue-800/40"
                    >
                        Back to Game
                    </Link>
                </div>

                <div className="mb-6 grid gap-3 sm:grid-cols-[1fr_auto_auto]">
                    <label className="flex flex-col text-sm text-blue-100">
                        Count
                        <input
                            type="number"
                            min={1}
                            max={MAX_COUNT}
                            value={countInput}
                            onChange={(e) => setCountInput(e.target.value)}
                            className="mt-1 rounded-md border border-blue-300/40 bg-zinc-900 px-3 py-2 text-white"
                        />
                    </label>

                    <button
                        type="button"
                        onClick={() => void startJob("scrape")}
                        disabled={submitting || !countIsValid}
                        className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                    >
                        Trigger Scrape
                    </button>

                    <button
                        type="button"
                        onClick={() => void startJob("generate")}
                        disabled={submitting || !countIsValid}
                        className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                    >
                        Trigger Generate
                    </button>
                </div>

                {error && (
                    <div className="mb-4 rounded-md border border-red-400/40 bg-red-500/20 p-3 text-sm text-red-100">
                        {error}
                    </div>
                )}

                <div className="mb-6 rounded-md border border-blue-300/20 bg-zinc-900/70 p-4">
                    <div className="mb-2 flex items-center justify-between">
                        <h2 className="text-sm font-semibold text-blue-100">
                            Headline Pool Stats
                        </h2>
                        <button
                            type="button"
                            onClick={() => void loadStats()}
                            className="rounded border border-blue-300/40 px-2 py-1 text-xs text-blue-100"
                        >
                            Refresh
                        </button>
                    </div>

                    {loadingStats || !stats ? (
                        <p className="text-sm text-blue-200">Loading stats...</p>
                    ) : (
                        <div className="grid grid-cols-3 gap-3 text-sm">
                            <div className="rounded bg-black/25 p-2 text-center">
                                <div className="text-blue-200">Total</div>
                                <div className="text-lg font-semibold text-white">
                                    {stats.total_headlines}
                                </div>
                            </div>
                            <div className="rounded bg-black/25 p-2 text-center">
                                <div className="text-blue-200">Real</div>
                                <div className="text-lg font-semibold text-white">
                                    {stats.real_headlines}
                                </div>
                            </div>
                            <div className="rounded bg-black/25 p-2 text-center">
                                <div className="text-blue-200">Fake</div>
                                <div className="text-lg font-semibold text-white">
                                    {stats.fake_headlines}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="rounded-md border border-blue-300/20 bg-zinc-900/70 p-4">
                    <h2 className="mb-2 text-sm font-semibold text-blue-100">
                        Latest Job
                    </h2>

                    {!job ? (
                        <p className="text-sm text-blue-200">No jobs queued yet.</p>
                    ) : (
                        <div className="space-y-2 text-sm text-blue-100">
                            <div>Job ID: {job.job_id}</div>
                            <div>Type: {job.job_type}</div>
                            <div>Status: {job.status}</div>
                            <div>Requested Count: {job.requested_count}</div>
                            <div>Message: {job.message}</div>
                            {job.error && (
                                <div className="text-red-300">Error: {job.error}</div>
                            )}
                            {job.result_summary && (
                                <pre className="mt-2 overflow-auto rounded bg-black/35 p-3 text-xs text-slate-100">
{job.result_summary}
                                </pre>
                            )}
                        </div>
                    )}
                </div>
            </section>
        </main>
    );
}