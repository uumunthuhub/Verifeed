import { Navbar } from "@/components/Navbar";
import { fetchInstitutionalAlerts, fetchEmergingClusters } from "@/lib/api";
import { VerdictBadge } from "@/components/VerdictBadge";
import { SubmitScamWidget } from "@/components/SubmitScamWidget";

export const metadata = {
  title: "Institutional Fraud & Scam Alerts — VeriFeed",
  description:
    "Official scam disclaimers and fraud warnings from banks, regulators, and mobile money providers.",
};

export default async function ScamsPage() {
  const [alerts, clusters] = await Promise.all([
    fetchInstitutionalAlerts(),
    fetchEmergingClusters(),
  ]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar maxWidth="max-w-6xl" />
      <main className="max-w-6xl mx-auto px-4 pt-8">
        {/* Page Header */}
        <header className="mb-10 text-center max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-red-50 text-red-600 border border-red-200 mb-3 shadow-[0_0_12px_rgba(197,61,61,0.2)]">
            <span>🛑 Institutional Scam Protection</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-black text-foreground tracking-tight mb-3">
            Institutional{" "}
            <span className="bg-linear-to-r from-danger via-danger/80 to-warning bg-clip-text text-transparent">
              Fraud Feed
            </span>
          </h1>
          <p className="text-sm md:text-base text-gray-600">
            Direct public disclaimers issued by banks, telecommunications
            operators, and government regulators warning against impersonation
            scams.
          </p>
        </header>

        {/* User Submission Widget */}
        <section className="mb-12">
          <SubmitScamWidget />
        </section>

        {/* Official Disclaimers Feed */}
        <section className="mb-16">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg md:text-xl font-black text-foreground tracking-tight flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-danger inline-block shadow-[0_0_8px_rgba(197,61,61,0.8)]" />
              Verified Institutional Warnings ({alerts.length})
            </h2>
            <span className="text-xs text-gray-500">Real-time DB feeds</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {alerts.map((alert) => (
              <article
                key={alert.id}
                className="relative flex flex-col justify-between overflow-hidden rounded-3xl border border-red-200 bg-white p-6 md:p-7 shadow-xl shadow-red-100 hover:border-red-300 transition-all duration-200"
              >
                {/* Top alert header */}
                <div className="flex items-center justify-between gap-3 mb-4">
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-50 text-red-600 font-black border border-red-200 text-base shadow-inner">
                      🏛️
                    </span>
                    <div>
                      <h3 className="text-sm font-bold text-foreground leading-tight">
                        {alert.institution.name}
                      </h3>
                      <span className="text-[11px] text-red-500 font-medium">
                        {alert.institution.sector}
                      </span>
                    </div>
                  </div>
                  <VerdictBadge verdict="Confirmed Scam" size="sm" />
                </div>

                {/* Title & Alert Text */}
                <div className="mb-6">
                  <h4 className="text-base md:text-lg font-bold text-foreground mb-2 leading-snug">
                    {alert.title}
                  </h4>
                  <p className="text-xs md:text-sm text-ink-700 leading-relaxed bg-soft p-4 rounded-xl border border-border font-normal">
                    {alert.alert_text}
                  </p>
                </div>

                {/* Source Link Footer */}
                <div className="flex items-center justify-between pt-4 border-t border-border text-xs text-ink-500">
                  <span>
                    {new Date(alert.published_date).toLocaleDateString(
                      "en-US",
                      {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      },
                    )}
                  </span>
                  <a
                    href={alert.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold text-danger hover:text-danger/80 hover:underline flex items-center gap-1 transition-colors"
                  >
                    <span>Official Disclaimer</span>
                    <span>↗</span>
                  </a>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* Emerging Patterns Feed */}
        {clusters.length > 0 && (
          <section className="mt-16 border-t border-gray-200 pt-12">
            <div className="mb-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-yellow-50 text-yellow-600 border border-yellow-200 mb-3 shadow-[0_0_10px_rgba(234,179,8,0.2)]">
                <span>⚠️ Emerging Patterns</span>
              </div>
              <h2 className="text-2xl md:text-3xl font-black text-foreground tracking-tight mb-2">
                Unconfirmed Community Scam Reports
              </h2>
              <p className="text-sm md:text-base text-gray-600">
                Suspicious SMS and WhatsApp messages recently reported by users,
                clustered automatically using vector embeddings.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {clusters.map((cluster) => (
                <article
                  key={cluster.id}
                  className="relative flex flex-col justify-between overflow-hidden rounded-3xl border border-yellow-200 bg-white p-6 md:p-7 shadow-xl shadow-yellow-100 hover:border-yellow-300 transition-all duration-200"
                >
                  <div className="flex items-center justify-between gap-3 mb-4">
                    <div className="flex items-center gap-3">
                      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-yellow-50 text-yellow-600 font-black border border-yellow-200 text-base">
                        👥
                      </span>
                      <div>
                        <h3 className="text-sm font-bold text-foreground leading-tight">
                          Community Fraud Cluster
                        </h3>
                        <span className="text-[11px] text-yellow-500 font-medium">
                          {cluster.submission_count}{" "}
                          {cluster.submission_count === 1
                            ? "report"
                            : "reports"}{" "}
                          received
                        </span>
                      </div>
                    </div>
                    <VerdictBadge verdict="Unconfirmed" size="sm" />
                  </div>

                  <div className="mb-6">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-ink-500 block mb-1">
                      Representative Message Text
                    </span>
                    <p className="text-xs md:text-sm text-ink-700 leading-relaxed bg-soft p-4 rounded-xl border border-border italic">
                      &ldquo;{cluster.representative_text}&rdquo;
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-border text-xs text-ink-500">
                    <span>
                      First seen:{" "}
                      {new Date(cluster.first_seen).toLocaleDateString(
                        "en-US",
                        {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        },
                      )}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
