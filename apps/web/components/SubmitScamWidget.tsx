"use client";

import { useState, useRef } from "react";
import { submitScamReport } from "@/lib/api";

interface AttachedFile {
  name: string;
  size: string;
  dataUrl: string;
  isImage: boolean;
}

export function SubmitScamWidget() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState<AttachedFile | null>(null);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const sizeFormatted = file.size > 1024 * 1024
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
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async () => {
    if (!text.trim() && !attachedFile) return;

    setLoading(true);
    setError("");
    setSuccess(false);

    const isSuccess = await submitScamReport(
      text.trim(),
      attachedFile?.dataUrl || null
    );

    setLoading(false);

    if (isSuccess) {
      setSuccess(true);
      setText("");
      handleRemoveFile();
      setTimeout(() => setSuccess(false), 5000);
    } else {
      setError("Failed to submit report. Please try again.");
    }
  };

  return (
    <div className="relative w-full overflow-hidden rounded-3xl border border-red-200 bg-linear-to-br from-white via-gray-50 to-white p-6 md:p-8 shadow-2xl shadow-red-100 backdrop-blur-xl mb-12">
      <input
        type="file"
        ref={fileInputRef}
        accept="image/*,.txt,.csv,.json"
        onChange={handleFileSelect}
        className="hidden"
      />

      <div className="relative flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-linear-to-tr from-red-500 to-orange-500 text-xl font-bold text-white shadow-lg shadow-red-500/30">
            ⚠️
          </span>
          <div>
            <h2 className="text-lg md:text-xl font-bold text-foreground tracking-tight">
              Report a New Scam
            </h2>
            <p className="text-xs md:text-sm text-gray-600">
              Received a suspicious SMS, email, or post? Upload a screenshot or paste the text to help us track emerging fraud.
            </p>
          </div>
        </div>

        {error && (
          <div className="text-xs font-semibold text-danger bg-danger/10 px-3 py-2 rounded-lg border border-danger/20">
            {error}
          </div>
        )}

        {success && (
          <div className="text-xs font-semibold text-success bg-success/10 px-3 py-2 rounded-lg border border-success/20">
            ✅ Thank you! Your report has been submitted and is being analyzed by our AI for clustering.
          </div>
        )}

        {/* Attached File Preview */}
        {attachedFile && (
          <div className="flex items-center gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-2.5 text-xs text-gray-700 backdrop-blur-md animate-in fade-in">
            {attachedFile.isImage ? (
              <img
                src={attachedFile.dataUrl}
                alt="Upload preview"
                className="h-9 w-9 rounded-lg object-cover border border-red-200"
              />
            ) : (
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-100 text-base">
                📄
              </span>
            )}
            <div className="flex flex-col flex-1 overflow-hidden">
              <span className="font-semibold text-red-700 truncate">
                {attachedFile.name}
              </span>
              <span className="text-ink-500 text-[11px]">
                {attachedFile.size} • Ready for OCR extraction
              </span>
            </div>
            <button
              type="button"
              onClick={handleRemoveFile}
              className="rounded-full p-1 text-ink-500 hover:bg-soft hover:text-ink-900 transition-colors"
            >
              ✕
            </button>
          </div>
        )}

        {/* Input area */}
        <div className="flex flex-col gap-3">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste the exact text of the message, or upload a screenshot..."
            disabled={loading}
            rows={3}
            className="w-full rounded-2xl border border-border bg-surface p-4 text-sm md:text-base text-ink-900 placeholder-ink-500 shadow-inner focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/30 transition-all disabled:opacity-50 resize-none"
          />

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
              className="flex items-center gap-2 rounded-xl border border-border bg-soft px-4 py-2 text-sm font-semibold text-ink-700 hover:text-ink-900 hover:bg-background transition-colors"
            >
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
              </svg>
              Attach Screenshot
            </button>

            <button
              onClick={handleSubmit}
              disabled={loading || (!text.trim() && !attachedFile)}
              className="flex items-center justify-center gap-2 rounded-xl bg-linear-to-r from-red-500 to-orange-500 px-6 py-2.5 font-bold text-white shadow-lg shadow-red-500/30 hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-red-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <svg className="h-4 w-4 animate-spin text-white" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <span>Submitting...</span>
                </>
              ) : (
                <span>Submit Report</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
