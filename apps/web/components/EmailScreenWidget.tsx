"use client";

import React, { useState } from "react";
import { Mail, AlertTriangle, ShieldCheck, ShieldAlert, CheckCircle2 } from "lucide-react";
import { verifyEmail } from "@/lib/api";

export function EmailScreenWidget() {
  const [sender, setSender] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [subject, setSubject] = useState("");
  const [bodyText, setBodyText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sender.trim() && !bodyText.trim()) return;

    setLoading(true);
    setResult(null);

    const res = await verifyEmail({
      sender_address: sender.trim(),
      display_name: displayName.trim() || undefined,
      subject: subject.trim() || undefined,
      body_text: bodyText.trim(),
    });

    setResult(res);
    setLoading(false);
  };

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-xl">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-xl bg-primary-500/15 border border-primary-500/30 flex items-center justify-center text-primary-500">
          <Mail className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-bold text-lg text-ink-950 dark:text-white">
            Email Phishing & Domain Spoof Inspector
          </h3>
          <p className="text-xs text-ink-500">
            Phase H: Detect sender domain mismatches, phishing lures, and malicious links.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-ink-700 dark:text-ink-300 mb-1">
              Sender Address *
            </label>
            <input
              type="email"
              required
              placeholder="e.g. security@paypal-verify.com"
              value={sender}
              onChange={(e) => setSender(e.target.value)}
              className="w-full px-3 py-2 rounded-xl text-xs bg-soft border border-border focus:ring-2 focus:ring-primary-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-ink-700 dark:text-ink-300 mb-1">
              Display Name (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. PayPal Customer Support"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full px-3 py-2 rounded-xl text-xs bg-soft border border-border focus:ring-2 focus:ring-primary-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-ink-700 dark:text-ink-300 mb-1">
            Subject Line
          </label>
          <input
            type="text"
            placeholder="e.g. Urgent: Account Action Required"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="w-full px-3 py-2 rounded-xl text-xs bg-soft border border-border focus:ring-2 focus:ring-primary-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-ink-700 dark:text-ink-300 mb-1">
            Email Body Text *
          </label>
          <textarea
            required
            rows={4}
            placeholder="Paste suspicious email text or links here..."
            value={bodyText}
            onChange={(e) => setBodyText(e.target.value)}
            className="w-full px-3 py-2 rounded-xl text-xs bg-soft border border-border focus:ring-2 focus:ring-primary-500 focus:outline-none resize-y"
          />
        </div>

        <button
          type="submit"
          disabled={loading || (!sender.trim() && !bodyText.trim())}
          className="w-full py-2.5 px-4 bg-primary-500 hover:bg-primary-600 disabled:opacity-50 text-white font-bold text-xs rounded-xl transition-all shadow-md flex items-center justify-center gap-2"
        >
          {loading ? (
            "Analyzing Email Signals..."
          ) : (
            <>
              <ShieldCheck className="w-4 h-4" /> Analyze Email Authenticity
            </>
          )}
        </button>
      </form>

      {result && (
        <div className="mt-6 pt-6 border-t border-border space-y-4">
          {/* Risk Level Badge */}
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-ink-500">
              Email Authenticity Result:
            </span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider flex items-center gap-1.5 ${
                result.risk_level === "High"
                  ? "bg-red-500/15 text-red-500 border border-red-500/30"
                  : result.risk_level === "Medium"
                  ? "bg-amber-500/15 text-amber-500 border border-amber-500/30"
                  : "bg-emerald-500/15 text-emerald-500 border border-emerald-500/30"
              }`}
            >
              {result.risk_level === "High" ? (
                <ShieldAlert className="w-3.5 h-3.5" />
              ) : result.risk_level === "Medium" ? (
                <AlertTriangle className="w-3.5 h-3.5" />
              ) : (
                <CheckCircle2 className="w-3.5 h-3.5" />
              )}
              {result.email_authenticity_verdict} ({result.risk_level} Risk)
            </span>
          </div>

          {/* Domain Spoofing Banner */}
          {result.domain_spoof_detected && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-xs font-medium flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
              <div>
                <strong>Domain Spoofing Detected!</strong> The display name claims to be a recognized institution, but the sender email domain does not match.
              </div>
            </div>
          )}

          {/* Detected Signals */}
          {result.detected_signals?.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-ink-950 dark:text-white mb-2">
                Detected Risk Signals:
              </h4>
              <ul className="space-y-1.5">
                {result.detected_signals.map((sig: string, idx: number) => (
                  <li
                    key={idx}
                    className="text-xs p-2 rounded-lg bg-soft border border-border text-ink-700 dark:text-ink-300 font-mono"
                  >
                    ⚠️ {sig}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommended Actions */}
          {result.recommended_actions?.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-ink-950 dark:text-white mb-2">
                Recommended Actions:
              </h4>
              <div className="space-y-1">
                {result.recommended_actions.map((act: string, idx: number) => (
                  <p key={idx} className="text-xs text-ink-600 dark:text-ink-400 flex items-center gap-1.5">
                    • {act}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
