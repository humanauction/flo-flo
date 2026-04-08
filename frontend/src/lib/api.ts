import { AdminJob, AdminStats, Headline, GuessResult } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MAX_ADMIN_JOB_COUNT = 50;

async function requestJson<T>(
    url: string,
    init: RequestInit | undefined,
    errorMessage: string,
): Promise<T> {
    const res = await fetch(url, init);
    if (!res.ok) {
        throw new Error(errorMessage);
    }
    return res.json() as Promise<T>;
}

function validateCount(count: number): void {
    if (!Number.isInteger(count)) {
        throw new Error("count must be an integer");
    }
    if (count < 1 || count > MAX_ADMIN_JOB_COUNT) {
        throw new Error(`count must be between 1 and ${MAX_ADMIN_JOB_COUNT}`);
    }
}

export async function getHeadline(): Promise<Headline> {
    return requestJson<Headline>(
        `${API_BASE}/api/game/headline`,
        undefined,
        "Failed to fetch headline",
    );
}

export async function submitGuess(
    headlineId: number,
    guess: boolean,
): Promise<GuessResult> {
    return requestJson<GuessResult>(
        `${API_BASE}/api/game/guess`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ headline_id: headlineId, guess }),
        },
        "Failed to submit guess",
    );
}

export async function getAdminStats(): Promise<AdminStats> {
    return requestJson<AdminStats>(
        `${API_BASE}/api/admin/stats`,
        undefined,
        "Failed to fetch admin stats",
    );
}

export async function triggerScrapeJob(count: number): Promise<AdminJob> {
    validateCount(count);
    return requestJson<AdminJob>(
        `${API_BASE}/api/admin/scrape`,
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ count }),
        },
        "Failed to queue scrape job",
    );
}

export async function triggerGenerateJob(count: number): Promise<AdminJob> {
    validateCount(count);
    return requestJson<AdminJob>(
        `${API_BASE}/api/admin/generate`,
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ count }),
        },
        "Failed to queue generate job",
    );
}

export async function getAdminJobStatus(jobId: string): Promise<AdminJob> {
    return requestJson<AdminJob>(
        `${API_BASE}/api/admin/jobs/${jobId}`,
        undefined,
        "Failed to fetch job status",
    );
}