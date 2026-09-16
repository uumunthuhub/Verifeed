import React from "react";

export function ConfidenceIndicator({ score }: { score: number }) {
  const percentage = Math.round(Math.min(Math.max(score, 0), 1) * 100);

  const getConfidenceLevel = (val: number) => {
    if (val >= 85) return { label: "Strong Evidence", color: "bg-primary-500 text-white border-primary-500/30" };
    if (val >= 60) return { label: "Moderate Evidence", color: "bg-warning text-white border-warning/30" };
    return { label: "Limited Evidence", color: "bg-danger text-white border-danger/30" };
  };

  const level = getConfidenceLevel(percentage);

  return (
    <div className="flex flex-col gap-1.5 w-full">
      <div className="flex items-center justify-between text-xs font-semibold">
        <span className="text-ink-400 flex items-center gap-1.5">
          Evidence Strength
          <span className="text-[10px] text-ink-500 font-normal">(Based on available sources)</span>
        </span>
        <span className={`px-2 py-0.5 rounded-full text-xs font-bold border ${level.color}`}>
          {percentage}% — {level.label}
        </span>
      </div>

      <div className="h-2 w-full bg-ink-950 rounded-full overflow-hidden border border-ink-800 p-0.5">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            percentage >= 85
              ? "bg-linear-to-r from-primary-600 to-primary-400 shadow-[0_0_8px_rgba(69,168,107,0.6)]"
              : percentage >= 60
              ? "bg-linear-to-r from-yellow-600 to-warning shadow-[0_0_8px_rgba(234,179,8,0.5)]"
              : "bg-linear-to-r from-red-600 to-danger shadow-[0_0_8px_rgba(197,61,61,0.5)]"
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
