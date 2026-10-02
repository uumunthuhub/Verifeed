"use client";

// ---------------------------------------------------------------------------
// Canonical 5-label verdict constants (G1 fix — Phase 1)
// All new code must use these. Legacy labels remain as fallback only.
// ---------------------------------------------------------------------------

export type CanonicalVerdict =
  | "VERIFIED_TRUE"
  | "VERIFIED_FALSE"
  | "HIGH_RISK_SCAM"
  | "PENDING_VERIFICATION"
  | "UNVERIFIED";

// Legacy verdict types kept for backward compat reads from old API responses
type LegacyClaimVerdict = "True" | "False" | "Partly True" | "Misleading" | "Insufficient Evidence";
type LegacyAuthenticityVerdict =
  | "Verified Official"
  | "Likely Legitimate"
  | "Unverified"
  | "Suspicious"
  | "Likely Fraudulent"
  | "Confirmed Fraudulent";
type LegacySingleVerdict =
  | "Confirmed Scam"
  | "Confirmed"
  | "Unconfirmed"
  | "Disputed / False"
  | "No Coverage Found";

type AnyVerdict = CanonicalVerdict | LegacyClaimVerdict | LegacyAuthenticityVerdict | LegacySingleVerdict | string;

// ---------------------------------------------------------------------------
// Legacy → Canonical mapping
// ---------------------------------------------------------------------------

function toCanonical(verdict: AnyVerdict): CanonicalVerdict {
  const map: Record<string, CanonicalVerdict> = {
    // New canonical (pass-through)
    VERIFIED_TRUE: "VERIFIED_TRUE",
    VERIFIED_FALSE: "VERIFIED_FALSE",
    HIGH_RISK_SCAM: "HIGH_RISK_SCAM",
    PENDING_VERIFICATION: "PENDING_VERIFICATION",
    UNVERIFIED: "UNVERIFIED",
    // Legacy single verdicts
    "Confirmed Scam": "HIGH_RISK_SCAM",
    "Confirmed": "VERIFIED_TRUE",
    "Unconfirmed": "PENDING_VERIFICATION",
    "Disputed / False": "VERIFIED_FALSE",
    "No Coverage Found": "UNVERIFIED",
    // Legacy claim verdicts
    "True": "VERIFIED_TRUE",
    "False": "VERIFIED_FALSE",
    "Partly True": "PENDING_VERIFICATION",
    "Misleading": "PENDING_VERIFICATION",
    "Insufficient Evidence": "UNVERIFIED",
    // Legacy authenticity verdicts
    "Verified Official": "VERIFIED_TRUE",
    "Likely Legitimate": "VERIFIED_TRUE",
    "Suspicious": "HIGH_RISK_SCAM",
    "Likely Fraudulent": "HIGH_RISK_SCAM",
    "Confirmed Fraudulent": "HIGH_RISK_SCAM",
  };
  return map[verdict] ?? "UNVERIFIED";
}

// ---------------------------------------------------------------------------
// Verdict badge config
// ---------------------------------------------------------------------------

interface BadgeConfig {
  label: string;
  labelCy: string;        // Chichewa display label
  icon: string;
  badgeClass: string;
}

const CANONICAL_CONFIG: Record<CanonicalVerdict, BadgeConfig> = {
  VERIFIED_TRUE: {
    label: "Verified Authentic",
    labelCy: "Nkhani Yotsimikizika",
    icon: "✅",
    badgeClass:
      "bg-emerald-500/15 text-emerald-400 border-emerald-500/40 shadow-[0_0_16px_rgba(16,185,129,0.20)]",
  },
  VERIFIED_FALSE: {
    label: "Verified False",
    labelCy: "Uthenga Wawonzedwa",
    icon: "🚫",
    badgeClass:
      "bg-red-500/15 text-red-400 border-red-500/40 shadow-[0_0_16px_rgba(239,68,68,0.25)]",
  },
  HIGH_RISK_SCAM: {
    label: "High Risk Scam",
    labelCy: "Muchenjere: Chinyengo",
    icon: "🚨",
    badgeClass:
      "bg-purple-500/15 text-purple-300 border-purple-500/50 shadow-[0_0_18px_rgba(168,85,247,0.30)] animate-pulse",
  },
  PENDING_VERIFICATION: {
    label: "Pending Verification",
    labelCy: "Ikufufuzidwa",
    icon: "🕐",
    badgeClass:
      "bg-amber-500/15 text-amber-400 border-amber-500/40",
  },
  UNVERIFIED: {
    label: "Unverified",
    labelCy: "Sichinatsimikizidwe",
    icon: "❓",
    badgeClass:
      "bg-slate-500/10 text-slate-400 border-slate-500/30",
  },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface VerdictBadgeProps {
  verdict: AnyVerdict;
  /** @deprecated use `verdict` with a canonical label; verdictType is ignored for canonical labels */
  verdictType?: "claim" | "authenticity" | "legacy" | "canonical";
  size?: "sm" | "md" | "lg";
  /** Show Chichewa label instead of English */
  locale?: "en" | "ny";
}

export function VerdictBadge({
  verdict,
  size = "md",
  locale = "en",
}: VerdictBadgeProps) {
  const canonical = toCanonical(verdict);
  const config = CANONICAL_CONFIG[canonical];

  const sizeClasses = {
    sm: "px-2.5 py-0.5 text-xs gap-1.5 font-semibold",
    md: "px-3.5 py-1 text-sm gap-2 font-bold",
    lg: "px-5 py-2 text-base gap-2.5 font-extrabold tracking-wide",
  }[size];

  const label = locale === "ny" ? config.labelCy : config.label;

  return (
    <span
      className={`inline-flex items-center rounded-full border backdrop-blur-md transition-all duration-300 ${config.badgeClass} ${sizeClasses}`}
      data-verdict={canonical}
      role="status"
      aria-label={`Verdict: ${label}`}
    >
      <span className="text-base" aria-hidden="true">{config.icon}</span>
      <span>{label}</span>
    </span>
  );
}
