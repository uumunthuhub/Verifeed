"use client";

import { useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";

export function Navbar({
  maxWidth = "max-w-6xl",
}: {
  activeCategory?: string;
  maxWidth?: string;
}) {
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
            <div className="w-8 h-8 rounded-lg bg-linear-to-tr from-primary-500 to-primary-600 text-white font-black shadow-lg shadow-primary-500/30 flex items-center justify-center text-sm">
              VF
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
                placeholder="Search claims & alerts..."
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
                Home
              </Link>
              <Link
                href="/scams"
                className="px-3 py-1.5 rounded-full text-xs font-bold text-red-600 bg-red-50 border border-red-200 hover:bg-red-100 transition-all"
              >
                Fraud Alerts
              </Link>
              <Link
                href="/email-inspector"
                className="px-3 py-1.5 rounded-full text-xs font-bold text-indigo-600 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 transition-all"
              >
                Email Inspector
              </Link>
              <Link
                href="/settings"
                className="px-3 py-1.5 rounded-full text-xs font-bold text-ink-700 hover:bg-soft hover:text-ink-900 transition-all"
              >
                Protection
              </Link>
            </div>

          </div>
        </div>
      </nav>
    </header>
  );
}
