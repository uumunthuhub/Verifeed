import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Footer } from "@/components/Footer";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

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
    <html lang="en" className={`h-full ${inter.variable}`}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className={`${inter.className} min-h-full flex flex-col bg-background text-foreground antialiased`}>
        <div className="flex-1 flex flex-col mx-auto max-w-6xl w-full px-4">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
