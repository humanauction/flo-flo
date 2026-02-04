import { GuessResult } from "@/types";

interface ResultModalProps {
    result: GuessResult | null;
    onNext: () => void;
}

export default function ResultModal({ result, onNext }: ResultModalProps) {
    if (!result) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-lg w-full text-center">
                <div className="text-6xl mb-4">
                    {result.correct ? "🎉" : "😬"}
                </div>
                
                <h2 className={`text-3xl font-bold mb-2 ${result.correct ? "text-green-600" : "text-red-600"}`}>
                    {result.correct ? "Correct!" : "Wrong!"}
                </h2>
                
                <p className="text-gray-600 mb-4">
                    This headline was <span className="font-bold">{result.was_real ? "REAL" : "FAKE"}</span>
                </p>
                
                <p className="text-gray-800 italic mb-4 text-sm">
                    &ldquo;{result.headline_text}&rdquo;
                </p>
                
                {result.source_url && (
                    <a 
                        href={result.source_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:underline text-sm block mb-6"
                    >
                        📰 View Source Article
                    </a>
                )}
                
                <button
                    onClick={onNext}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-xl transition-colors"
                >
                    Next Headline →
                </button>
            </div>
        </div>
    );
}