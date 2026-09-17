"use client";

/**
 * AskAgentWithContent — AskAgent variant accepting optional pre-filled content.
 *
 * Used by the updated verify page to support the share-to-VeriFeed flow:
 *   /verify?content=<encoded> → pre-fills this component's textarea
 *
 * Identical to AskAgent in all other behaviour. The initialContent prop
 * is applied once on mount via useState default value.
 */

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { verifyClaim } from "@/lib/api";
import { VerificationResult } from "@/lib/types";

const SAMPLE_CLAIMS = [
  "Standard Bank offering instant WhatsApp collateral free loans",
  "WHO declares new global pandemic emergency",
  "Reserve Bank warns against unlicensed crypto trading schemes",
  "Airtel Money calling users asking for secret PIN",
];

interface AttachedFile {
  name: string;
  size: string;
  dataUrl: string;
  isImage: boolean;
}

interface AskAgentWithContentProps {
  /** Pre-filled content from URL param — applied once on mount */
  initialContent?: string;
}

export function AskAgentWithContent({ initialContent }: AskAgentWithContentProps) {
  const [query, setQuery] = useState(initialContent ?? "");
  const [loading, setLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState<AttachedFile | null>(null);

  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const sizeFormatted =
      file.size > 1024 * 1024
        ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
        : `${Math.round(file.size / 1024)} KB`;

    const isImage = file.type.startsWith("image/");

    const reader = new FileReader();
    reader.onload = () => {
      setAttachedFile({
        name: file.name,
        size: sizeFormatted,
        dataUrl: reader.result as string,
        isImage,
      });
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveFile = () => {
    setAttachedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleVerify = async (textToVerify?: string) => {
    const text = textToVerify !== undefined ? textToVerify : query;
    if (!text.trim() && !attachedFile) return;

    setLoading(true);
    if (textToVerify !== undefined) setQuery(textToVerify);

    const res = await verifyClaim(
      text.trim(),
      attachedFile?.dataUrl || null,
      attachedFile?.name || null,
    );
    setLoading(false);

    if (res) router.push(`/verify/${res.id}`);
  };

  return (
    <div className="relative w-full overflow-hidden rounded-3xl border border-primary-200 bg-linear-to-br from-white via-gray-50 to-white p-6 md:p-8 shadow-2xl shadow-gray-200 backdrop-blur-xl">
      {/* Hidden File Input */}
      <input
        type="file"
        ref={fileInputRef}
        accept="image/*,.txt,.csv,.json"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Decorative Glow */}
      <div className="pointer-events-none absolute -top-24 -right-24 h-64 w-64 rounded-full bg-primary-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -left-24 h-64 w-64 rounded-full bg-primary-400/8 blur-3xl" />

      <div className="relative flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white border border-primary-200 p-0.5 shadow-md shadow-primary-500/10 overflow-hidden shrink-0">
            <img src="/verifeed-bot.png" alt="VeriFeed AI Bot" className="h-full w-full object-contain" />
          </span>
          <div>
            <h2 className="text-lg md:text-xl font-bold text-foreground tracking-tight">
              Ask VeriFeed AI Verification Agent
            </h2>
            <p className="text-xs md:text-sm text-gray-600">
              Paste a claim, headline, or upload an SMS screenshot / document to verify using
              multimodal RAG.
            </p>
          </div>
        </div>

        {/* Attached File Preview */}
        {attachedFile && (
          <div className="flex items-center gap-3 rounded-2xl border border-primary-200 bg-primary-50 px-4 py-2.5 text-xs text-gray-700 backdrop-blur-md animate-in fade-in">
            {attachedFile.isImage ? (
              <img
                src={attachedFile.dataUrl}
                alt="Upload preview"
                className="h-9 w-9 rounded-lg object-cover border border-primary-200"
              />
            ) : (
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-100 text-base">
                📄
              </span>
            )}
            <div className="flex flex-col flex-1 overflow-hidden">
              <span className="font-semibold text-primary-700 truncate">{attachedFile.name}</span>
              <span className="text-ink-500 text-[11px]">
                {attachedFile.size} • Multimodal attachment ready
              </span>
            </div>
            <button
              type="button"
              onClick={handleRemoveFile}
              className="rounded-full p-1 text-ink-500 hover:bg-soft hover:text-ink-900 transition-colors"
              title="Remove attached file"
            >
              ✕
            </button>
          </div>
        )}

        {/* Search Input */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleVerify();
          }}
          className="relative flex flex-col md:flex-row gap-3"
        >
          <div className="relative flex-1 flex items-center">
            <input
              id="ask-agent-input"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                attachedFile
                  ? "Add additional notes (optional)..."
                  : "e.g. 'Standard Bank loan promotion SMS' or upload screenshot..."
              }
              disabled={loading}
              autoFocus={!!initialContent}
              className="w-full rounded-2xl border border-border bg-surface pl-5 pr-14 py-4 text-sm md:text-base text-ink-900 placeholder-ink-500 shadow-inner focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/30 transition-all disabled:opacity-50"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
              className="absolute right-3 p-2 rounded-xl text-ink-500 hover:bg-soft hover:text-primary-600 transition-colors"
              title="Upload file or screenshot"
            >
              <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
              </svg>
            </button>
          </div>

          <button
            id="ask-agent-verify-button"
            type="submit"
            disabled={loading || (!query.trim() && !attachedFile)}
            className="flex items-center justify-center gap-2 rounded-2xl bg-linear-to-r from-primary-500 via-primary-600 to-primary-700 px-7 py-4 font-bold text-white shadow-lg shadow-primary-500/30 hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <svg className="h-5 w-5 animate-spin text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Analyzing Evidence…</span>
              </>
            ) : (
              <>
                <span>Verify Claim</span>
                <span className="text-lg">🔍</span>
              </>
            )}
          </button>
        </form>

        {/* Sample prompts */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-ink-700">Try testing:</span>
            {SAMPLE_CLAIMS.map((claim, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleVerify(claim)}
                disabled={loading}
                className="rounded-full border border-border bg-soft px-3 py-1 text-xs text-ink-700 hover:border-primary-300 hover:bg-background hover:text-ink-900 transition-all disabled:opacity-50"
              >
                &ldquo;{claim.length > 30 ? claim.slice(0, 30) + "…" : claim}&rdquo;
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="text-xs text-primary-500 hover:underline font-medium flex items-center gap-1"
          >
            <span>📁 Upload local file/image</span>
          </button>
        </div>
      </div>
    </div>
  );
}
