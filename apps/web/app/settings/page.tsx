/**
 * VeriFeed Settings Page — Proactive Protection Controls
 *
 * Allows users to configure what VeriFeed monitors in their web session.
 * On web, "automatic protection" means monitoring content pasted or
 * shared into the session — NOT OS-level notification/SMS interception
 * (that is Android-only, Phase F).
 *
 * Privacy-first: all toggles default to opt-in. No data is sent to
 * VeriFeed without the user's active consent per interaction.
 */

import { Navbar } from "@/components/Navbar";
import {
  Shield,
  Smartphone,
  Bell,
  Lock,
  ChevronRight,
  Info,
  PhoneCall,
  Mail,
} from "lucide-react";

export const metadata = {
  title: "Protection Settings — VeriFeed",
  description:
    "Configure VeriFeed's proactive protection settings. Control what content is scanned and how you are alerted.",
};

interface SettingRowProps {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  status?: "active" | "coming-soon" | "off";
  badge?: string;
}

function SettingRow({
  id,
  icon,
  title,
  description,
  status = "off",
  badge,
}: SettingRowProps) {
  return (
    <div
      id={id}
      className="flex items-start gap-4 rounded-2xl border border-border bg-surface p-5 transition-all hover:border-primary-300/50 hover:shadow-sm"
    >
      <div className="shrink-0 flex h-10 w-10 items-center justify-center rounded-xl bg-soft border border-border">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <span className="text-sm font-bold text-foreground">{title}</span>
          {badge && (
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-amber-50 text-amber-700 border-amber-200">
              {badge}
            </span>
          )}
          {status === "active" && (
            <span className="flex items-center gap-1 text-[10px] font-bold text-primary-600">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary-500 animate-pulse" />
              Active
            </span>
          )}
          {status === "coming-soon" && (
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-soft text-ink-500 border-border">
              Coming Soon
            </span>
          )}
        </div>
        <p className="text-xs text-ink-500 leading-relaxed">{description}</p>
      </div>
    </div>
  );
}

function SectionHeading({
  title,
  subtitle,
}: {
  title: string;
  subtitle: string;
}) {
  return (
    <div className="mb-4">
      <h2 className="text-base font-extrabold uppercase tracking-wider text-ink-500 mb-0.5">
        {title}
      </h2>
      <p className="text-xs text-ink-500">{subtitle}</p>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar maxWidth="max-w-6xl" />

      <div className="max-w-6xl mx-auto px-4 pt-8">
        {/* Page header */}
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-primary-50 text-primary-600 border border-primary-200 mb-3">
            <Shield className="h-3.5 w-3.5" />
            <span>Proactive Protection</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-black text-foreground tracking-tight mb-3">
            Protection{" "}
            <span className="bg-linear-to-r from-primary-500 via-primary-600 to-primary-500 bg-clip-text text-transparent">
              Settings
            </span>
          </h1>
          <p className="text-sm md:text-base text-ink-500 max-w-xl">
            Control how VeriFeed protects you. All features are opt-in — you
            choose what VeriFeed can see and when.
          </p>
        </div>

        {/* Privacy notice */}
        <div className="mb-8 flex items-start gap-3 rounded-2xl border border-primary-200 bg-primary-50/50 p-4">
          <Info className="h-4 w-4 shrink-0 mt-0.5 text-primary-600" />
          <p className="text-xs text-ink-700 leading-relaxed">
            <strong className="text-ink-900">Privacy first:</strong> VeriFeed
            only processes content you explicitly share or paste. We never
            access your messages, notifications, or files without your active
            action. On web, scanning is session-only and not stored unless you
            initiate a full verification.
          </p>
        </div>

        <div className="space-y-10">
          {/* Web session protection */}
          <section id="settings-web-protection">
            <SectionHeading
              title="Web Session"
              subtitle="Protection features available in your browser session"
            />
            <div className="space-y-3">
              <SettingRow
                id="setting-quick-screen"
                icon={<Shield className="h-5 w-5 text-primary-600" />}
                title="Quick Screen Widget"
                description="Paste any suspicious message or URL into the Quick Screen widget on the Verify page for an instant Stage 1 risk assessment. No AI call — results in milliseconds."
                status="active"
              />
              <SettingRow
                id="setting-url-prefill"
                icon={<ChevronRight className="h-5 w-5 text-ink-500" />}
                title="Share → VeriFeed Pre-fill"
                description="Any content shared to VeriFeed via a URL parameter (?content=...) is automatically pre-filled into the verification form. Works from any source that can construct a link."
                status="active"
              />
            </div>
          </section>

          {/* Android protection */}
          <section id="settings-android">
            <SectionHeading
              title="Android Mobile Companion"
              subtitle="Native mobile protection features implemented in the VeriFeed Android app"
            />
            <div className="space-y-3">
              <SettingRow
                id="setting-android-manual"
                icon={<Smartphone className="h-5 w-5 text-primary-600" />}
                title="Manual Verification"
                description="Paste text, upload a screenshot, or share content from any Android app directly into VeriFeed for Stage 1 + Stage 2 verification."
                status="active"
                badge="Available on Android"
              />
              <SettingRow
                id="setting-android-notification"
                icon={<Bell className="h-5 w-5 text-primary-600" />}
                title="Notification Screening"
                description="VeriFeed screens incoming notifications from messaging apps for suspicious content. Requires explicit Notification Access permission in Android Settings — off by default."
                status="active"
                badge="Android · Policy gated"
              />
              <SettingRow
                id="setting-android-share"
                icon={<ChevronRight className="h-5 w-5 text-primary-600" />}
                title="Share Intent Receiver"
                description="Share any message, URL, or screenshot to VeriFeed from any Android app using the native system share sheet."
                status="active"
                badge="Available on Android"
              />
              <SettingRow
                id="setting-android-call"
                icon={<PhoneCall className="h-5 w-5 text-primary-600" />}
                title="Voice Call & Phishing Screening"
                description="Evaluates incoming call numbers and voice phishing indicators using the Android CallScreeningService."
                status="active"
                badge="Android · Call Screening"
              />
              <SettingRow
                id="setting-android-email"
                icon={<Mail className="h-5 w-5 text-primary-600" />}
                title="Email Header & Domain Screener"
                description="Analyzes raw email content and headers for SPF/DKIM/DMARC status, domain spoofing, and phishing lures."
                status="active"
                badge="Android · Email Screener"
              />
            </div>
          </section>

          {/* Privacy controls */}
          <section id="settings-privacy">
            <SectionHeading
              title="Privacy & Data"
              subtitle="What VeriFeed does and does not do with your content"
            />
            <div className="rounded-2xl border border-border bg-surface p-5 space-y-4">
              <div className="flex items-start gap-3">
                <Lock className="h-4 w-4 shrink-0 mt-0.5 text-primary-600" />
                <div>
                  <p className="text-sm font-semibold text-foreground mb-1">
                    What VeriFeed never does
                  </p>
                  <ul className="text-xs text-ink-500 leading-relaxed space-y-1 list-none">
                    {[
                      "Access your messages, emails, or notifications without your action",
                      "Store screening results unless you initiate a full verification",
                      "Share your content with third parties",
                      "Access your contact list or address book",
                      "Request permissions before they are needed for an active feature",
                    ].map((item, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-primary-500 mt-0.5 shrink-0">
                          ✓
                        </span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="border-t border-border pt-4 flex items-start gap-3">
                <Info className="h-4 w-4 shrink-0 mt-0.5 text-ink-500" />
                <p className="text-xs text-ink-500 leading-relaxed">
                  Stage 1 screening (Quick Screen) runs entirely on the VeriFeed
                  server with no third-party calls. Stage 2 verification uses
                  Google Gemini for evidence synthesis. No content is retained
                  after your session ends unless you submit it for community
                  fraud tracking.
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
