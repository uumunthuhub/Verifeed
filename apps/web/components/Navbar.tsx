"use client";

import { useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";

const CATEGORIES = [
  { name: "All", slug: "" },
  { name: "Politics", slug: "Politics" },
  { name: "World", slug: "World" },
  { name: "Business", slug: "Business" },
  { name: "Technology", slug: "Technology" },
  { name: "Health", slug: "Health" },
  { name: "Sports", slug: "Sports" },
  { name: "Entertainment", slug: "Entertainment" },
  { name: "Regional", slug: "Regional" },
];

export function Navbar({
  activeCategory,
  maxWidth = "max-w-6xl",
}: {
  activeCategory?: string;
  maxWidth?: string;
}) {
  const active = activeCategory ?? "";
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <header className={`sticky top-4 z-40 mx-auto ${maxWidth} px-4`}>
      {/* Main nav - Floating glassmorphism */}
      <nav
        className="bg-white/80 backdrop-blur-xl border border-border rounded-2xl shadow-lg"
        role="banner"
      >
        <div className="flex items-center justify-between px-6 py-3">
          {/* Logo - Left side */}
          <Link
            href="/"
            className="flex items-center gap-2"
            aria-label="VeriFeed home"
          >
            <div className="w-9 h-9 rounded-xl bg-white border border-primary-200 shadow-md shadow-primary-500/10 flex items-center justify-center p-0.5 overflow-hidden shrink-0">
              <img src="/verifeed-bot.png" alt="VeriFeed Logo" className="h-full w-full object-contain" />
            </div>
            <span className="font-black text-lg text-primary-600">
              VeriFeed
            </span>
          </Link>

          {/* Searchbar, Nav Links & Mobile Links - Right side */}
          <div className="flex items-center gap-4">
            {/* Searchbar */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (searchQuery.trim()) {
                  window.location.href = `/search?q=${encodeURIComponent(searchQuery.trim())}`;
                }
              }}
              className="relative hidden md:block"
            >
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-400" />
              <input
                type="text"
                placeholder="Search stories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-1.5 rounded-full text-xs bg-soft border border-border focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent w-48 md:w-64 transition-all"
              />
            </form>

            {/* Main Nav Links */}
            <div className="hidden md:flex items-center gap-2">
              <Link
                href="/"
                className="px-3 py-1.5 rounded-full text-xs font-bold text-ink-700 hover:bg-soft hover:text-ink-900 transition-all"
              >
                📰 News Feed
              </Link>
              <Link
                href="/verify"
                className="px-3 py-1.5 rounded-full text-xs font-bold text-white bg-primary-500 border border-primary-600 hover:bg-primary-600 transition-all shadow-[0_0_12px_rgba(69,168,107,0.3)]"
              >
                🔍 Verify Claim
              </Link>
              <Link
                href="/scams"
                className="px-3 py-1.5 rounded-full text-xs font-bold text-red-600 bg-red-50 border border-red-200 hover:bg-red-100 transition-all"
              >
                🛑 Fraud Alerts
              </Link>
              <Link
                href="/settings"
                className="px-3 py-1.5 rounded-full text-xs font-bold text-ink-700 hover:bg-soft hover:text-ink-900 transition-all"
              >
                ⚙️ Protection
              </Link>
            </div>

            {/* Mobile Verify Link */}
            <Link
              href="/verify"
              className="md:hidden px-3 py-1 rounded-full text-xs font-bold bg-primary-500 text-white border border-primary-600"
            >
              Verify 🔍
            </Link>
          </div>
        </div>
      </nav>

      {/* Category pills - Floating below main nav */}
      <div className="mt-3 bg-white/60 backdrop-blur-lg rounded-xl shadow-sm">
        <div
          className="flex items-center justify-center gap-1 px-4 py-2 mb-4 overflow-x-auto"
          role="navigation"
          aria-label="Category navigation"
        >
          {CATEGORIES.map((cat) => (
            <Link
              key={cat.slug}
              href={cat.slug ? `/category/${cat.slug}` : "/"}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                active === cat.slug
                  ? "bg-primary-500 text-white shadow-sm"
                  : "text-ink-700 hover:bg-soft"
              }`}
              aria-current={active === cat.slug ? "page" : undefined}
            >
              {cat.name}
            </Link>
          ))}
        </div>
      </div>
    </header>
  );
}
