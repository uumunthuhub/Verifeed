"use client";

import { useState } from "react";
import { QuickScreenWidget } from "@/components/QuickScreenWidget";
import { AskAgentWithContent } from "@/components/AskAgentWithContent";

interface VerifyLabFlowProps {
  initialContent?: string;
}

export function VerifyLabFlow({ initialContent }: VerifyLabFlowProps) {
  const [activeTab, setActiveTab] = useState<"quick" | "deep">("quick");

  return (
    <div className="bg-surface border border-border rounded-2xl overflow-hidden shadow-sm mb-8">
      {/* Tabs Header */}
      <div className="flex border-b border-border bg-soft flex-col sm:flex-row">
        <button
          onClick={() => setActiveTab("quick")}
          className={`flex-1 py-4 px-4 text-center font-bold text-sm transition-colors ${
            activeTab === "quick"
              ? "bg-surface text-foreground border-b-2 border-primary-500"
              : "text-ink-500 hover:text-foreground hover:bg-surface/50"
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-black ${
                activeTab === "quick"
                  ? "bg-amber-100 text-amber-700"
                  : "bg-ink-100 text-ink-500"
              }`}
            >
              1
            </span>
            Quick Screen
          </div>
        </button>
        <button
          onClick={() => setActiveTab("deep")}
          className={`flex-1 py-4 px-4 text-center font-bold text-sm transition-colors ${
            activeTab === "deep"
              ? "bg-surface text-foreground border-b-2 border-primary-500"
              : "text-ink-500 hover:text-foreground hover:bg-surface/50"
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-black ${
                activeTab === "deep"
                  ? "bg-primary-100 text-primary-700"
                  : "bg-ink-100 text-ink-500"
              }`}
            >
              2
            </span>
            Deep Verification
          </div>
        </button>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === "quick" ? (
          <div>
            <div className="mb-6 pb-4 border-b border-border">
              <h2 className="text-lg font-bold text-foreground">Quick Screen</h2>
              <p className="text-sm text-ink-500">
                Instant fact-check against known databases without full AI synthesis.
              </p>
            </div>
            <QuickScreenWidget />
            <div className="mt-8 flex justify-end">
              <button
                onClick={() => setActiveTab("deep")}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700 transition-colors"
              >
                Proceed to Deep Verification →
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="mb-6 pb-4 border-b border-border flex justify-between items-center">
              <div>
                <h2 className="text-lg font-bold text-foreground">
                  Deep Verification
                </h2>
                <p className="text-sm text-ink-500">
                  Full AI verification with evidence trails and detailed verdict.
                </p>
              </div>
            </div>
            <AskAgentWithContent initialContent={initialContent} />
          </div>
        )}
      </div>
    </div>
  );
}
