import React from "react";
import { VerdictBadge } from "./VerdictBadge";
import { ConfidenceIndicator } from "./ConfidenceIndicator";
import { GuidanceCard } from "./GuidanceCard";
import { EvidenceCard, EvidenceSource } from "./EvidenceCard";
import { ExternalLink } from "lucide-react";

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
  verificationDetails?: {
    sender_verified?: boolean;
    channel_verified?: boolean;
    matched_institution?: string;
    image_authenticity?: {
      is_ai_generated?: boolean;
      confidence?: number;
      verdict_label?: string;
      detected_artifacts?: string[];
      analysis_explanation?: string;
    };
    audio_transcription?: string;
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
  verificationDetails,
  methodology,
}: VerdictFirstResultProps) {
  // Grounded unified 'Is It True?' verdict configuration
  let answerTitle = "UNVERIFIED — NO OFFICIAL COVERAGE FOUND";
  let answerSubtitle = "No official announcements or news articles corroborating this claim were found in registered news sources.";
  let answerIcon = "❓";
  let bannerClass = "bg-white text-ink-900 border-primary-200 shadow-xl shadow-primary-500/5";
  let badgeLabel = "Unverified Claim";

  if (claimVerdict === "True") {
    answerTitle = "YES, IT IS TRUE";
    answerSubtitle = "Verified news reports or official institutional statements confirm this claim.";
    answerIcon = "✅";
    bannerClass = "bg-white text-emerald-950 border-emerald-500 shadow-xl shadow-emerald-500/10";
    badgeLabel = "Confirmed True";
  } else if (claimVerdict === "False" && riskLevel !== "High") {
    answerTitle = "NO, IT IS NOT TRUE";
    answerSubtitle = "Official statements or verified news reports refute or debunk this claim.";
    answerIcon = "🚫";
    bannerClass = "bg-white text-red-950 border-red-500 shadow-xl shadow-red-500/10";
    badgeLabel = "Verified False";
  } else if (riskLevel === "High" || claimVerdict === "Confirmed Scam") {
    answerTitle = "NO — CONFIRMED FRAUD / SCAM WARNING";
    answerSubtitle = "This message matches known scam and phishing patterns. Do not trust, forward, or act on it.";
    answerIcon = "🚨";
    bannerClass = "bg-white text-rose-950 border-rose-500 shadow-xl shadow-rose-500/10";
    badgeLabel = "High Risk Scam";
  } else if (claimVerdict === "Misleading") {
    answerTitle = "PARTIALLY / UNCONFIRMED RUMOR";
    answerSubtitle = "Current news reports or evidence are partial, disputed, or ongoing.";
    answerIcon = "⚠️";
    bannerClass = "bg-white text-amber-950 border-amber-500 shadow-xl shadow-amber-500/10";
    badgeLabel = "Partially True / Unconfirmed";
  }

  return (
    <div className="space-y-6">
      {/* Submitted Claim Box */}
      {query && query !== "Unspecified claim" && (
        <div className="rounded-2xl border border-border bg-white p-5 shadow-xs">
          <span className="text-[11px] font-extrabold uppercase tracking-wider text-ink-500 block mb-2">
            Message / Claim Analyzed
          </span>
          <p className="text-base font-semibold text-foreground italic leading-relaxed">
            &ldquo;{query.length > 300 ? `${query.slice(0, 300)}…` : query}&rdquo;
          </p>
        </div>
      )}

      {/* SYNTHETIC MEDIA / AI IMAGE ANALYSIS CARD */}
      {verificationDetails?.image_authenticity && (
        <div className="rounded-2xl border border-purple-300 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between gap-2 mb-2 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-base">🎨</span>
              <span className="text-xs font-extrabold uppercase tracking-wider text-purple-900">
                AI Image & Synthetic Media Inspection
              </span>
            </div>
            <span className={`px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wider ${
              verificationDetails.image_authenticity.is_ai_generated
                ? "bg-purple-600 text-white"
                : "bg-emerald-600 text-white"
            }`}>
              {verificationDetails.image_authenticity.verdict_label || (verificationDetails.image_authenticity.is_ai_generated ? "AI Generated Image" : "Authentic Photo")}
            </span>
          </div>
          {verificationDetails.image_authenticity.analysis_explanation && (
            <p className="text-xs text-purple-950 font-medium leading-relaxed mb-2">
              {verificationDetails.image_authenticity.analysis_explanation}
            </p>
          )}
          {verificationDetails.image_authenticity.detected_artifacts && verificationDetails.image_authenticity.detected_artifacts.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {verificationDetails.image_authenticity.detected_artifacts.map((art, i) => (
                <span key={i} className="px-2 py-0.5 rounded-md bg-purple-100 border border-purple-200 text-[10px] font-semibold text-purple-800">
                  {art}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* AUDIO VOICE NOTE TRANSCRIPTION CARD */}
      {verificationDetails?.audio_transcription && (
        <div className="rounded-2xl border border-emerald-300 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-base">🎙️</span>
            <span className="text-xs font-extrabold uppercase tracking-wider text-emerald-900">
              Audio Voice Note Transcription & Analysis
            </span>
          </div>
          <p className="text-xs text-emerald-950 italic leading-relaxed bg-emerald-50/50 p-3.5 rounded-xl border border-emerald-200 font-medium">
            &ldquo;{verificationDetails.audio_transcription}&rdquo;
          </p>
        </div>
      )}

      {/* GROUNDED UNIFIED ANSWER CARD: IS IT TRUE? */}
      <div className={`rounded-2xl border-2 p-6 shadow-xl transition-all ${bannerClass}`}>
        <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
          <span className="text-xs font-black uppercase tracking-wider opacity-80 flex items-center gap-1.5">
            <span>🔍</span>
            <span>VERDICT — IS IT TRUE?</span>
          </span>
          <span className="text-xs font-bold px-3 py-1 rounded-full bg-primary-50 border border-primary-200 shadow-xs text-primary-900">
            {badgeLabel}
          </span>
        </div>

        <div className="flex items-start gap-4 mb-5">
          <span className="text-4xl md:text-5xl shrink-0 leading-none">{answerIcon}</span>
          <div>
            <h2 className="text-2xl md:text-3xl font-black tracking-tight leading-tight">
              {answerTitle}
            </h2>
            <p className="text-sm md:text-base font-semibold mt-1 opacity-90 leading-relaxed">
              {answerSubtitle}
            </p>
          </div>
        </div>

        {/* WHY? Interactive Evidence Explanation Card inside the Response Widget */}
        <div className="bg-white rounded-2xl p-5 md:p-6 border border-primary-200 shadow-md mt-4 text-ink-900">
          <div className="flex items-center gap-2 mb-3">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary-100 text-primary-700 text-sm font-bold">
              💡
            </span>
            <span className="text-xs md:text-sm font-black uppercase tracking-wider text-primary-800">
              WHY HAS VERIFEED REACHED THIS VERDICT?
            </span>
          </div>

          <div className="space-y-3">
            <p className="text-sm md:text-base font-bold text-ink-900 leading-relaxed">
              VeriFeed has found evidence regarding this claim or question:
            </p>
            <p className="text-sm md:text-base leading-relaxed text-ink-800 bg-white p-4 rounded-xl border border-border font-medium">
              {summary}
            </p>
          </div>

          {/* Interactive News Citations & Direct Links below */}
          {sources && sources.length > 0 && (
            <div className="mt-5 pt-4 border-t border-border">
              <span className="text-xs font-bold uppercase tracking-wider text-ink-600 block mb-3">
                📰 Verified News Coverage & Direct Articles:
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {sources.map((src, i) => (
                  <div key={i} className="flex flex-col justify-between p-3.5 rounded-xl bg-white border border-border hover:border-primary-400 hover:shadow-md transition-all">
                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-extrabold uppercase bg-primary-100 text-primary-800 border border-primary-200">
                          {src.outlet || "Verified Outlet"}
                        </span>
                        {src.type && (
                          <span className="text-[10px] text-ink-500 font-medium truncate">
                            {src.type}
                          </span>
                        )}
                      </div>
                      <h4 className="text-xs md:text-sm font-bold text-ink-900 line-clamp-2 leading-snug">
                        {src.title}
                      </h4>
                      {src.snippet && (
                        <p className="text-xs text-ink-600 line-clamp-2 mt-1 italic">
                          &ldquo;{src.snippet}&rdquo;
                        </p>
                      )}
                    </div>
                    {src.url && (
                      <div className="mt-3 pt-2 border-t border-border flex items-center justify-between">
                        <span className="text-[10px] text-ink-500 font-mono truncate max-w-[180px]">
                          {src.url.replace(/^https?:\/\//, '')}
                        </span>
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-bold text-primary-700 hover:text-primary-800 bg-primary-50 hover:bg-primary-100 px-3 py-1 rounded-lg border border-primary-300 transition-all shrink-0"
                        >
                          <span>Read News Article</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* EXTRACTED ENTITIES */}
      {extractedEntities && (
        <div className="rounded-2xl border border-border bg-white p-6 shadow-xs">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-xs font-extrabold uppercase tracking-wider text-ink-500">
              EXTRACTED INFORMATION
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {extractedEntities.sender && (
              <div className="bg-white rounded-lg p-3 border border-border">
                <span className="text-[10px] font-bold uppercase text-ink-500 block mb-1">Sender</span>
                <span className="text-xs font-medium text-ink-900">{extractedEntities.sender}</span>
              </div>
            )}
            {extractedEntities.institution_names && extractedEntities.institution_names.length > 0 && (
              <div className="bg-white rounded-lg p-3 border border-border">
                <span className="text-[10px] font-bold uppercase text-ink-500 block mb-1">Institution</span>
                <span className="text-xs font-medium text-ink-900">
                  {extractedEntities.institution_names[0]}
                  {extractedEntities.institution_names.length > 1 && ` +${extractedEntities.institution_names.length - 1}`}
                </span>
              </div>
            )}
            {extractedEntities.phone_numbers && extractedEntities.phone_numbers.length > 0 && (
              <div className="bg-white rounded-lg p-3 border border-border">
                <span className="text-[10px] font-bold uppercase text-ink-500 block mb-1">Numbers</span>
                <span className="text-xs font-medium text-ink-900">
                  {extractedEntities.phone_numbers[0]}
                  {extractedEntities.phone_numbers.length > 1 && ` +${extractedEntities.phone_numbers.length - 1}`}
                </span>
              </div>
            )}
            {extractedEntities.urls && extractedEntities.urls.length > 0 && (
              <div className="bg-white rounded-lg p-3 border border-border">
                <span className="text-[10px] font-bold uppercase text-ink-500 block mb-1">URLs</span>
                <span className="text-xs font-medium text-ink-900">
                  {extractedEntities.urls.length} detected
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ACTIONABLE GUIDANCE FOR CITIZENS */}
      <GuidanceCard
        riskLevel={riskLevel}
        messageAuthenticityVerdict={messageAuthenticityVerdict}
        claimVerdict={claimVerdict}
        recommendedActions={recommendedActions}
        verifiedInstitution={verifiedInstitution}
        officialChannels={officialChannels}
      />

      {/* EVIDENCE SOURCES */}
      {sources && sources.length > 0 && (
        <div className="rounded-2xl border border-border bg-white p-6 shadow-xs">
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

      {/* OPTIONAL TECHNICAL BREAKDOWN & RAW SCORES (COLLAPSED BY DEFAULT) */}
      <details className="rounded-2xl border border-border bg-white group">
        <summary className="flex items-center justify-between cursor-pointer select-none px-5 py-4 text-xs font-bold uppercase tracking-wider text-ink-500 hover:text-ink-900 transition-colors list-none">
          <span className="flex items-center gap-2">
            <span>🔬</span>
            <span>Technical Verification Details & Sub-scores</span>
          </span>
          <span className="text-xs font-semibold text-primary-600 group-open:rotate-180 transition-transform">▼</span>
        </summary>
        <div className="px-5 pb-5 space-y-4 border-t border-border pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {messageAuthenticityVerdict && (
              <div className="bg-white rounded-xl p-3.5 border border-border">
                <span className="text-[10px] font-bold uppercase tracking-wider text-ink-500 block mb-1.5">
                  Message Authenticity
                </span>
                <VerdictBadge verdict={messageAuthenticityVerdict} verdictType="authenticity" size="sm" />
              </div>
            )}
            {claimVerdict && (
              <div className="bg-white rounded-xl p-3.5 border border-border">
                <span className="text-[10px] font-bold uppercase tracking-wider text-ink-500 block mb-1.5">
                  Claim Verdict
                </span>
                <VerdictBadge verdict={claimVerdict} verdictType="claim" size="sm" />
              </div>
            )}
          </div>

          <ConfidenceIndicator score={confidenceScore} />

          {methodology && (
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-ink-500 block mb-1">
                Scoring Methodology
              </span>
              <p className="text-xs text-ink-600 leading-relaxed bg-white p-3 rounded-xl border border-border font-mono">
                {methodology}
              </p>
            </div>
          )}
        </div>
      </details>
    </div>
  );
}


