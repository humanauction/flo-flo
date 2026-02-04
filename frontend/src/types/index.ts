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