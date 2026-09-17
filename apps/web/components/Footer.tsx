import Link from "next/link";

export function Footer({ maxWidth = "max-w-6xl" }: { maxWidth?: string }) {
  return (
    <footer className="w-full mt-20 pt-12 pb-10 border-t border-border bg-white/80 backdrop-blur-xl text-gray-600">
      <div className={`mx-auto ${maxWidth} px-4 md:px-6`}>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
          {/* Brand & Description */}
          <div className="md:col-span-1 flex flex-col gap-4">
            <Link href="/" className="vf-logo" aria-label="VeriFeed home">
              <div
                className="w-9 h-9 rounded-xl bg-white border border-primary-200 shadow-md shadow-primary-500/10 flex items-center justify-center p-0.5 overflow-hidden shrink-0"
                aria-hidden="true"
              >
                <img src="/verifeed-bot.png" alt="VeriFeed Logo" className="h-full w-full object-contain" />
              </div>
              <span className="vf-logo-text font-black text-xl text-primary-600">
                VeriFeed
              </span>
            </Link>

            <p className="text-xs text-gray-600 leading-relaxed">
              VeriFeed clusters headlines from legitimate news agencies and
              AI-verifies claims against retrieved news coverage and official
              fraud disclaimers.
            </p>

            <div className="flex items-center gap-2 text-xs text-primary-500 font-semibold">
              <span className="flex h-2 w-2 rounded-full bg-primary-500 animate-ping" />
              <span>Real-Time Indexing Active</span>
            </div>
          </div>

          {/* Quick Links */}
          <div className="flex flex-col gap-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-ink-900">
              Platform Features
            </h4>
            <ul className="flex flex-col gap-2.5 text-xs">
              <li>
                <Link
                  href="/"
                  className="hover:text-primary-600 transition-colors"
                >
                  📰 Live Headline Feed
                </Link>
              </li>
              <li>
                <Link
                  href="/verify"
                  className="hover:text-primary-600 transition-colors"
                >
                  🔍 AI Claim Lab (&ldquo;Ask-the-Agent&rdquo;)
                </Link>
              </li>
              <li>
                <Link
                  href="/scams"
                  className="hover:text-primary-600 transition-colors"
                >
                  🛑 Institutional Fraud Alerts
                </Link>
              </li>
            </ul>
          </div>

          {/* Categories */}
          <div className="flex flex-col gap-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-ink-900">
              News Categories
            </h4>
            <ul className="grid grid-cols-2 gap-3 text-xs">
              <li>
                <Link
                  href="/?category=Politics"
                  className="hover:text-primary-600 transition-colors"
                >
                  Politics
                </Link>
              </li>
              <li>
                <Link
                  href="/?category=Business"
                  className="hover:text-primary-600 transition-colors"
                >
                  Business
                </Link>
              </li>
              <li>
                <Link
                  href="/?category=Health"
                  className="hover:text-primary-600 transition-colors"
                >
                  Health
                </Link>
              </li>
              <li>
                <Link
                  href="/?category=Technology"
                  className="hover:text-primary-600 transition-colors"
                >
                  Technology
                </Link>
              </li>
              <li>
                <Link
                  href="/?category=World"
                  className="hover:text-primary-600 transition-colors"
                >
                  World
                </Link>
              </li>
              <li>
                <Link
                  href="/?category=Regional"
                  className="hover:text-primary-600 transition-colors"
                >
                  Regional
                </Link>
              </li>
            </ul>
          </div>

          {/* Transparency & Integrity Statement */}
          <div className="flex flex-col gap-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-ink-900">
              Verification Standards
            </h4>
            <p className="text-xs text-ink-700 leading-relaxed bg-soft p-4 rounded-xl border border-border">
              VeriFeed never asserts truth from LLM judgment alone. Every
              verdict is strictly grounded in retrieved, citable evidence from
              indexed outlets & official institutional registries.
            </p>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="flex flex-col md:flex-row items-center justify-between pt-8 border-t border-border text-xs text-ink-500 gap-4">
          <p>
            © {new Date().getFullYear()} VeriFeed. Made with ❤️ from Mzuzu,
            Malawi. Powered by Gemini AI & pgvector RAG Architecture.
          </p>

          <div className="flex items-center gap-4">
            <span className="hover:text-gray-700 cursor-pointer">
              Privacy Policy
            </span>
            <span>•</span>
            <span className="hover:text-gray-700 cursor-pointer">
              Terms of Service
            </span>
            <span>•</span>
            <span className="hover:text-gray-700 cursor-pointer">
              Source Transparency Policy
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
