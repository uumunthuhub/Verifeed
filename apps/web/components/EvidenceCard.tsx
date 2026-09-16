import React from "react";
import { ExternalLink, ShieldAlert, Newspaper, CheckCircle2, FileText } from "lucide-react";

export interface EvidenceSource {
  title: string;
  outlet: string;
  url?: string;
  type?: string;
  snippet?: string;
}

export function EvidenceCard({ source }: { source: EvidenceSource }) {
  const getBadgeStyle = (type?: string) => {
    switch (type) {
      case "Official Institutional Alert":
        return "bg-red-50 text-red-600 border-red-200 shadow-[0_0_10px_rgba(197,61,61,0.2)]";
      case "Fact Checker Rating":
        return "bg-primary-50 text-primary-600 border-primary-200";
      case "News Article":
        return "bg-soft text-ink-600 border-border";
      default:
        return "bg-soft text-ink-600 border-border";
    }
  };

  const getIcon = (type?: string) => {
    switch (type) {
      case "Official Institutional Alert":
        return <ShieldAlert className="w-4 h-4 text-red-600 mr-1.5 inline-block" />;
      case "Fact Checker Rating":
        return <CheckCircle2 className="w-4 h-4 text-primary-600 mr-1.5 inline-block" />;
      case "News Article":
        return <Newspaper className="w-4 h-4 text-ink-600 mr-1.5 inline-block" />;
      default:
        return <FileText className="w-4 h-4 text-ink-600 mr-1.5 inline-block" />;
    }
  };

  return (
    <div className="group relative rounded-xl bg-surface border border-border p-4 transition-all duration-200 hover:border-border hover:bg-soft shadow-md">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getBadgeStyle(
              source.type
            )}`}
          >
            {getIcon(source.type)}
            {source.type || "Evidence Source"}
          </span>
          <span className="text-xs font-medium text-ink-600 bg-soft px-2 py-0.5 rounded-md border border-border">
            {source.outlet}
          </span>
        </div>
        {source.url && (
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-ink-400 hover:text-primary-600 transition-colors p-1 rounded-lg hover:bg-soft"
            title="Open primary source"
            aria-label={`Open primary source for ${source.title}`}
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        )}
      </div>

      <h4 className="text-sm font-bold text-ink-900 group-hover:text-primary-600 transition-colors line-clamp-2 mb-1">
        {source.title}
      </h4>

      {source.snippet && (
        <p className="text-xs text-ink-600 line-clamp-3 leading-relaxed mt-2 bg-soft p-2.5 rounded-lg border border-border">
          &ldquo;{source.snippet}&rdquo;
        </p>
      )}
    </div>
  );
}
