import { notFound } from "next/navigation";
import { fetchVerificationById } from "@/lib/api";
import { VerdictFirstResult } from "@/components/VerdictFirstResult";
import { Navbar } from "@/components/Navbar";
import Link from "next/link";
import { ArrowLeft, ShieldCheck } from "lucide-react";

interface PageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function VerificationResultPage({ params }: PageProps) {
  const resolvedParams = await params;
  const result = await fetchVerificationById(resolvedParams.id);

  if (!result) {
    notFound();
  }

  // Transform result to match new VerdictFirstResult structure
  // For backward compatibility, map legacy single verdict to dual verdict system
  const claimVerdict = result.claim_verdict || undefined;
  const messageAuthenticityVerdict =
    result.message_authenticity_verdict || undefined;

  // Default risk level based on verdict if not provided
  const riskLevel =
    result.risk_level ||
    (result.verdict === "Confirmed Scam"
      ? "High"
      : result.verdict === "Disputed / False"
        ? "High"
        : result.verdict === "Unconfirmed"
          ? "Medium"
          : "Low");

  // Default recommended actions based on risk level
  const recommendedActions = result.recommended_actions || [
    {
      action:
        riskLevel === "High"
          ? "Do not send money or share personal information"
          : "Verify the information independently",
      priority: riskLevel === "High" ? "critical" : "medium",
      reason:
        riskLevel === "High"
          ? "High-risk message detected"
          : "Standard verification precaution",
    },
    {
      action: "Contact the institution using official channels",
      priority: "high",
      reason: "Always verify through official communication channels",
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar maxWidth="max-w-6xl" />
      <main className="max-w-6xl mx-auto px-4 pt-8">
        <div className="mb-6">
          <Link
            href="/verify"
            className="inline-flex items-center gap-2 text-xs font-semibold text-primary-600 hover:text-primary-700 transition-colors bg-primary-50 px-3 py-1.5 rounded-full border border-primary-200"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Verification Lab
          </Link>
        </div>

        {/* Header */}
        <div className="flex items-center justify-between gap-4 text-xs font-semibold text-ink-500 mb-6 pb-4 border-b border-border">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-primary-600" />
            <span className="uppercase tracking-wider">
              Verification Report
            </span>
          </div>
          <time dateTime={result.created_at} className="text-ink-500">
            {new Date(result.created_at).toLocaleDateString("en-US", {
              year: "numeric",
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </time>
        </div>

        {/* Submitted Claim Query */}
        <div className="mb-6">
          <span className="text-[11px] font-bold uppercase tracking-wider text-ink-500 block mb-2">
            Message / Claim Analyzed
          </span>
          <p className="text-sm text-ink-700 leading-relaxed bg-soft p-4 rounded-xl border border-border font-normal">
            &ldquo;{result.query}&rdquo;
          </p>
        </div>

        {/* Verdict-First Result Display */}
        <VerdictFirstResult
          claimVerdict={claimVerdict}
          messageAuthenticityVerdict={messageAuthenticityVerdict}
          riskLevel={riskLevel as "High" | "Medium" | "Low"}
          confidenceScore={result.confidence_score}
          summary={result.summary}
          sources={result.sources || []}
          recommendedActions={recommendedActions}
          verifiedInstitution={result.verification_details?.matched_institution}
          officialChannels={result.verification_details?.matched_channels}
          extractedEntities={{
            sender: result.extracted_sender,
            phone_numbers: result.extracted_numbers,
            urls: result.extracted_urls,
            institution_names: result.extracted_institutions,
          }}
          methodology={result.methodology}
        />
      </main>
    </div>
  );
}
