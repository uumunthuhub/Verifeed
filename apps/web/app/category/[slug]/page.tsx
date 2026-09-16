import { Suspense } from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { StoryCard, StoryCardSkeleton } from "@/components/StoryCard";
import { fetchStories } from "@/lib/api";
import { Story } from "@/lib/types";
import { ArrowLeft } from "lucide-react";

interface PageProps {
  params: Promise<{ slug: string }>;
}

function EmptyState({ category }: { category: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="text-6xl mb-4">📰</div>
      <h2 className="text-2xl font-bold text-foreground mb-2">
        No {category} stories yet
      </h2>
      <p className="text-ink-700 max-w-md">
        The feed is warming up. Add news sources and trigger ingestion to see{" "}
        {category.toLowerCase()} stories here.
      </p>
    </div>
  );
}

function SkeletonFeed() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <StoryCardSkeleton key={i} />
      ))}
    </div>
  );
}

async function StoryFeed({ category }: { category: string }) {
  const stories: Story[] = await fetchStories(category);
  if (!stories.length) return <EmptyState category={category} />;
  return (
    <main className="space-y-4" aria-label="Story feed">
      {stories.map((story) => (
        <StoryCard key={story.id} story={story} />
      ))}
    </main>
  );
}

export default async function CategoryPage({ params }: PageProps) {
  const { slug } = await params;

  // Map slug to display name
  const categoryNames: Record<string, string> = {
    "": "All",
    Politics: "Politics",
    World: "World",
    Business: "Business",
    Technology: "Technology",
    Health: "Health",
    Sports: "Sports",
    Entertainment: "Entertainment",
    Regional: "Regional",
  };

  const categoryName = categoryNames[slug] || slug;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar activeCategory={slug} maxWidth="max-w-6xl" />
      <div className="max-w-6xl mx-auto px-4 pt-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm font-semibold text-primary-600 hover:text-primary-700 transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
          <h1 className="text-3xl md:text-4xl font-black text-foreground">
            {categoryName} News
          </h1>
          <p className="text-ink-700 mt-2">
            Browse the latest {categoryName.toLowerCase()} headlines from
            verified sources.
          </p>
        </div>

        {/* Content Row */}
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Story Feed */}
          <div className="flex-1 min-w-0">
            <Suspense fallback={<SkeletonFeed />}>
              <StoryFeed category={slug} />
            </Suspense>
          </div>
        </div>
      </div>
    </div>
  );
}
