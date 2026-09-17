import Link from "next/link";
import { Story } from "@/lib/types";

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

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60)    return `${diff}s ago`;
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function getInitials(count: number): string[] {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  return Array.from({ length: Math.min(count, 5) }, (_, i) => alphabet[i % 26]);
}

export function StoryCard({ story }: { story: Story }) {
  const catClass = story.category ? (CATEGORIES[story.category] ?? "cat-other") : "cat-other";
  const initials = getInitials(story.article_count);

  return (
    <Link href={`/story/${story.id}`} className="vf-card vf-animate-in" aria-label={`Read story: ${story.title}`}>
      <div className="vf-card-header">
        <div>
          {story.primary_source && (
            <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-extrabold uppercase tracking-wider bg-primary-100 text-primary-800 dark:bg-primary-950/80 dark:text-primary-300 dark:border dark:border-primary-800/60 mb-1.5">
              <span>{story.primary_source}</span>
            </div>
          )}
          <h2 className="vf-card-headline">{story.title}</h2>
        </div>
        <svg className="vf-arrow" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"
          viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 17L17 7M17 7H7M17 7v10" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>

      {story.summary && (
        <p style={{ fontSize: "13px", color: "var(--vf-text-secondary)", margin: "0 0 10px", lineHeight: 1.5 }}>
          {story.summary.slice(0, 160)}{story.summary.length > 160 ? "…" : ""}
        </p>
      )}

      <div className="vf-card-meta">
        {story.category && (
          <span className={`vf-category-badge ${catClass}`}>
            {story.category}
          </span>
        )}

        {story.article_count > 0 && (
          <div className="vf-sources-count">
            <div className="vf-sources-dots" aria-hidden="true">
              {initials.map((letter, i) => (
                <div key={i} className="vf-source-dot">{letter}</div>
              ))}
            </div>
            <span>{story.article_count} source{story.article_count !== 1 ? "s" : ""}</span>
          </div>
        )}

        <span className="vf-time">{timeAgo(story.created_at)}</span>
      </div>
    </Link>
  );
}

export function StoryCardSkeleton() {
  return (
    <div className="vf-card" aria-hidden="true">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, marginBottom: 10 }}>
        <div className="vf-skeleton" style={{ height: 20, width: "70%", borderRadius: 6 }} />
        <div className="vf-skeleton" style={{ height: 16, width: 16, borderRadius: 4, flexShrink: 0 }} />
      </div>
      <div className="vf-skeleton" style={{ height: 14, width: "90%", borderRadius: 6, marginBottom: 6 }} />
      <div className="vf-skeleton" style={{ height: 14, width: "60%", borderRadius: 6, marginBottom: 14 }} />
      <div style={{ display: "flex", gap: 10 }}>
        <div className="vf-skeleton" style={{ height: 22, width: 70, borderRadius: 100 }} />
        <div className="vf-skeleton" style={{ height: 22, width: 90, borderRadius: 100 }} />
      </div>
    </div>
  );
}
