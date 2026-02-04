import Game from "@/components/Game";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
     <main className="min-h-screen bg-gradient-to-b from-blue-900 to-blue-950">
        <Game />
      </main>
    </div>
  );
}
