"use client";

import { useState, useEffect, useCallback } from "react";
import { Headline, GuessResult, GameStats } from "@/types";
import { getHeadline, submitGuess } from "@/lib/api";
import Header from "./Header";
import ScoreBoard from "./ScoreBoard";
import GameCard from "./GameCard";
import ResultModal from "./ResultModal";

export default function Game() {
  const [headline, setHeadline] = useState<Headline | null>(null);
  const [result, setResult] = useState<GuessResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<GameStats>({
    total: 0,
    correct: 0,
    streak: 0,
    bestStreak: 0,
  });

  const fetchHeadline = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getHeadline();
      setHeadline(data);
    } catch (err) {
      setError("Failed to load headline. Is the backend running?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHeadline();
  }, [fetchHeadline]);

  const handleGuess = async (guess: boolean) => {
    if (!headline || submitting) return;
    
    setSubmitting(true);
    try {
      const guessResult = await submitGuess(headline.id, guess);
      setResult(guessResult);
      
      setStats(prev => ({
        total: prev.total + 1,
        correct: prev.correct + (guessResult.correct ? 1 : 0),
        streak: guessResult.correct ? prev.streak + 1 : 0,
        bestStreak: guessResult.correct 
          ? Math.max(prev.bestStreak, prev.streak + 1)
          : prev.bestStreak,
      }));
    } catch (err) {
      setError("Failed to submit guess");
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    setResult(null);
    fetchHeadline();
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <Header />
      <ScoreBoard stats={stats} />
      
      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-200 rounded-lg p-4 mb-6 max-w-2xl mx-auto text-center">
          {error}
          <button 
            onClick={fetchHeadline}
            className="ml-4 underline hover:no-underline"
          >
            Retry
          </button>
        </div>
      )}
      
      <GameCard 
        headline={headline}
        onGuess={handleGuess}
        disabled={submitting || !!result}
        loading={loading}
      />
      
      <ResultModal result={result} onNext={handleNext} />
    </div>
  );
}