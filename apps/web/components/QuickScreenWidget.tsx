"use client";

/**
 * QuickScreenWidget — Stage 1 instant content screening.
 *
 * Allows users to paste a message, URL, or suspicious text and get
 * an immediate risk assessment (Stage 1) without a full Gemini call.
 *
 * Flow:
 *   User pastes content → Stage 1 screen() → Risk badge shown instantly
 *   If needs_deep_verify → ProtectionAlert + "Verify with VeriFeed" CTA
 *
 * The component never shows a final "Confirmed Scam" verdict — that
 * requires Stage 2 (the full evidence pipeline via /api/v1/verify).
 */

import { useState, useTransition } from "react";
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  Loader2,
  Zap,
  ArrowRight,
} from "lucide-react";
import { screenContent, type ScreeningResult } from "@/lib/api";
import { ProtectionAlert } from "./ProtectionAlert";

const RISK_CONFIG = {
  Low: {
    icon: ShieldCheck,
    iconColor: "text-primary-400",
    bg: "bg-primary-500/10 border-primary-500/30",
    label: "Low Risk",
    labelColor: "text-primary-400",
    description: "No obvious scam signals detected.",
  },
  Medium: {
    icon: ShieldAlert,
    iconColor: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/30",
    label: "Suspicious",
    labelColor: "text-amber-400",
    description: "Some signals detected — verify before acting.",
  },
  High: {
    icon: ShieldAlert,
    iconColor: "text-red-400",
    bg: "bg-red-500/10 border-red-500/30",
    label: "High Risk",
    labelColor: "text-red-400",
    description: "Multiple risk signals — do not act without verifying.",
  },
} as const;

const PLACEHOLDER_EXAMPLES = [
  "Congratulations! You have won MK500,000. Click http://bit.ly/claim-prize to redeem.",
  "URGENT: Standard Bank has suspended your account. Verify now at http://stdbank-mw.net",
  "Airtel Money: Send MK5,000 processing fee to activate your loan.",
];

export function QuickScreenWidget() {
  const [content, setContent] = useState("");
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [alertDismissed, setAlertDismissed] = useState(false);
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState("");

  const handleScreen = () => {
    if (!content.trim()) return;
    setResult(null);
    setAlertDismissed(false);
    setError("");

    startTransition(async () => {
      const res = await screenContent(content.trim());
      if (res) {
        setResult(res);
      } else {
        setError(
          "Could not connect to screening service. Check your connection and try again.",
        );
      }
    });
  };

  const handleClear = () => {
    setContent("");
    setResult(null);
    setAlertDismissed(false);
    setError("");
  };

  const handleExampleClick = (example: string) => {
    setContent(example);
    setResult(null);
    setAlertDismissed(false);
    setError("");
  };

  const riskCfg = result ? RISK_CONFIG[result.risk_level] : null;

  return (
    <div
      id="quick-screen-widget"
      className="relative w-full overflow-hidden rounded-3xl border border-border bg-surface shadow-xl"
    >
      {/* Subtle glow */}
      <div className="pointer-events-none absolute -top-20 -right-20 h-56 w-56 rounded-full bg-primary-500/6 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 -left-20 h-56 w-56 rounded-full bg-amber-500/4 blur-3xl" />

      <div className="relative p-6 md:p-7">
        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-linear-to-tr from-amber-500 to-orange-500 shadow-lg shadow-amber-500/30">
            <Zap className="h-5 w-5 text-white" />
          </span>
          <div>
            <h2 className="text-base md:text-lg font-bold text-foreground tracking-tight">
              Quick Screen
            </h2>
            <p className="text-xs text-ink-500">
              Instant Stage 1 scan — no AI, results in milliseconds
            </p>
          </div>
        </div>

        {/* Text area */}
        <div className="relative mb-3">
          <textarea
            id="quick-screen-input"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleScreen();
            }}
            placeholder="Paste a suspicious message, SMS, or URL here…"
            rows={4}
            disabled={isPending}
            className="w-full resize-none rounded-2xl border border-border bg-background p-4 text-sm text-ink-900 placeholder-ink-500 shadow-inner focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-400/20 transition-all disabled:opacity-60"
          />
          <span className="absolute bottom-3 right-3 text-[10px] text-ink-500 select-none">
            ⌘↵ to scan
          </span>
        </div>

        {/* Example prompts */}
        {!content && (
          <div className="mb-4">
            <p className="text-[11px] font-semibold text-ink-500 mb-1.5">
              Try an example:
            </p>
            <div className="flex flex-col gap-1.5">
              {PLACEHOLDER_EXAMPLES.map((ex, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleExampleClick(ex)}
                  className="text-left text-[11px] text-ink-500 hover:text-ink-900 rounded-lg px-3 py-1.5 border border-dashed border-border hover:border-amber-400/50 hover:bg-amber-50/5 transition-all line-clamp-1"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-3 text-xs font-semibold text-red-500 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
            {error}
          </div>
        )}

        {/* Action row */}
        <div className="flex items-center gap-2 mb-5">
          <button
            id="quick-screen-submit"
            type="button"
            onClick={handleScreen}
            disabled={isPending || !content.trim()}
            className="inline-flex items-center gap-2 rounded-xl bg-linear-to-r from-amber-500 to-orange-500 px-5 py-2.5 text-sm font-bold text-white shadow-lg shadow-amber-500/25 hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-amber-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
          >
            {isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Scanning…</span>
              </>
            ) : (
              <>
                <Shield className="h-4 w-4" />
                <span>Screen Content</span>
              </>
            )}
          </button>

          {(content || result) && (
            <button
              id="quick-screen-clear"
              type="button"
              onClick={handleClear}
              className="text-xs text-ink-500 hover:text-ink-900 transition-colors px-2"
            >
              Clear
            </button>
          )}

          <span className="ml-auto text-[10px] text-ink-500 italic">
            Stage 1 only — no final verdict
          </span>
        </div>

        {/* Result */}
        {result && riskCfg && (
          <div className="space-y-3 animate-in fade-in slide-in-from-bottom-1 duration-300">
            {/* Risk badge row */}
            <div
              className={`flex items-center gap-3 rounded-xl border p-3 ${riskCfg.bg}`}
            >
              <riskCfg.icon
                className={`h-5 w-5 shrink-0 ${riskCfg.iconColor}`}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span
                    className={`text-sm font-extrabold ${riskCfg.labelColor}`}
                  >
                    {riskCfg.label}
                  </span>
                  <span className="text-[10px] text-ink-500">
                    {result.signals.length} signal
                    {result.signals.length !== 1 ? "s" : ""}
                  </span>
                </div>
                <p className="text-xs text-ink-500">{riskCfg.description}</p>
              </div>

              {result.needs_deep_verify && (
                <a
                  id="quick-screen-verify-cta"
                  href={`/verify?content=${encodeURIComponent(content)}`}
                  className="shrink-0 inline-flex items-center gap-1 rounded-lg bg-white/90 px-3 py-1.5 text-xs font-bold text-gray-900 shadow hover:brightness-105 transition-all"
                >
                  Verify
                  <ArrowRight className="h-3 w-3" />
                </a>
              )}
            </div>

            {/* Signal chips */}
            {result.signals.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {result.signals.map((signal, i) => (
                  <span
                    key={i}
                    title={signal.description}
                    className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${
                      signal.severity === "high"
                        ? "border-red-500/40 bg-red-500/10 text-red-600"
                        : signal.severity === "medium"
                          ? "border-amber-500/40 bg-amber-500/10 text-amber-600"
                          : "border-border bg-soft text-ink-700"
                    }`}
                  >
                    {signal.signal_type.replace(/_/g, " ")}
                    {signal.matched_text && (
                      <span className="opacity-60 max-w-20 truncate">
                        — {signal.matched_text}
                      </span>
                    )}
                  </span>
                ))}
              </div>
            )}

            {/* Full protection alert for High risk */}
            {result.risk_level === "High" && !alertDismissed && (
              <ProtectionAlert
                result={result}
                content={content}
                onDismiss={() => setAlertDismissed(true)}
              />
            )}

            {/* Low risk positive feedback */}
            {result.risk_level === "Low" && (
              <p className="text-[11px] text-primary-600 font-medium">
                ✓ No obvious scam signals. You can still{" "}
                <a
                  href={`/verify?content=${encodeURIComponent(content)}`}
                  className="underline hover:text-primary-700"
                >
                  verify with VeriFeed
                </a>{" "}
                for full evidence-backed confirmation.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
