import type { Metadata } from "next";
import { Footer } from "@/components/Footer";
import "./globals.css";

export const metadata: Metadata = {
  title: "VeriFeed — AI-Powered News Fact-Checking",
  description:
    "VeriFeed clusters news from multiple sources and AI-verifies claims in real time. Get the truth behind every headline.",
  keywords: ["fact check", "news", "AI", "verification", "VeriFeed"],
  openGraph: {
    title: "VeriFeed — AI-Powered News Fact-Checking",
    description: "See how every story is covered across sources — and what's actually true.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />
      </head>
      <body className="font-sans min-h-full flex flex-col bg-background text-foreground antialiased">
        <div className="flex-1 flex flex-col mx-auto max-w-6xl w-full px-4">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
