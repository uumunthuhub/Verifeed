import { Navbar } from "@/components/Navbar";
import { VerdictBadge } from "@/components/VerdictBadge";
import { searchStories } from "@/lib/api";
import Link from "next/link";
import { Search } from "lucide-react";

interface SearchPageProps {
  searchParams: Promise<{ q?: string }>;
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const params = await searchParams;
  const query = params.q || "";
  const stories = query ? await searchStories(query) : [];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar maxWidth="max-w-6xl" />

      <main className="max-w-6xl mx-auto px-4 pt-8 space-y-6">
        {/* Header section */}
        <div className="bg-white border border-border rounded-2xl p-6 shadow-xs">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center">
              <Search className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-black text-ink-900 tracking-tight">
                Search Results
              </h1>
              {query ? (
                <p className="text-ink-500 text-xs mt-0.5">
                  Showing results for &ldquo;<span className="text-primary-600 font-semibold">{query}</span>&rdquo;
                </p>
              ) : (
                <p className="text-ink-500 text-xs mt-0.5">
                  Type a keyword in the navigation search bar to search stories and headlines.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Results grid */}
        {stories.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {stories.map((story: {
              id: number;
              title: string;
              summary?: string;
              verdict?: string;
              category?: string;
              created_at?: string;
              article_count?: number;
            }) => (
              <Link
                key={story.id}
                href={`/story/${story.id}`}
                className="group flex flex-col justify-between bg-white border border-border hover:border-primary-500/50 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all duration-200"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-soft text-ink-700 border border-border">
                      {story.category || "General"}
                    </span>
                    {story.verdict && <VerdictBadge verdict={story.verdict} size="sm" />}
                  </div>

                  <h2 className="text-base font-bold text-ink-900 group-hover:text-primary-600 transition-colors line-clamp-2 mb-2 leading-snug">
                    {story.title}
                  </h2>

                  {story.summary && (
                    <p className="text-xs text-ink-600 line-clamp-3 mb-4 leading-relaxed">
                      {story.summary}
                    </p>
                  )}
                </div>

                <div className="pt-3 border-t border-border/60 flex items-center justify-between text-xs text-ink-500">
                  <span>{story.article_count || 1} source articles</span>
                  <span className="text-primary-600 font-bold group-hover:translate-x-1 transition-transform inline-flex items-center gap-1">
                    View Details &rarr;
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          query && (
            <div className="text-center py-16 bg-white border border-border rounded-2xl p-8 shadow-xs">
              <span className="text-4xl mb-4 block">🔍</span>
              <h3 className="text-lg font-bold text-ink-900 mb-1">No matching stories found</h3>
              <p className="text-ink-500 text-xs max-w-md mx-auto mb-6">
                We couldn&apos;t find any stories matching &ldquo;{query}&rdquo;. Try searching with different keywords or browse the category feeds.
              </p>
              <Link
                href="/"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary-500 hover:bg-primary-600 text-white font-bold text-xs transition-all shadow-sm"
              >
                Browse All Stories
              </Link>
            </div>
          )
        )}
      </main>
    </div>
  );
}
