import React from "react";
import { AlertTriangle, ShieldCheck, XCircle, CheckCircle, Info, ExternalLink } from "lucide-react";

interface RecommendedAction {
  action: string;
  priority: "critical" | "high" | "medium" | "low";
  reason?: string;
}

interface GuidanceCardProps {
  riskLevel: "High" | "Medium" | "Low";
  messageAuthenticityVerdict?: string;
  claimVerdict?: string;
  recommendedActions: RecommendedAction[];
  verifiedInstitution?: string;
  officialChannels?: string[];
}

export function GuidanceCard({
  riskLevel,
  messageAuthenticityVerdict,
  claimVerdict,
  recommendedActions,
  verifiedInstitution,
  officialChannels,
}: GuidanceCardProps) {
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case "High":
        return "bg-danger/10 border-danger/30 text-danger";
      case "Medium":
        return "bg-warning/10 border-warning/30 text-warning";
      case "Low":
        return "bg-success/10 border-success/30 text-success";
      default:
        return "bg-info/10 border-info/30 text-info";
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case "critical":
        return <XCircle className="w-4 h-4 text-danger" />;
      case "high":
        return <AlertTriangle className="w-4 h-4 text-warning" />;
      case "medium":
        return <Info className="w-4 h-4 text-info" />;
      case "low":
        return <CheckCircle className="w-4 h-4 text-success" />;
      default:
        return <Info className="w-4 h-4 text-info" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical":
        return "text-danger border-danger/30 bg-danger/5";
      case "high":
        return "text-warning border-warning/30 bg-warning/5";
      case "medium":
        return "text-info border-info/30 bg-info/5";
      case "low":
        return "text-success border-success/30 bg-success/5";
      default:
        return "text-ink-700 border-border bg-soft";
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-surface p-6 shadow-lg">
      {/* Risk Level Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-border">
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-5 h-5 text-primary-600" />
          <h3 className="text-sm font-extrabold uppercase tracking-wider text-ink-500">
            What Should You Do?
          </h3>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getRiskColor(riskLevel)}`}>
          Risk: {riskLevel}
        </span>
      </div>

      {/* Verdict Summary */}
      {(messageAuthenticityVerdict || claimVerdict) && (
        <div className="mb-6 bg-soft rounded-xl p-4 border border-border">
          {messageAuthenticityVerdict && (
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-semibold text-ink-500">Message Authenticity:</span>
              <span className="text-xs font-bold text-ink-900">{messageAuthenticityVerdict}</span>
            </div>
          )}
          {claimVerdict && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-ink-500">Claim Verdict:</span>
              <span className="text-xs font-bold text-ink-900">{claimVerdict}</span>
            </div>
          )}
        </div>
      )}

      {/* Verified Institution Info */}
      {verifiedInstitution && (
        <div className="mb-6 bg-success/10 rounded-xl p-4 border border-success/30">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-4 h-4 text-success" />
            <span className="text-xs font-bold text-success">
              Verified Institution: {verifiedInstitution}
            </span>
          </div>
          {officialChannels && officialChannels.length > 0 && (
            <div className="ml-6">
              <span className="text-xs font-semibold text-ink-600 block mb-1">Official Channels:</span>
              <ul className="text-xs text-ink-700 space-y-1">
                {officialChannels.map((channel, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <span className="w-1 h-1 bg-success rounded-full" />
                    {channel}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Recommended Actions */}
      <div className="space-y-3">
        <span className="text-xs font-semibold text-ink-500 block mb-3">Recommended Actions:</span>
        {recommendedActions.map((action, idx) => (
          <div
            key={idx}
            className={`flex items-start gap-3 p-3 rounded-lg border ${getPriorityColor(action.priority)}`}
          >
            <div className="mt-0.5">{getPriorityIcon(action.priority)}</div>
            <div className="flex-1">
              <p className="text-sm font-medium text-ink-900">{action.action}</p>
              {action.reason && (
                <p className="text-xs text-ink-600 mt-1">{action.reason}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Contact Official Channel CTA */}
      {verifiedInstitution && (
        <div className="mt-6 pt-4 border-t border-border">
          <div className="bg-primary-50 rounded-xl p-4 border border-primary-200">
            <div className="flex items-center gap-2 mb-2">
              <ExternalLink className="w-4 h-4 text-primary-600" />
              <span className="text-xs font-bold text-primary-700">
                Contact Official Channel
              </span>
            </div>
            <p className="text-xs text-ink-700 leading-relaxed">
              If you&apos;re unsure, contact {verifiedInstitution} directly using their verified official channels listed above.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
