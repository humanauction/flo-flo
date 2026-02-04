import { Headline } from "@/types";

interface GameCardProps {
  headline: Headline | null;
  onGuess: (isReal: boolean) => void;
  disabled: boolean;
  loading: boolean;
}

export default function GameCard({ headline, onGuess, disabled, loading }: GameCardProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-2xl mx-auto">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-3/4 mx-auto mb-4"></div>
          <div className="h-6 bg-gray-200 rounded w-1/2 mx-auto"></div>
        </div>
      </div>
    );
  }

  if (!headline) {
    return (
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-2xl mx-auto text-center">
        <p className="text-gray-600">No headlines available. Check back later!</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-xl p-8 max-w-2xl mx-auto">
      <p className="text-gray-800 text-xl md:text-2xl font-medium text-center mb-8 leading-relaxed">
        &ldquo;{headline.text}&rdquo;
      </p>
      
      <div className="flex gap-4 justify-center">
        <button
          onClick={() => onGuess(true)}
          disabled={disabled}
          className="flex-1 max-w-40 bg-green-500 hover:bg-green-600 disabled:bg-gray-300 
                     text-white font-bold py-4 px-6 rounded-xl transition-colors
                     text-lg shadow-lg hover:shadow-xl"
        >
          ✅ Real
        </button>
        <button
          onClick={() => onGuess(false)}
          disabled={disabled}
          className="flex-1 max-w-40 bg-red-500 hover:bg-red-600 disabled:bg-gray-300 
                     text-white font-bold py-4 px-6 rounded-xl transition-colors
                     text-lg shadow-lg hover:shadow-xl"
        >
          ❌ Fake
        </button>
      </div>
    </div>
  );
}