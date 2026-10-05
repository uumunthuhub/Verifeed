import type { Metadata } from "next";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Shield, Trash2, Mail, CheckCircle2, ArrowLeft } from "lucide-react";

export const metadata: Metadata = {
  title: "User Data Deletion Instructions — VeriFeed",
  description: "Instructions on how users can request data deletion or remove VeriFeed Facebook/Messenger integration.",
};

export default function DataDeletionPage() {
  return (
    <div className="min-h-screen flex flex-col pb-16 bg-background">
      <Navbar />

      <main className="flex-1 max-w-3xl mx-auto w-full px-4 pt-10">
        <header className="mb-8 text-center bg-white p-8 md:p-10 rounded-3xl border border-border shadow-xs">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-100 text-red-700 text-xs font-bold mb-4">
            <Trash2 className="w-3.5 h-3.5" />
            <span>Meta Platform Compliance</span>
          </div>
          <h1 className="text-3xl font-black text-ink-950 tracking-tight mb-3">
            User Data Deletion Instructions
          </h1>
          <p className="text-sm text-ink-700 max-w-xl mx-auto leading-relaxed">
            VeriFeed respects your privacy rights. If you interact with VeriFeed through Facebook Messenger or connected Page integrations, here is how you can delete your data.
          </p>
        </header>

        <div className="bg-white border border-border rounded-3xl p-6 md:p-10 shadow-xs space-y-8 text-ink-800 text-sm leading-relaxed">
          
          <section className="space-y-4">
            <h2 className="text-lg font-bold text-ink-950 flex items-center gap-2 border-b border-border pb-2">
              <Shield className="w-5 h-5 text-primary-600" />
              1. Remove VeriFeed Integration via Facebook Settings
            </h2>
            <p className="text-xs text-ink-700">
              To immediately stop VeriFeed from receiving any future events or messages from your Facebook account:
            </p>
            <ol className="list-decimal pl-5 space-y-2 text-xs text-ink-800 font-medium">
              <li>Log in to your Facebook Account and go to <strong>Settings & Privacy &gt; Settings</strong>.</li>
              <li>In the left sidebar, click <strong>Apps and Websites</strong>.</li>
              <li>Locate <strong>VeriFeed</strong> in the list of connected apps.</li>
              <li>Click <strong>Remove</strong> to revoke all platform permissions and disconnect the app.</li>
            </ol>
          </section>

          <section className="space-y-4">
            <h2 className="text-lg font-bold text-ink-950 flex items-center gap-2 border-b border-border pb-2">
              <Trash2 className="w-5 h-5 text-red-600" />
              2. Direct Data Deletion Request (Purge Stored Logs)
            </h2>
            <p className="text-xs text-ink-700">
              If you want all cached conversation logs, query submissions, or Facebook Page alert records associated with your account permanently deleted from VeriFeed databases:
            </p>
            
            <div className="bg-soft p-4 rounded-2xl border border-border/80 space-y-3">
              <div className="flex items-center gap-2 font-mono font-bold text-primary-700 bg-white p-3 rounded-xl border border-primary-200">
                <Mail className="w-4 h-4 text-primary-600" />
                <span>privacy@verifeed.org</span>
              </div>
              <p className="text-xs text-ink-700">
                Send an email with the subject line <strong>&quot;Meta Data Deletion Request&quot;</strong> and include your Facebook User ID or Page ID.
              </p>
            </div>
          </section>

          <section className="space-y-3 bg-green-50/50 p-5 rounded-2xl border border-green-200">
            <h3 className="font-bold text-green-900 text-sm flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-600" />
              Data Processing Guarantee
            </h3>
            <p className="text-xs text-green-800">
              All deletion requests are verified and executed within <strong>48 hours</strong>. Upon completion, a confirmation code and deletion log hash will be sent to your email.
            </p>
          </section>

        </div>

        <div className="mt-8 text-center">
          <Link href="/privacy" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white hover:bg-soft text-ink-800 text-xs font-bold border border-border transition-all">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Privacy Policy</span>
          </Link>
        </div>
      </main>
    </div>
  );
}
