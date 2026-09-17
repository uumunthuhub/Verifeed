import React from "react";
import { VerdictBadge } from "./VerdictBadge";
import { ConfidenceIndicator } from "./ConfidenceIndicator";
import { GuidanceCard } from "./GuidanceCard";
import { EvidenceCard, EvidenceSource } from "./EvidenceCard";

interface VerdictFirstResultProps {
  query?: string;
  claimVerdict?: string;
  messageAuthenticityVerdict?: string;
  riskLevel: "High" | "Medium" | "Low";
  confidenceScore: number;
  summary: string;
  sources: EvidenceSource[];
  recommendedActions: Array<{
    action: string;
    priority: "critical" | "high" | "medium" | "low";
    reason?: string;
  }>;
  verifiedInstitution?: string;
  officialChannels?: string[];
  extractedEntities?: {
    sender?: string;
    phone_numbers?: string[];
    urls?: string[];
    institution_names?: string[];
  };
  /** D2: Human-readable explanation of how the verdict was reached */
  methodology?: string;
}

export function VerdictFirstResult({
  query,
  claimVerdict,
  messageAuthenticityVerdict,
  riskLevel,
  confidenceScore,
  summary,
  sources,
  recommendedActions,
  verifiedInstitution,
  officialChannels,
  extractedEntities,
  methodology,
}: VerdictFirstResultProps) {
  return (
    <div className="space-y-6">
      {/* Submitted Claim Box */}
      {query && query !== "Unspecified claim" && (
        <div className="rounded-2xl border border-border bg-soft p-5">
          <span className="text-[11px] font-extrabold uppercase tracking-wider text-ink-500 block mb-2">
            Message / Claim Analyzed
          </span>
          <p className="text-sm font-medium text-foreground italic leading-relaxed">
            &ldquo;{query.length > 300 ? `${query.slice(0, 300)}…` : query}&rdquo;
          </p>
        </div>
      )}

      {/* VERDICT SECTION - Prominent at top */}
      <div className="rounded-2xl border-2 border-border bg-surface p-6 shadow-xl">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xs font-extrabold uppercase tracking-wider text-ink-500">
            VERDICT
          </span>
        </div>

        {/* Dual Verdict Display */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Message Authenticity Verdict */}
          {messageAuthenticityVerdict && (
            <div className="bg-soft rounded-xl p-4 border border-border">
              <span className="text-[11px] font-bold uppercase tracking-wider text-ink-500 block mb-2">
                Message Authenticity
              </span>
              <VerdictBadge 
                verdict={messageAuthenticityVerdict} 
                verdictType="authenticity" 
                size="lg" 
              />
            </div>
          )}

          {/* Claim Verdict */}
          {claimVerdict && (
            <div className="bg-soft rounded-xl p-4 border border-border">
              <span className="text-[11px] font-bold uppercase tracking-wider text-ink-500 block mb-2">
                Claim Verdict
              </span>
              <VerdictBadge 
                verdict={claimVerdict} 
                verdictType="claim" 
                size="lg" 
              />
            </div>
          )}
        </div>

        {/* Risk Level */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs font-semibold text-ink-500">Risk Level:</span>
          <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
            riskLevel === "High" ? "bg-danger/20 text-danger border-danger/50" :
            riskLevel === "Medium" ? "bg-warning/20 text-warning border-warning/50" :
            "bg-success/20 text-success border-success/50"
          }`}>
            {riskLevel}
          </span>
        </div>

        {/* Evidence Strength */}
        <ConfidenceIndicator score={confidenceScore} />
      </div>

      {/* EXTRACTED ENTITIES */}
      {extractedEntities && (
        <div className="rounded-2xl border border-border bg-surface p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-xs font-extrabold uppercase tracking-wider text-ink-500">
              EXTRACTED INFORMATION
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {extractedEntities.sender && (
              <div className="bg-soft rounded-lg p-3 border border-border">
                <span className="text-[10px] font-bold uppercase text-ink-500 block mb-1">Sender</span>
                <span className="text-xs font-medium text-ink-900">{extractedEntities.sender}</span>
              </div>
            )}
            {extractedEntities.institution_names && extractedEntities.institution_names.length > 0 && (
              <div className="bg-soft rounded-lg p-3 border border-border">
                <span className="text-[10px] font-bold uppercase text-ink-500 block mb-1">Institution</span>
                <span className="text-xs font-medium text-ink-900">
                  {extractedEntities.institution_names[0]}
                  {extractedEntities.institution_names.length > 1 && ` +${extractedEntities.institution_names.length - 1}`}
                </span>
              </div>
            )}
            {extractedEntities.phone_numbers && extractedEntities.phone_numbers.length > 0 && (
              <div className="bg-soft rounded-lg p-3 border border-border">
                <span className="text-[10px] font-bold uppercase text-ink-500 block mb-1">Numbers</span>
                <span className="text-xs font-medium text-ink-900">
                  {extractedEntities.phone_numbers[0]}
                  {extractedEntities.phone_numbers.length > 1 && ` +${extractedEntities.phone_numbers.length - 1}`}
                </span>
              </div>
            )}
            {extractedEntities.urls && extractedEntities.urls.length > 0 && (
              <div className="bg-soft rounded-lg p-3 border border-border">
                <span className="text-[10px] font-bold uppercase text-ink-500 block mb-1">URLs</span>
                <span className="text-xs font-medium text-ink-900">
                  {extractedEntities.urls.length} detected
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SUMMARY */}
      <div className="rounded-2xl border border-border bg-surface p-6">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xs font-extrabold uppercase tracking-wider text-ink-500">
            WHY?
          </span>
        </div>
        <p className="text-base leading-relaxed text-ink-900 font-medium">
          {summary}
        </p>
      </div>

      {/* METHODOLOGY — how the verdict was reached */}
      {methodology && (
        <details
          id="verdict-methodology"
          className="rounded-2xl border border-border bg-soft"
        >
          <summary className="flex items-center gap-2 cursor-pointer select-none px-5 py-3 text-xs font-bold uppercase tracking-wider text-ink-500 hover:text-ink-900 transition-colors list-none">
            <span>🔬</span>
            <span>How this verdict was reached</span>
          </summary>
          <div className="px-5 pb-4">
            <p className="text-xs text-ink-500 leading-relaxed">{methodology}</p>
          </div>
        </details>
      )}

      {/* GUIDANCE */}
      <GuidanceCard
        riskLevel={riskLevel}
        messageAuthenticityVerdict={messageAuthenticityVerdict}
        claimVerdict={claimVerdict}
        recommendedActions={recommendedActions}
        verifiedInstitution={verifiedInstitution}
        officialChannels={officialChannels}
      />

      {/* EVIDENCE */}
      {sources && sources.length > 0 && (
        <div className="rounded-2xl border border-border bg-surface p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-extrabold uppercase tracking-wider text-ink-500">
                EVIDENCE
              </span>
            </div>
            <span className="text-xs text-ink-500">{sources.length} sources</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sources.map((source, idx) => (
              <EvidenceCard key={idx} source={source} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
