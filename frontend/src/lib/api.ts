import { Headline, GuessResult } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getHeadline(): Promise<Headline> {
    const res = await fetch(`${API_BASE}/api/game/headline`);
    if(!res.ok) {
        throw new Error("Failed to fetch headline");
    }
    return res.json();
}

export async function submitGuess(headlineId: number, guess: boolean): Promise<GuessResult> {
    const res = await fetch(`${API_BASE}/api/game/guess`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ headline_id: headlineId, guess: guess }),
    });
    if(!res.ok) {
        throw new Error("Failed to submit guess");
    }
    return res.json();
}