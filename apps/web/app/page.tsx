import { Suspense } from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { AskAgent } from "@/components/AskAgent";
import { VerdictBadge } from "@/components/VerdictBadge";
import { fetchRecentVerifications } from "@/lib/api";
import { VerificationResult } from "@/lib/types";
import { CheckCircle2, ArrowRight } from "lucide-react";

interface PageProps {
  searchParams: Promise<{ category?: string }>;
}

async function RecentVerificationsSection() {
  const recentList = await fetchRecentVerifications();
  if (!recentList || recentList.length === 0) return null;

  return (
    <section className="py-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-bold text-ink-900">
            Recent Public Verifications
          </h2>
        </div>
        <Link
          href="/verify"
          className="text-sm font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-1 transition-colors"
        >
          <span>Verify another claim</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 justify-items-center">
        {recentList.slice(0, 6).map((item: VerificationResult) => (
          <Link
            key={item.id}
            href={`/verify/${item.id}`}
            className="group flex flex-col justify-between p-4 rounded-xl bg-white/70 backdrop-blur-xl border border-border shadow-lg hover:border-primary-300 hover:bg-white/90 hover:shadow-xl transition-all duration-300 w-full max-w-sm"
          >
            <div className="mb-3">
              <div className="flex items-center justify-between gap-2 mb-2">
                <VerdictBadge verdict={item.verdict || "Unconfirmed"} size="sm" />
                <span className="text-xs text-ink-500 font-mono">
                  {Math.round((item.confidence_score || 0.5) * 100)}% conf
                </span>
              </div>
              <p className="text-sm font-bold text-foreground group-hover:text-primary-600 transition-colors line-clamp-2">
                &ldquo;{item.query}&rdquo;
              </p>
            </div>
            <span className="text-xs text-ink-500 font-medium">
              Verified {new Date(item.created_at || "1970-01-01").toLocaleDateString()}
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}

export default async function HomePage({ searchParams }: PageProps) {
  const { category } = await searchParams;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar activeCategory={category ?? ""} maxWidth="max-w-6xl" />
      <div className="max-w-6xl mx-auto px-4 pt-8" style={{ position: "relative", zIndex: 1 }}>
        
        {/* Hero Section - Compact */}
        <section className="py-6 md:py-8">
          <div className="max-w-4xl mx-auto text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <span className="flex h-2 w-2 rounded-full bg-primary-500 animate-ping" />
              <span className="text-xs font-semibold text-primary-600 uppercase tracking-wider">Live News Feed & AI Verification</span>
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-black text-foreground tracking-tight mb-4">
              News you can <span className="text-primary-600">verify.</span>
            </h1>
            <p className="text-base md:text-lg text-ink-700 max-w-2xl mx-auto mb-8">
              Browse real-time headlines clustered from top outlets, or ask our AI verification agent to verify rumors & scam messages.
            </p>

            {/* Ask Agent Search Box */}
            <div className="mb-8">
              <AskAgent />
            </div>

            {/* Stats Row */}
            <div className="flex flex-wrap justify-center gap-8 md:gap-12">
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-black text-primary-600">15+</div>
                <div className="text-xs text-ink-500 uppercase tracking-wider mt-1">Verified Institutions</div>
              </div>
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-black text-primary-600">Real-time</div>
                <div className="text-xs text-ink-500 uppercase tracking-wider mt-1">Story Updates</div>
              </div>
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-black text-primary-600">RAG AI</div>
                <div className="text-xs text-ink-500 uppercase tracking-wider mt-1">Grounded Fact-checking</div>
              </div>
            </div>
          </div>
        </section>

        {/* Recent Public Verifications - Horizontal Row */}
        <Suspense fallback={null}>
          <RecentVerificationsSection />
        </Suspense>
      </div>
    </div>
  );
}
