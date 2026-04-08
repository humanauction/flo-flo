export interface Headline {
    id: number;
    text: string;
}

export interface GuessResult {
    correct: boolean;
    was_real: boolean;
    source_url: string | null;
    headline_text: string;
}

export interface GameStats {
    total: number;
    correct: number;
    streak: number;
    bestStreak: number;   
}

export interface AdminStats {
    total_headlines: number;
    real_headlines: number;
    fake_headlines: number;
}

export type AdminJobType = "scrape"| "generate";
export type AdminJobStatus = "queued"| "running"| "completed"| "failed";

export interface AdminJob {
    job_id: string;
    job_type: AdminJobType;
    status: AdminJobStatus;
    requested_count: number;
    message: string;
    created_at: string;
    started_at: string | null;
    finished_at: string | null;
    error: string | null;
    result_summary: string | null;
}