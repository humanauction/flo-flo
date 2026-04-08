import Link from "next/link";

export default function Header() {
    return (
        <header className="text-center py-8">
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-2">
                Florida Man or AI Fiction
            </h1>
            <p className="text-blue-300 text-lg">
                Can you guess which headlines are real and which are AI-generated?
            </p>
            <div className="mt-4">
                <Link
                    href="/admin"
                    className="inline-block rounded-md border border-blue-300 px-4 py-2 text-sm text-blue-100 hover:bg-blue-800/40"
                >
                    Admin Panel
                </Link>
            </div>
        </header>
    );
}