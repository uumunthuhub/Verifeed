import { notFound } from "next/navigation";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { fetchStory } from "@/lib/api";
import { StoryDetail, Article } from "@/lib/types";
import type { Metadata } from "next";

const CATEGORIES: Record<string, string> = {
  Politics:      "cat-politics",
  Health:        "cat-health",
  Business:      "cat-business",
  Sports:        "cat-sports",
  Technology:    "cat-technology",
  World:         "cat-world",
  Regional:      "cat-regional",
  Entertainment: "cat-entertainment",
  Other:         "cat-other",
  Uncategorized: "cat-other",
};

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "Unknown";
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60)    return `${diff}s ago`;
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  const story: StoryDetail | null = await fetchStory(Number(id));
  if (!story) return { title: "Story Not Found — VeriFeed" };
  return {
    title: `${story.title} — VeriFeed`,
    description: story.summary ?? `See how ${story.article_count} sources covered this story.`,
  };
}

function SourceArticleCard({ article }: { article: Article }) {
  const sourceName = article.source?.name ?? (() => {
    try { return new URL(article.url).hostname.replace("www.", ""); }
    catch { return "Unknown Source"; }
  })();

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="vf-source-card"
      aria-label={`Read "${article.headline}" on ${sourceName}`}
    >
      <div className="vf-source-name font-bold text-primary-600 dark:text-primary-400 uppercase tracking-wider mb-1">
        {sourceName}
      </div>
      <div className="vf-source-headline text-base font-semibold text-foreground">
        {article.headline}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
        <div className="vf-source-time">{timeAgo(article.published_at)}</div>
        {article.published_at && (
          <div className="vf-source-time" aria-label={`Published ${formatDate(article.published_at)}`}>
            · {formatDate(article.published_at)}
          </div>
        )}
        <svg style={{ marginLeft: "auto", color: "var(--vf-text-muted)" }} width="13" height="13"
          fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>
          <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
        </svg>
      </div>
    </a>
  );
}

export default async function StoryPage({ params }: PageProps) {
  const { id } = await params;
  const story: StoryDetail | null = await fetchStory(Number(id));
  if (!story) notFound();

  const catClass = story.category ? (CATEGORIES[story.category] ?? "cat-other") : "cat-other";

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar maxWidth="max-w-6xl" />
      <div className="max-w-6xl mx-auto px-4 pt-8" style={{ position: "relative", zIndex: 1 }}>
        {/* Detail header */}
        <section className="vf-detail-header vf-animate-in">
          <Link href="/" className="vf-back">
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"
              viewBox="0 0 24 24" aria-hidden="true">
              <path d="M19 12H5M12 5l-7 7 7 7" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Back to feed
          </Link>

          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10, marginTop: 20, marginBottom: 4 }}>
            {story.category && (
              <span className={`vf-category-badge ${catClass}`} style={{ fontSize: 12 }}>
                {story.category}
              </span>
            )}
            <span className="vf-live" style={{ fontSize: 11 }}>
              <span className="vf-live-dot" aria-hidden="true" />
              {story.article_count} source{story.article_count !== 1 ? "s" : ""} covering this
            </span>
          </div>

          <h1 className="vf-detail-title">{story.title}</h1>

          {story.summary && (
            <p style={{ color: "var(--vf-text-secondary)", fontSize: 15, lineHeight: 1.6, marginTop: 8 }}>
              {story.summary}
            </p>
          )}

          <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 16 }}>
            <span style={{ fontSize: 13, color: "var(--vf-text-muted)" }}>
              First seen {timeAgo(story.created_at)}
            </span>
          </div>
        </section>

        {/* Sources section */}
        <section aria-labelledby="sources-heading" className="vf-animate-in vf-stagger-2">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
            <h2
              id="sources-heading"
              style={{
                fontFamily: "Inter, sans-serif",
                fontSize: 18,
                fontWeight: 700,
                margin: 0,
                color: "var(--vf-text-primary)",
              }}
            >
              Sources
            </h2>
            <span style={{ fontSize: 13, color: "var(--vf-text-muted)" }}>
              {story.articles.length} article{story.articles.length !== 1 ? "s" : ""}
            </span>
          </div>

          {story.articles.length === 0 ? (
            <div className="vf-empty">
              <div className="vf-empty-icon">📭</div>
              <p className="vf-empty-text">No source articles found for this story yet.</p>
            </div>
          ) : (
            <div>
              {story.articles.map((article) => (
                <SourceArticleCard key={article.id} article={article} />
              ))}
            </div>
          )}
        </section>

        <div style={{ height: 64 }} />
      </div>
    </div>
  );
}
