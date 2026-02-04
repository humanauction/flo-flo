import { GameStats } from "@/types";

interface ScoreBoardProps {
  stats: GameStats;
}

export default function ScoreBoard({ stats }: ScoreBoardProps) {
  const accuracy = stats.total > 0 
    ? Math.round((stats.correct / stats.total) * 100) 
    : 0;

  return (
    <div className="flex justify-center gap-6 mb-8">
      <div className="bg-blue-800/50 rounded-lg px-4 py-2 text-center">
        <div className="text-2xl font-bold text-white">{stats.correct}/{stats.total}</div>
        <div className="text-blue-300 text-sm">Score</div>
      </div>
      <div className="bg-blue-800/50 rounded-lg px-4 py-2 text-center">
        <div className="text-2xl font-bold text-white">{accuracy}%</div>
        <div className="text-blue-300 text-sm">Accuracy</div>
      </div>
      <div className="bg-blue-800/50 rounded-lg px-4 py-2 text-center">
        <div className="text-2xl font-bold text-orange-400">🔥 {stats.streak}</div>
        <div className="text-blue-300 text-sm">Streak</div>
      </div>
    </div>
  );
}