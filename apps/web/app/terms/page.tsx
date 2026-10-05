import type { Metadata } from "next";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { FileText, ShieldAlert, CheckCircle2, Scale } from "lucide-react";

export const metadata: Metadata = {
  title: "Terms of Service — VeriFeed",
  description: "Terms of Service and Verification Grounding Standards for the VeriFeed platform.",
};

export default function TermsPage() {
  const lastUpdated = "October 3, 2026";

  return (
    <div className="min-h-screen flex flex-col pb-16">
      <Navbar />

      <main className="flex-1 max-w-4xl mx-auto w-full px-4 pt-10">
        <header className="mb-10 text-center md:text-left bg-gradient-to-br from-white via-primary-50/30 to-white p-8 md:p-10 rounded-3xl border border-border shadow-sm">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-100 text-primary-700 text-xs font-bold mb-4">
            <Scale className="w-3.5 h-3.5" />
            <span>Platform Agreement</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-black text-ink-950 tracking-tight mb-3">
            VeriFeed Terms of Service
          </h1>
          <p className="text-sm text-ink-700 max-w-2xl leading-relaxed">
            These terms govern your access to and use of the VeriFeed platform, AI verification services, APIs, and mobile protection services.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-4 text-xs text-ink-500 pt-4 border-t border-border/60">
            <span><strong>Effective Date:</strong> {lastUpdated}</span>
            <span>•</span>
            <span><strong>Version:</strong> 2.0.0</span>
          </div>
        </header>

        <div className="bg-white border border-border rounded-3xl p-6 md:p-10 shadow-xs space-y-8 text-ink-800 text-sm leading-relaxed">
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-ink-950 flex items-center gap-2 border-b border-border/80 pb-2">
              <FileText className="w-5 h-5 text-primary-600" />
              1. Verification & Evidence Grounding Disclaimer
            </h2>
            <p>
              VeriFeed provides automated AI-assisted claim verification, rumor checking, and scam detection. VeriFeed never asserts truth from LLM judgment alone; all verdicts are grounded in retrieved evidence from verified public registries, news sources, and official institutional announcements.
            </p>
            <div className="bg-amber-50/70 p-4 rounded-xl border border-amber-200 text-xs text-amber-900 space-y-1">
              <div className="flex items-center gap-2 font-bold text-amber-950">
                <ShieldAlert className="w-4 h-4 text-amber-700" />
                <span>Notice on Critical Decisions</span>
              </div>
              <p>
                Verification verdicts are informative tools. Users should cross-reference critical legal, financial, or medical decisions with primary official bodies.
              </p>
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-bold text-ink-950 flex items-center gap-2 border-b border-border/80 pb-2">
              <CheckCircle2 className="w-5 h-5 text-primary-600" />
              2. Acceptable Use
            </h2>
            <p>
              By using VeriFeed, you agree not to attempt unauthorized API access, submit malicious payloads, or abuse our automated verification systems for spam or harassment.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-bold text-ink-950 flex items-center gap-2 border-b border-border/80 pb-2">
              <Scale className="w-5 h-5 text-primary-600" />
              3. Intellectual Property & Data Rights
            </h2>
            <p>
              The VeriFeed verification algorithms, UI design systems, brand assets, and aggregation structures are property of VeriFeed. Public evidence snippets remain the property of their respective publishers and original source outlets.
            </p>
          </section>
        </div>

        <div className="mt-8 text-center">
          <Link href="/" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-soft hover:bg-border text-ink-800 text-xs font-bold transition-all">
            ← Return to VeriFeed Home
          </Link>
        </div>
      </main>
    </div>
  );
}
