"use client";

/**
 * ProtectionAlert — Stage 1 risk notification banner.
 *
 * Displayed when local screening returns a Medium or High risk_level.
 * Surfaces the top signal (urgency, suspicious URL, monetary request, etc.)
 * and provides two actions: Dismiss or Verify with VeriFeed (Stage 2).
 *
 * Architecture: This is a display component only. It does NOT produce
 * a verdict. The "SUSPICIOUS" label here reflects Stage 1 signal detection,
 * not confirmed fraud. Confirmed verdicts require Stage 2 evidence pipeline.
 */

import { useState } from "react";
import {
  AlertTriangle,
  ShieldAlert,
  X,
  ArrowRight,
  ExternalLink,
} from "lucide-react";
import type { ScreeningResult } from "@/lib/api";

interface ProtectionAlertProps {
  result: ScreeningResult;
  /** Original content that was screened — passed to verify page if user escalates */
  content: string;
  onDismiss: () => void;
}

const SEVERITY_CONFIG = {
  High: {
    border: "border-red-400/60",
    bg: "bg-red-950/80",
    iconBg: "bg-red-500/20",
    iconColor: "text-red-400",
    badge: "bg-red-500/20 text-red-300 border-red-500/40",
    label: "HIGH RISK",
    Icon: ShieldAlert,
  },
  Medium: {
    border: "border-amber-400/50",
    bg: "bg-amber-950/70",
    iconBg: "bg-amber-500/20",
    iconColor: "text-amber-400",
    badge: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    label: "SUSPICIOUS",
    Icon: AlertTriangle,
  },
  Low: {
    border: "border-primary-400/40",
    bg: "bg-primary-950/60",
    iconBg: "bg-primary-500/20",
    iconColor: "text-primary-400",
    badge: "bg-primary-500/20 text-primary-300 border-primary-500/40",
    label: "LOW RISK",
    Icon: AlertTriangle,
  },
} as const;

const SIGNAL_LABELS: Record<string, string> = {
  urgency_language: "Urgency language",
  suspicious_url: "Suspicious URL",
  monetary_request: "Money transfer request",
  unsolicited_prize: "Unsolicited prize claim",
  suspicious_sender: "Suspicious sender",
  impersonation_keyword: "Possible impersonation",
  institution_mention: "Institution name detected",
};

export function ProtectionAlert({
  result,
  content,
  onDismiss,
}: ProtectionAlertProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  const cfg = SEVERITY_CONFIG[result.risk_level] ?? SEVERITY_CONFIG.Medium;
  const { Icon } = cfg;

  // Top signals to display (cap at 3)
  const topSignals = result.signals.slice(0, 3);

  const handleDismiss = () => {
    setDismissed(true);
    onDismiss();
  };

  const handleVerify = () => {
    const encoded = encodeURIComponent(content);
    window.open(`/verify?content=${encoded}`, "_self");
  };

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`
        relative w-full rounded-2xl border backdrop-blur-xl
        ${cfg.border} ${cfg.bg}
        p-4 md:p-5 shadow-2xl
        animate-in slide-in-from-top-2 fade-in duration-300
      `}
    >
      {/* Dismiss button */}
      <button
        id="protection-alert-dismiss"
        type="button"
        onClick={handleDismiss}
        aria-label="Dismiss alert"
        className="absolute right-3 top-3 rounded-full p-1.5 text-white/50 hover:bg-white/10 hover:text-white transition-colors"
      >
        <X className="h-4 w-4" />
      </button>

      <div className="flex items-start gap-4 pr-8">
        {/* Icon */}
        <div
          className={`shrink-0 flex h-10 w-10 items-center justify-center rounded-xl ${cfg.iconBg}`}
        >
          <Icon className={`h-5 w-5 ${cfg.iconColor}`} />
        </div>

        <div className="flex-1 min-w-0">
          {/* Header row */}
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full border ${cfg.badge}`}
            >
              {cfg.label}
            </span>
            <span className="text-xs text-white/50">
              {result.signals.length} signal
              {result.signals.length !== 1 ? "s" : ""} detected
            </span>
          </div>

          {/* Headline */}
          <p className="text-sm font-bold text-white mb-2">
            ⚠️ Suspicious content detected before you act
          </p>

          {/* Signal chips */}
          {topSignals.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {topSignals.map((signal, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 rounded-full border border-white/20 bg-white/10 px-2.5 py-0.5 text-[11px] font-semibold text-white/80"
                >
                  {SIGNAL_LABELS[signal.signal_type] ?? signal.signal_type}
                </span>
              ))}
            </div>
          )}

          {/* Recommended action */}
          <p className="text-xs text-white/60 mb-3 leading-relaxed">
            {result.recommended_action}
          </p>

          {/* Detected institutions */}
          {result.detected_institutions.length > 0 && (
            <p className="text-[11px] text-white/50 mb-3">
              <span className="font-semibold text-white/70">Detected: </span>
              {result.detected_institutions.join(", ")}
            </p>
          )}

          {/* Action note */}
          <p className="text-[10px] text-white/35 mb-3 italic">
            This is a Stage 1 signal scan only — not a final verdict.
            Verification uses evidence + AI.
          </p>

          {/* CTA row */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              id="protection-alert-verify"
              type="button"
              onClick={handleVerify}
              className="inline-flex items-center gap-1.5 rounded-xl bg-white px-4 py-2 text-xs font-bold text-gray-900 shadow-lg hover:brightness-105 active:scale-95 transition-all"
            >
              Verify with VeriFeed
              <ArrowRight className="h-3.5 w-3.5" />
            </button>

            {result.screened_urls.length > 0 && (
              <span className="inline-flex items-center gap-1 text-[11px] text-white/40">
                <ExternalLink className="h-3 w-3" />
                {result.screened_urls.length} URL
                {result.screened_urls.length !== 1 ? "s" : ""} flagged
              </span>
            )}

            <button
              id="protection-alert-dismiss-text"
              type="button"
              onClick={handleDismiss}
              className="text-[11px] text-white/40 hover:text-white/60 transition-colors underline-offset-2 hover:underline"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
