import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Florida Man or AI Fiction",
  description: "Guess real Florida Man headlines from fictional AI-generated ones?",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
