/**
 * Verify Page — Claim Verification Lab
 *
 * Updated for Phase C: now includes the QuickScreenWidget for Stage 1
 * instant screening before full Stage 2 verification.
 *
 * URL param pre-population: ?content=<encoded> pre-fills the AskAgent
 * input, allowing share-to-VeriFeed flows from any source.
 */

import { Navbar } from "@/components/Navbar";
import { AskAgentWithContent } from "@/components/AskAgentWithContent";
import { QuickScreenWidget } from "@/components/QuickScreenWidget";
import { VerdictBadge } from "@/components/VerdictBadge";
import { fetchRecentVerifications } from "@/lib/api";

export const metadata = {
  title: "Claim Verification Lab — VeriFeed",
  description:
    "Verify headlines, rumors, and forwarded scam messages using grounded RAG AI synthesis and evidence trails.",
};

interface VerifyPageProps {
  searchParams: Promise<{ content?: string }>;
}

export default async function VerifyPage({ searchParams }: VerifyPageProps) {
  const { content: prefilledContent } = await searchParams;
  const recentVerifications = await fetchRecentVerifications();

  // Decode and sanitise the pre-filled content from URL param
  const initialContent = prefilledContent
    ? decodeURIComponent(prefilledContent).slice(0, 2000)
    : undefined;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar maxWidth="max-w-6xl" />
      <div className="max-w-6xl mx-auto px-4 pt-8">
        {/* Page Header */}
        <div className="mb-6 text-center max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-primary-50 text-primary-600 border border-primary-200 mb-3">
            <span>🤖 AI Grounded RAG Verification</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-black text-foreground tracking-tight mb-3">
            VeriFeed{" "}
            <span className="bg-linear-to-r from-primary-500 via-primary-600 to-primary-500 bg-clip-text text-transparent">
              Claim Lab
            </span>
          </h1>
          <p className="text-sm md:text-base text-gray-600">
            Check any claim against our indexed news sources, Google Fact Check
            database, and official institutional fraud registries.
          </p>
        </div>

        {/* Pre-fill notice — shown when content arrives via URL param */}
        {initialContent && (
          <div className="mb-4 flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-xs font-medium text-amber-800">
            <span>📎</span>
            <span>
              Content pre-filled from shared link —{" "}
              <strong>review below before verifying.</strong>
            </span>
          </div>
        )}

        {/* Two-column layout: Stage 1 Quick Screen + Stage 2 Full Verify */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
          {/* Stage 1 — Quick Screen (2/5 width on desktop) */}
          <div className="lg:col-span-2">
            <div className="sticky top-6">
              <div className="flex items-center gap-2 mb-3">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-100 text-xs font-black text-amber-700">
                  1
                </span>
                <span className="text-sm font-bold text-foreground">
                  Quick Screen
                </span>
                <span className="text-xs text-ink-500">Instant · No AI</span>
              </div>
              <QuickScreenWidget />
            </div>
          </div>

          {/* Stage 2 — Full Verification (3/5 width on desktop) */}
          <div className="lg:col-span-3">
            <div className="flex items-center gap-2 mb-3">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary-100 text-xs font-black text-primary-700">
                2
              </span>
              <span className="text-sm font-bold text-foreground">
                Deep Verification
              </span>
              <span className="text-xs text-ink-500">
                Evidence + AI · Full verdict
              </span>
            </div>
            <AskAgentWithContent initialContent={initialContent} />
          </div>
        </div>

        {/* Recent Community Verifications Feed */}
        <section className="mt-10">
          <div className="flex items-center justify-between mb-6 border-b border-border pb-3">
            <h2 className="text-lg md:text-xl font-bold text-foreground flex items-center gap-2">
              <span>🕒</span>
              <span>Recent Public Claim Checks</span>
            </h2>
            <span className="text-xs text-ink-500 font-medium">
              Updated real-time
            </span>
          </div>

          {recentVerifications.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-border p-8 text-center text-ink-500">
              No recent public claim verifications recorded yet. Be the first to
              test a claim above!
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recentVerifications.map((item) => (
                <div
                  key={item.id}
                  className="group flex flex-col justify-between rounded-2xl border border-border bg-surface p-5 hover:border-primary-300 hover:bg-soft transition-all shadow-lg"
                >
                  <div>
                    <div className="flex items-center justify-between gap-3 mb-3">
                      <VerdictBadge verdict={item.verdict} size="sm" />
                      <span className="text-xs text-ink-500">
                        {new Date(item.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-foreground mb-2 line-clamp-2">
                      &ldquo;{item.query}&rdquo;
                    </h3>

                    <p className="text-xs text-ink-500 line-clamp-3 leading-relaxed mb-4">
                      {item.summary}
                    </p>
                  </div>

                  <div className="flex items-center justify-between text-xs text-ink-500 pt-3 border-t border-border">
                    <span>Sources cited: {item.sources?.length || 0}</span>
                    <span className="text-primary-500 font-medium group-hover:underline">
                      Confidence: {Math.round(item.confidence_score * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
