import Link from "next/link";

const CATEGORIES = [
  { name: "All",           slug: "",              dot: "#8b93b0" },
  { name: "Politics",      slug: "Politics",      dot: "#f87171" },
  { name: "World",         slug: "World",         dot: "#f472b6" },
  { name: "Business",      slug: "Business",      dot: "#fbbf24" },
  { name: "Technology",    slug: "Technology",    dot: "#a78bfa" },
  { name: "Health",        slug: "Health",        dot: "#4ade80" },
  { name: "Sports",        slug: "Sports",        dot: "#63d3ff" },
  { name: "Entertainment", slug: "Entertainment", dot: "#fb923c" },
  { name: "Regional",      slug: "Regional",      dot: "#34d399" },
];

export function Sidebar({ activeCategory }: { activeCategory?: string }) {
  const active = activeCategory ?? "";
  return (
    <nav aria-label="Category filter">
      <p className="vf-sidebar-heading">Categories</p>
      {CATEGORIES.map((cat) => (
        <Link
          key={cat.slug}
          href={cat.slug ? `/?category=${cat.slug}` : "/"}
          className={`vf-sidebar-item ${active === cat.slug ? "vf-sidebar-item-active" : ""}`}
          aria-current={active === cat.slug ? "page" : undefined}
        >
          <span className="vf-sidebar-dot" style={{ background: cat.dot }} aria-hidden="true" />
          {cat.name}
        </Link>
      ))}
    </nav>
  );
}
