"use client";

interface VerdictBadgeProps {
  verdict: string;
  verdictType?: "claim" | "authenticity" | "legacy";
  size?: "sm" | "md" | "lg";
}

export function VerdictBadge({ verdict, verdictType = "legacy", size = "md" }: VerdictBadgeProps) {
  let badgeStyle = "bg-ink-900 text-ink-100 border-ink-700";
  let icon = "❓";

  // Claim verdicts: True, False, Partly True, Misleading, Insufficient Evidence
  if (verdictType === "claim") {
    switch (verdict) {
      case "True":
        badgeStyle = "bg-success/20 text-success border-success/50 shadow-[0_0_15px_rgba(36,122,77,0.25)]";
        icon = "✅";
        break;
      case "False":
        badgeStyle = "bg-danger/20 text-danger border-danger/50 shadow-[0_0_15px_rgba(197,61,61,0.3)]";
        icon = "🚫";
        break;
      case "Partly True":
        badgeStyle = "bg-warning/20 text-warning border-warning/50";
        icon = "⚠️";
        break;
      case "Misleading":
        badgeStyle = "bg-warning/20 text-warning border-warning/50";
        icon = "⚠️";
        break;
      case "Insufficient Evidence":
      default:
        badgeStyle = "bg-info/20 text-info border-info/50";
        icon = "❓";
        break;
    }
  }
  // Message authenticity verdicts: Verified Official, Likely Legitimate, Unverified, Suspicious, Likely Fraudulent, Confirmed Fraudulent
  else if (verdictType === "authenticity") {
    switch (verdict) {
      case "Verified Official":
        badgeStyle = "bg-success/20 text-success border-success/50 shadow-[0_0_15px_rgba(36,122,77,0.25)]";
        icon = "✅";
        break;
      case "Likely Legitimate":
        badgeStyle = "bg-success/20 text-success border-success/50";
        icon = "✓";
        break;
      case "Unverified":
        badgeStyle = "bg-info/20 text-info border-info/50";
        icon = "❓";
        break;
      case "Suspicious":
        badgeStyle = "bg-warning/20 text-warning border-warning/50";
        icon = "⚠️";
        break;
      case "Likely Fraudulent":
        badgeStyle = "bg-danger/20 text-danger border-danger/50";
        icon = "⚠️";
        break;
      case "Confirmed Fraudulent":
        badgeStyle = "bg-danger/20 text-danger border-danger/50 shadow-[0_0_15px_rgba(197,61,61,0.3)] animate-pulse";
        icon = "🛑";
        break;
      default:
        badgeStyle = "bg-info/20 text-info border-info/50";
        icon = "❓";
        break;
    }
  }
  // Legacy single verdict system (backward compatibility)
  else {
    switch (verdict) {
      case "Confirmed Scam":
        badgeStyle = "bg-danger/20 text-danger border-danger/50 shadow-[0_0_15px_rgba(197,61,61,0.3)] animate-pulse";
        icon = "🛑";
        break;
      case "Confirmed":
        badgeStyle = "bg-success/20 text-success border-success/50 shadow-[0_0_15px_rgba(36,122,77,0.25)]";
        icon = "✅";
        break;
      case "Unconfirmed":
        badgeStyle = "bg-warning/20 text-warning border-warning/50";
        icon = "⚠️";
        break;
      case "Disputed / False":
        badgeStyle = "bg-danger/20 text-danger border-danger/50";
        icon = "🚫";
        break;
      case "No Coverage Found":
      default:
        badgeStyle = "bg-info/20 text-info border-info/50";
        icon = "❓";
        break;
    }
  }

  const sizeClasses = {
    sm: "px-2.5 py-0.5 text-xs gap-1.5 font-semibold",
    md: "px-3.5 py-1 text-sm gap-2 font-bold",
    lg: "px-5 py-2 text-base gap-2.5 font-extrabold tracking-wide",
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-full border backdrop-blur-md transition-all duration-300 ${badgeStyle} ${sizeClasses}`}
    >
      <span className="text-base">{icon}</span>
      <span>{verdict}</span>
    </span>
  );
}
