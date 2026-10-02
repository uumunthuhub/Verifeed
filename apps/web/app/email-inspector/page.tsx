import { Navbar } from "@/components/Navbar";
import { EmailScreenWidget } from "@/components/EmailScreenWidget";

export const metadata = {
  title: "Email Phishing Inspector — VeriFeed",
  description: "Detect sender domain mismatches, phishing lures, and malicious links in emails.",
};

export default function EmailInspectorPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar maxWidth="max-w-6xl" />
      <div className="max-w-6xl mx-auto px-4 pt-8 pb-12">
        <div className="mb-6 text-center max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-primary-50 text-primary-600 border border-primary-200 mb-3">
            <span>🛡️ Domain Authentication</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-black text-foreground tracking-tight mb-3">
            Email & Phishing{" "}
            <span className="bg-linear-to-r from-primary-500 via-primary-600 to-primary-500 bg-clip-text text-transparent">
              Inspector
            </span>
          </h1>
          <p className="text-sm md:text-base text-gray-600">
            Paste suspicious emails below to check sender authenticity and detect potential phishing attempts or malicious links.
          </p>
        </div>
        
        <EmailScreenWidget />
      </div>
    </div>
  );
}
