import type { Metadata } from "next";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Shield, Lock, FileText, Trash2, Eye, Server, RefreshCw, Mail, CheckCircle2 } from "lucide-react";

export const metadata: Metadata = {
  title: "Privacy Policy — VeriFeed",
  description: "VeriFeed Privacy Policy and Data Handling Disclosures, including Meta Platform Data Usage & User Data Deletion Instructions.",
};

export default function PrivacyPolicyPage() {
  const lastUpdated = "October 3, 2026";

  return (
    <div className="min-h-screen flex flex-col pb-16">
      <Navbar />

      <main className="flex-1 max-w-4xl mx-auto w-full px-4 pt-10">
        {/* Header Hero */}
        <header className="mb-10 text-center md:text-left bg-gradient-to-br from-white via-primary-50/30 to-white p-8 md:p-10 rounded-3xl border border-border shadow-sm">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-100 text-primary-700 text-xs font-bold mb-4">
            <Shield className="w-3.5 h-3.5" />
            <span>Transparency & Privacy Standard</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-black text-ink-950 tracking-tight mb-3">
            VeriFeed Privacy Policy
          </h1>
          <p className="text-sm text-ink-700 max-w-2xl leading-relaxed">
            VeriFeed is committed to protecting user privacy, maintaining transparency, and handling data ethically across our AI verification engine, mobile protection apps, and social feed integrations.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-4 text-xs text-ink-500 pt-4 border-t border-border/60">
            <span><strong>Effective Date:</strong> {lastUpdated}</span>
            <span>•</span>
            <span><strong>Version:</strong> 2.4.0</span>
            <span>•</span>
            <span className="text-primary-600 font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-primary-500" />
              Meta Platform Compliant
            </span>
          </div>
        </header>

        {/* Highlight Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
          <div className="p-5 rounded-2xl bg-white border border-border flex flex-col gap-2">
            <Lock className="w-5 h-5 text-primary-600" />
            <h3 className="text-sm font-bold text-ink-950">Privacy First</h3>
            <p className="text-xs text-ink-700">
              On-device screening and opt-in telemetry. We never monetize, sell, or rent personal user data.
            </p>
          </div>
          <div className="p-5 rounded-2xl bg-white border border-border flex flex-col gap-2">
            <Server className="w-5 h-5 text-indigo-600" />
            <h3 className="text-sm font-bold text-ink-950">Strict Scope</h3>
            <p className="text-xs text-ink-700">
              Social webhooks ingest public posts strictly for institutional fraud detection and fact verification.
            </p>
          </div>
          <div className="p-5 rounded-2xl bg-white border border-border flex flex-col gap-2">
            <Trash2 className="w-5 h-5 text-red-600" />
            <h3 className="text-sm font-bold text-ink-950">Data Control</h3>
            <p className="text-xs text-ink-700">
              Full control to request deletion of cached submissions or revoke social platform permissions anytime.
            </p>
          </div>
        </div>

        {/* Main Body Document */}
        <div className="bg-white border border-border rounded-3xl p-6 md:p-10 shadow-xs space-y-10 text-ink-800 text-sm leading-relaxed">
          
          {/* Section 1 */}
          <section id="section-1" className="space-y-3">
            <h2 className="text-xl font-bold text-ink-950 flex items-center gap-2 border-b border-border/80 pb-2">
              <Eye className="w-5 h-5 text-primary-600" />
              1. Overview & Scope
            </h2>
            <p>
              VeriFeed (&quot;we&quot;, &quot;our&quot;, or &quot;us&quot;) operates the VeriFeed claim verification platform, including our web portal, API services, mobile protection applications (Android), and connected social media integrations (including Meta/Facebook Graph API, Webhooks, and WhatsApp Business API).
            </p>
            <p>
              This policy explains what information is collected when you interact with our platform, how that information is used, how data from third-party platforms (like Meta) is handled, and your rights regarding data access and deletion.
            </p>
          </section>

          {/* Section 2 */}
          <section id="section-2" className="space-y-3">
            <h2 className="text-xl font-bold text-ink-950 flex items-center gap-2 border-b border-border/80 pb-2">
              <FileText className="w-5 h-5 text-primary-600" />
              2. Information We Collect
            </h2>
            <div className="space-y-4">
              <div className="bg-soft/60 p-4 rounded-xl border border-border/60">
                <h4 className="font-bold text-ink-950 text-sm mb-1">A. Public Social Media & Webhook Data</h4>
                <p className="text-xs text-ink-700">
                  When Facebook Pages or social channels publish public posts, Meta webhooks deliver event payloads (such as post text, timestamps, and permalinks) to our secure ingest endpoint. We collect this public data solely to classify and index public health alerts, banking notices, and fraud warnings.
                </p>
              </div>

              <div className="bg-soft/60 p-4 rounded-xl border border-border/60">
                <h4 className="font-bold text-ink-950 text-sm mb-1">B. User-Submitted Claim Data</h4>
                <p className="text-xs text-ink-700">
                  When you submit a text query, headline, image, or email header for fact-checking via our AI agent or Email Inspector, we process the content to search public registries, extract evidence, and output a ground-checked verdict.
                </p>
              </div>

              <div className="bg-soft/60 p-4 rounded-xl border border-border/60">
                <h4 className="font-bold text-ink-950 text-sm mb-1">C. Mobile Telemetry & On-Device Screening</h4>
                <p className="text-xs text-ink-700">
                  Our Android caller & notification protection service processes incoming phone numbers and message headers locally on your device. Call logs and message texts are <strong>never transmitted</strong> to remote servers unless an explicit user action triggers a remote verification lookup.
                </p>
              </div>
            </div>
          </section>

          {/* Section 3 */}
          <section id="section-3" className="space-y-3">
            <h2 className="text-xl font-bold text-ink-950 flex items-center gap-2 border-b border-border/80 pb-2">
              <Server className="w-5 h-5 text-primary-600" />
              3. Meta (Facebook & Instagram) Platform Data Policy
            </h2>
            <p>
              VeriFeed adheres strictly to the <strong>Meta Platform Terms</strong> and <strong>Developer Policies</strong>:
            </p>
            <ul className="list-disc pl-5 space-y-2 text-xs md:text-sm text-ink-700">
              <li>
                <strong>Purpose Limit:</strong> Data received via Facebook Webhooks or Graph API is used exclusively to display institutional announcements, verify public claims, and alert users to fraudulent impersonations.
              </li>
              <li>
                <strong>No Data Sales or Advertising:</strong> We do not sell, license, or monetize Meta user or Page data, nor do we pass platform data to ad networks, data brokers, or intelligence providers.
              </li>
              <li>
                <strong>Signature Validation:</strong> All incoming Meta webhook payloads are cryptographically validated using <code className="bg-soft px-1.5 py-0.5 rounded text-xs">X-Hub-Signature-256</code> HMAC matching our registered Meta App Secret.
              </li>
              <li>
                <strong>Data Minimization:</strong> Non-qualifying social feed items (posts determined by our AI classifiers not to contain fraud alerts or institutional notices) are immediately discarded and not stored in persistent databases.
              </li>
            </ul>
          </section>

          {/* Section 4 - DATA DELETION INSTRUCTIONS FOR META COMPLIANCE */}
          <section id="data-deletion" className="space-y-4 bg-primary-50/40 p-6 rounded-2xl border border-primary-200">
            <h2 className="text-xl font-bold text-primary-900 flex items-center gap-2">
              <Trash2 className="w-5 h-5 text-primary-600" />
              4. User Data Deletion Instructions (Meta Platform Access)
            </h2>
            <p className="text-xs md:text-sm text-ink-800">
              In accordance with Meta Developer Policies, users have the right to request the deletion of any data associated with their Facebook account or pages accessed by VeriFeed.
            </p>

            <div className="space-y-3 bg-white p-4 rounded-xl border border-primary-100 text-xs">
              <h4 className="font-bold text-ink-950 text-sm">Option 1: Remove VeriFeed App via Facebook Account Settings</h4>
              <ol className="list-decimal pl-5 space-y-1.5 text-ink-700">
                <li>Log in to your Facebook account and navigate to <strong>Settings & Privacy &gt; Settings</strong>.</li>
                <li>In the left sidebar, click <strong>Apps and Websites</strong>.</li>
                <li>Find <strong>VeriFeed</strong> in the list of active apps and click <strong>Remove</strong>.</li>
                <li>Confirming removal automatically revokes all permissions and prevents further webhook notifications for your account/pages.</li>
              </ol>
            </div>

            <div className="space-y-3 bg-white p-4 rounded-xl border border-primary-100 text-xs">
              <h4 className="font-bold text-ink-950 text-sm">Option 2: Direct Data Deletion Request</h4>
              <p className="text-ink-700">
                If you wish to purge all stored records, alert queries, or cached page data linked to your identity or institution from VeriFeed databases, send an email to:
              </p>
              <div className="flex items-center gap-2 font-mono font-bold text-primary-700 bg-primary-50 p-3 rounded-lg border border-primary-200">
                <Mail className="w-4 h-4 text-primary-600" />
                <span>privacy@verifeed.org</span>
              </div>
              <p className="text-ink-600 text-[11px]">
                Please state <em>&quot;Meta Data Deletion Request&quot;</em> in the subject line along with your Facebook Page ID or user handle. All related records will be purged within 48 hours of verification.
              </p>
            </div>
          </section>

          {/* Section 5 */}
          <section id="section-5" className="space-y-3">
            <h2 className="text-xl font-bold text-ink-950 flex items-center gap-2 border-b border-border/80 pb-2">
              <Lock className="w-5 h-5 text-primary-600" />
              5. Data Security & Retention
            </h2>
            <p>
              We implement industry-standard security measures, including end-to-end TLS encryption in transit, strict API authentication, and parameterized SQL query protection. Database backups are encrypted at rest using AES-256 standards.
            </p>
          </section>

          {/* Section 6 */}
          <section id="section-6" className="space-y-3">
            <h2 className="text-xl font-bold text-ink-950 flex items-center gap-2 border-b border-border/80 pb-2">
              <RefreshCw className="w-5 h-5 text-primary-600" />
              6. Updates to This Policy
            </h2>
            <p>
              We may update this Privacy Policy periodically to reflect changes in regulatory standards or platform integrations. Any updates will be published on this page with an updated revision date.
            </p>
          </section>

          {/* Section 7 */}
          <section id="section-7" className="space-y-3 border-t border-border/80 pt-6">
            <h2 className="text-lg font-bold text-ink-950">Contact Us</h2>
            <p className="text-xs text-ink-700">
              If you have any questions, concerns, or requests regarding this Privacy Policy or our data handling practices, contact our privacy team at:
            </p>
            <div className="text-xs text-ink-900 font-medium space-y-1">
              <p><strong>VeriFeed Technology & Security Team</strong></p>
              <p>Email: <a href="mailto:privacy@verifeed.org" className="text-primary-600 hover:underline">privacy@verifeed.org</a></p>
              <p>Location: Mzuzu, Malawi</p>
            </div>
          </section>

        </div>

        {/* Navigation back */}
        <div className="mt-8 text-center">
          <Link href="/" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-soft hover:bg-border text-ink-800 text-xs font-bold transition-all">
            ← Return to VeriFeed Home
          </Link>
        </div>
      </main>
    </div>
  );
}
