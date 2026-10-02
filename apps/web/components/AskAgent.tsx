"use client";

import { useState, useRef, useEffect } from "react";
import {
  verifyClaim,
  askVerificationFollowup,
  ReportAskMessage,
} from "@/lib/api";
import { VerificationResult } from "@/lib/types";
import {
  Bot,
  Send,
  User,
  Sparkles,
  RefreshCw,
  ExternalLink,
  HelpCircle,
  Paperclip,
  X,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  ShieldCheck,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Source = NonNullable<VerificationResult["sources"]>[number];

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  timestamp: string;
  // Verdict data (populated only on the first verification response)
  claimVerdict?: VerificationResult["claim_verdict"];
  legacyVerdict?: VerificationResult["verdict"];
  riskLevel?: VerificationResult["risk_level"];
  confidenceScore?: number;
  isVerificationResult?: boolean;
  // Clarification request data
  isClarificationRequest?: boolean;
  clarificationQuestion?: string;
  clarificationSuggestions?: { label: string; query: string }[];
}

interface AttachedFile {
  name: string;
  size: string;
  dataUrl: string;
  isImage: boolean;
  isAudio: boolean;
}

// ---------------------------------------------------------------------------
// Vague query detection + Malawi-context disambiguation
// ---------------------------------------------------------------------------

interface ClarificationResult {
  isVague: boolean;
  question: string;
  suggestions: { label: string; query: string }[];
}

// Context seeds — Malawi-first, then regional/global generic expansions
const CONTEXT_SEEDS: {
  keywords: string[];
  suggestions: { label: string; query: string }[];
  question: string;
}[] = [
  {
    keywords: ["plane", "crash", "aircraft", "helicopter", "plane crash"],
    question: "Which plane crash are you referring to? Here are some I can look into:",
    suggestions: [
      { label: "✈️ Malawi: VP Saulos Chilima plane crash — June 2024", query: "Malawi Vice President Saulos Chilima plane crash June 2024" },
      { label: "✈️ Malawi: Presidential plane crash Mchinji June 10 2024", query: "Malawi government plane crash Mchinji June 10 2024" },
      { label: "✈️ Other plane crash (type location or name below)", query: "plane crash" },
    ],
  },
  {
    keywords: ["election", "vote", "voting", "ballot", "polling"],
    question: "Which election would you like me to verify information about?",
    suggestions: [
      { label: "🗳️ Malawi 2025 General Elections", query: "Malawi 2025 general elections" },
      { label: "🗳️ Malawi 2020 Constitutional Court election ruling", query: "Malawi 2020 fresh elections constitutional court" },
      { label: "🗳️ Other election (add country or date below)", query: "election" },
    ],
  },
  {
    keywords: ["flood", "flooding", "cyclone", "storm", "disaster"],
    question: "Which natural disaster event are you asking about?",
    suggestions: [
      { label: "🌊 Malawi Cyclone Freddy 2023 — Southern Region", query: "Malawi Cyclone Freddy 2023 floods Southern Region" },
      { label: "🌊 Malawi 2024 floods Blantyre and Zomba", query: "Malawi 2024 floods Blantyre Zomba" },
      { label: "🌊 Other disaster (add location or date below)", query: "flood disaster" },
    ],
  },
  {
    keywords: ["president", "mcp", "chakwera", "government", "minister"],
    question: "What would you like to verify about the Malawi government?",
    suggestions: [
      { label: "🏛️ Lazarus Chakwera presidency allegations", query: "Malawi President Lazarus Chakwera allegations" },
      { label: "🏛️ Malawi government corruption claims", query: "Malawi government corruption 2024" },
      { label: "🏛️ Specific minister or policy (type name below)", query: "Malawi government" },
    ],
  },
  {
    keywords: ["scam", "fraud", "mobile money", "airtel money", "m-pesa", "momo", "loan", "bank"],
    question: "Which scam or fraud claim are you checking?",
    suggestions: [
      { label: "💸 Airtel Money PIN scam messages circulating", query: "Airtel Money PIN scam Malawi" },
      { label: "💸 Standard Bank WhatsApp loan scam", query: "Standard Bank WhatsApp loan scam Malawi" },
      { label: "💸 Reserve Bank crypto/investment warning", query: "Reserve Bank Malawi unlicensed crypto investment warning" },
    ],
  },
];

const VAGUE_QUESTION_OPENERS = [
  "is there", "did you hear", "have you seen", "is it true", "what happened",
  "any news", "any update", "any video", "any proof", "any evidence",
  "do you know", "can you check", "tell me about", "what about",
];

function detectVagueQuery(text: string): ClarificationResult {
  const lower = text.toLowerCase().trim();
  const wordCount = lower.split(/\s+/).length;

  // Check keyword seeds first (regardless of length)
  for (const seed of CONTEXT_SEEDS) {
    const matched = seed.keywords.some((kw) => lower.includes(kw));
    if (matched) {
      // Only intercept if vague (no specific person/place/date attached)
      const hasSpecific = /\d{4}|malawi|blantyre|lilongwe|mchinji|zomba|[A-Z][a-z]+ [A-Z][a-z]+/.test(text);
      if (!hasSpecific || VAGUE_QUESTION_OPENERS.some((op) => lower.startsWith(op))) {
        return {
          isVague: true,
          question: seed.question,
          suggestions: seed.suggestions,
        };
      }
    }
  }

  // Generic vagueness: very short or opens with a vague question
  const startsVague = VAGUE_QUESTION_OPENERS.some((op) => lower.startsWith(op));
  if (wordCount <= 3 || (startsVague && wordCount <= 7)) {
    return {
      isVague: true,
      question: "Could you be more specific? To give you an accurate verdict I need a bit more detail:",
      suggestions: [
        { label: "📍 Add a location (e.g. Malawi, Blantyre…)", query: text + " in Malawi" },
        { label: "👤 Add a person or organisation involved", query: text },
        { label: "📅 Add a date or timeframe (e.g. 2024)", query: text + " 2024" },
      ],
    };
  }

  return { isVague: false, question: "", suggestions: [] };
}

// ---------------------------------------------------------------------------
// Clarification bubble component
// ---------------------------------------------------------------------------

function ClarificationBubble({
  msg,
  onSelect,
}: {
  msg: ChatMessage;
  onSelect: (query: string) => void;
}) {
  return (
    <div className="flex flex-col gap-2.5 w-full">
      {/* Question */}
      <div className="bg-white border border-sky-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm space-y-2.5">
        <p className="text-[12px] font-semibold text-sky-700 flex items-center gap-1.5">
          <HelpCircle className="w-3.5 h-3.5 shrink-0" />
          {msg.clarificationQuestion}
        </p>
        <div className="flex flex-col gap-1.5">
          {(msg.clarificationSuggestions ?? []).map((s, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onSelect(s.query)}
              className="text-left w-full px-3 py-2 rounded-xl bg-sky-50 hover:bg-sky-100 border border-sky-200 hover:border-sky-400 text-[12px] font-medium text-sky-800 transition-all flex items-center justify-between gap-2 group"
            >
              <span>{s.label}</span>
              <Send className="w-3 h-3 text-sky-400 group-hover:text-sky-600 shrink-0" />
            </button>
          ))}
        </div>
        <p className="text-[10px] text-ink-400 pt-0.5">
          Or type more detail in the box below for a precise result.
        </p>
      </div>
    </div>
  );
}


const SAMPLE_CLAIMS = [
  "Lion escaped Kasungu game reserve attacking people",
  "Standard Bank offering WhatsApp collateral-free loans",
  "Reserve Bank warns against unlicensed crypto trading",
  "Airtel Money asking for secret PIN over the phone",
];

// ---------------------------------------------------------------------------
// Verdict metadata — tone, copy and visuals per verdict type
// ---------------------------------------------------------------------------

type VerdictType = "true" | "false" | "pending" | "misleading" | "partly";

interface VerdictMeta {
  type: VerdictType;
  label: string;
  color: string;
  bg: string;
  border: string;
  icon: React.ReactNode;
  // Contextual intro line shown before the summary
  introLine: string;
  // Short disclaimer / context note shown below the summary
  contextNote: string;
  // Animated "pulse" indicator for developing stories
  pulse?: boolean;
}

function getVerdictMeta(claimVerdict?: string, legacyVerdict?: string): VerdictMeta {
  const v = claimVerdict?.toLowerCase() ?? legacyVerdict?.toLowerCase() ?? "";

  if (v.includes("true") || (v.includes("confirmed") && !v.includes("scam"))) {
    return {
      type: "true",
      label: "TRUE",
      color: "text-emerald-700",
      bg: "bg-emerald-50",
      border: "border-emerald-300",
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-600" />,
      introLine: "VeriFeed has found credible, corroborated evidence supporting this claim.",
      contextNote: "Multiple sources independently confirm the key facts. Always verify through official channels before acting.",
    };
  }
  if (v.includes("false") || v.includes("scam") || v.includes("disputed") || v.includes("fraudulent")) {
    return {
      type: "false",
      label: "FALSE",
      color: "text-red-700",
      bg: "bg-red-50",
      border: "border-red-300",
      icon: <XCircle className="w-5 h-5 text-red-600" />,
      introLine: "VeriFeed has found strong evidence that this claim is false or fraudulent.",
      contextNote: "⚠️ Do not share, click any links, or send money. Report to authorities if you received this as a message.",
    };
  }
  if (v.includes("misleading")) {
    return {
      type: "misleading",
      label: "MISLEADING",
      color: "text-orange-700",
      bg: "bg-orange-50",
      border: "border-orange-300",
      icon: <AlertTriangle className="w-5 h-5 text-orange-600" />,
      introLine: "VeriFeed has found that this claim contains a mix of facts and distortions.",
      contextNote: "The core story may have a basis in reality, but key details are exaggerated, taken out of context, or selectively omitted.",
    };
  }
  if (v.includes("partly")) {
    return {
      type: "partly",
      label: "PARTLY TRUE",
      color: "text-amber-700",
      bg: "bg-amber-50",
      border: "border-amber-300",
      icon: <AlertTriangle className="w-5 h-5 text-amber-600" />,
      introLine: "VeriFeed has found that some parts of this claim are accurate, while others are not.",
      contextNote: "Treat with caution — partial truths can be as misleading as outright falsehoods. Cross-check specifics before sharing.",
    };
  }
  // Default → pending / developing / unconfirmed
  return {
    type: "pending",
    label: "PENDING REVIEW",
    color: "text-sky-700",
    bg: "bg-sky-50",
    border: "border-sky-300",
    icon: <Clock className="w-5 h-5 text-sky-500 animate-pulse" />,
    introLine: "VeriFeed has found early reports on this — however the full picture is still emerging.",
    contextNote: "This appears to be a developing story. Available sources are limited or conflicting, and the real truth has not yet been independently established. We recommend monitoring trusted news outlets for updates before acting on or sharing this claim.",
    pulse: true,
  };
}

// ---------------------------------------------------------------------------
// Structured, interactive verification response card
// ---------------------------------------------------------------------------

function VerificationCard({ msg }: { msg: ChatMessage }) {
  const meta = getVerdictMeta(msg.claimVerdict, msg.legacyVerdict);

  return (
    <div className="flex flex-col gap-3 w-full">

      {/* Full-width verdict badge */}
      <div className={`flex items-center justify-between gap-3 w-full px-4 py-3 rounded-xl border ${meta.bg} ${meta.border}`}>
        <div className="flex items-center gap-2.5">
          {/* Pulse dot for developing stories */}
          {meta.pulse && (
            <span className="relative flex h-2.5 w-2.5 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-sky-500" />
            </span>
          )}
          {meta.icon}
          <span className="text-[11px] font-bold uppercase tracking-widest text-ink-500">Verdict:</span>
          <span className={`text-[15px] font-black tracking-tight leading-none ${meta.color}`}>{meta.label}</span>
        </div>
        {msg.confidenceScore !== undefined && (
          <span className="px-2.5 py-1 rounded-full bg-white/80 border border-black/10 text-[11px] font-bold text-ink-600 shrink-0">
            {msg.confidenceScore}% confident
          </span>
        )}
      </div>

      {/* Contextual intro + AI summary */}
      <div className="bg-white border border-border rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm space-y-2">
        {/* Intro line — verdict-specific tone */}
        <p className={`text-[12px] font-semibold flex items-center gap-1.5 ${
          meta.type === "false" ? "text-red-600" :
          meta.type === "pending" ? "text-sky-600" :
          meta.type === "misleading" ? "text-orange-600" :
          meta.type === "partly" ? "text-amber-600" :
          "text-primary-700"
        }`}>
          <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
          {meta.introLine}
        </p>

        {/* Divider */}
        <div className="border-t border-border" />

        {/* Full AI summary */}
        <div className="text-[13px] leading-relaxed text-ink-800 whitespace-pre-wrap">{msg.content}</div>

        {/* Context note — always shown */}
        <div className={`mt-1 rounded-lg px-3 py-2 text-[11px] leading-snug ${
          meta.type === "false"   ? "bg-red-50 text-red-700 border border-red-200" :
          meta.type === "pending" ? "bg-sky-50 text-sky-700 border border-sky-200" :
          meta.type === "misleading" ? "bg-orange-50 text-orange-700 border border-orange-200" :
          meta.type === "partly" ? "bg-amber-50 text-amber-700 border border-amber-200" :
          "bg-emerald-50 text-emerald-700 border border-emerald-200"
        }`}>
          {meta.contextNote}
        </div>
      </div>

      {/* Evidence sources */}
      {msg.sources && msg.sources.length > 0 ? (
        <div className="w-full space-y-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-ink-500 block px-1">
            📰 Evidence Sources — you can check them below
          </span>
          <div className="grid grid-cols-1 gap-1.5">
            {msg.sources.map((src, i) => (
              <a
                key={i}
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-white border border-border hover:border-primary-300 hover:shadow-sm transition-all group"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-primary-100 text-primary-700 border border-primary-200 shrink-0">
                      {src.outlet || "Source"}
                    </span>
                    {src.type && (
                      <span className="text-[9px] text-ink-400 truncate hidden sm:block">{src.type}</span>
                    )}
                  </div>
                  <p className="text-[11px] font-semibold text-ink-800 line-clamp-1 group-hover:text-primary-700 transition-colors">{src.title}</p>
                </div>
                <ExternalLink className="w-3 h-3 text-ink-400 group-hover:text-primary-600 shrink-0" />
              </a>
            ))}
          </div>
        </div>
      ) : (
        /* No sources found — explain why (especially relevant for PENDING) */
        <div className="rounded-xl border border-dashed border-border px-4 py-3 text-[11px] text-ink-500 text-center">
          {meta.type === "pending"
            ? "📡 No confirmed sources found yet. This may be breaking news or an unverified rumour — VeriFeed will surface evidence as it becomes available."
            : "No linked sources were returned for this verification."}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Plain source links (follow-up answers)
// ---------------------------------------------------------------------------

function SourceLinks({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;

  return (
    <div className="w-full space-y-1.5">
      <span className="text-[10px] font-bold uppercase tracking-wider text-ink-500 block px-1">
        📰 Sources
      </span>
      <div className="grid grid-cols-1 gap-1.5">
        {sources.map((src, i) => (
          <a
            key={i}
            href={src.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-white border border-border hover:border-primary-300 hover:shadow-sm transition-all group"
          >
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 mb-0.5">
                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-primary-100 text-primary-700 border border-primary-200 shrink-0">
                  {src.outlet || "Source"}
                </span>
                {src.type && (
                  <span className="text-[9px] text-ink-400 truncate hidden sm:block">
                    {src.type}
                  </span>
                )}
              </div>
              <p className="text-[11px] font-semibold text-ink-800 line-clamp-1 group-hover:text-primary-700 transition-colors">
                {src.title}
              </p>
            </div>
            <ExternalLink className="w-3 h-3 text-ink-400 group-hover:text-primary-600 shrink-0" />
          </a>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main AskAgent widget
// ---------------------------------------------------------------------------

export function AskAgent() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState<AttachedFile | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [activeReportId, setActiveReportId] = useState<string | number | null>(
    null,
  );
  const [chatHistory, setChatHistory] = useState<ReportAskMessage[]>([]);
  const [showSamples, setShowSamples] = useState(true);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  // Initial welcome message
  useEffect(() => {
    const ts = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content:
          "Hello! I'm VeriFeed AI — your real-time claim verification assistant.\n\nPaste any rumour, WhatsApp forward, scam message, or headline below and I'll check it against news sources, official registries, and fact-checkers instantly.\n\nYou can also upload a screenshot or voice note 📎",
        timestamp: ts,
      },
    ]);
  }, []);

  // File handling
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const size =
      file.size > 1024 * 1024
        ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
        : `${Math.round(file.size / 1024)} KB`;
    const isImage = file.type.startsWith("image/");
    const isAudio =
      file.type.startsWith("audio/") ||
      /\.(mp3|wav|m4a|ogg|aac|flac|opus)$/i.test(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      setAttachedFile({
        name: file.name,
        size,
        dataUrl: reader.result as string,
        isImage,
        isAudio,
      });
    };
    reader.readAsDataURL(file);
  };

  const removeFile = () => {
    setAttachedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Unified send handler — initial verify OR follow-up question
  const handleSend = async (textOverride?: string) => {
    const text = (textOverride !== undefined ? textOverride : input).trim();
    if (!text && !attachedFile) return;
    if (loading) return;

    setShowSamples(false);
    const ts = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text || `[Attached: ${attachedFile?.name}]`,
      timestamp: ts,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const newHistory: ReportAskMessage[] = [
      ...chatHistory,
      { role: "user", content: userMsg.content },
    ];

    try {
      let aiContent = "";
      let sources: Source[] | undefined;
      let newSuggestions: string[] = [];
      const verdictData: Partial<ChatMessage> = {};

      if (!activeReportId) {
        // ── Check for vague / ambiguous query first ──────────────────────
        const clarification = detectVagueQuery(text);
        if (clarification.isVague) {
          setLoading(false);
          const clarTs = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
          setMessages((prev) => [
            ...prev,
            {
              id: `clar-${Date.now()}`,
              role: "assistant",
              content: "",
              timestamp: clarTs,
              isClarificationRequest: true,
              clarificationQuestion: clarification.question,
              clarificationSuggestions: clarification.suggestions,
            },
          ]);
          inputRef.current?.focus();
          return;
        }

        // ── First message: full verification ────────────────────────────
        const res = await verifyClaim(
          text,
          attachedFile?.isImage ? attachedFile.dataUrl : null,
          attachedFile?.name || null,
          null,
          attachedFile?.isAudio ? attachedFile.dataUrl : null,
          attachedFile?.isAudio ? attachedFile.name : null,
        );
        removeFile();

        if (res) {
          setActiveReportId(res.id);
          aiContent =
            res.summary?.trim() ||
            "Verification complete, but no summary was returned.";
          sources = res.sources?.slice(0, 4) ?? [];
          Object.assign(verdictData, {
            claimVerdict: res.claim_verdict,
            legacyVerdict: res.verdict,
            riskLevel: res.risk_level,
            confidenceScore: res.confidence_score,
            isVerificationResult: true,
          });
          newSuggestions = [
            "What specific red flags were found?",
            "How do I report this to authorities?",
            "What should I do if I already clicked the link?",
            "How can I verify the official contact for this institution?",
          ];
        } else {
          aiContent =
            "I was unable to complete the verification. Please check your connection and try again.";
        }
      } else {
        // ── Follow-up question ───────────────────────────────────────────
        const res = await askVerificationFollowup(
          activeReportId,
          text,
          chatHistory,
        );
        if (res?.answer) {
          aiContent = res.answer;
          if (res.suggested_followups?.length) {
            newSuggestions = res.suggested_followups;
          }
        } else {
          aiContent =
            "I couldn't retrieve an answer right now. Try rephrasing your question.";
        }
      }

      const aiTs = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: aiContent,
        sources,
        timestamp: aiTs,
        ...verdictData,
      };

      setChatHistory([
        ...newHistory,
        { role: "assistant", content: aiContent },
      ]);
      setMessages((prev) => [...prev, aiMsg]);
      if (newSuggestions.length) setSuggestions(newSuggestions);
    } catch (err) {
      console.error("AskAgent error:", err);
      const errTs = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: "Something went wrong. Please try again.",
          timestamp: errTs,
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  // Reset to verify a new claim
  const handleNewVerification = () => {
    setActiveReportId(null);
    setChatHistory([]);
    setSuggestions([]);
    setShowSamples(true);
    const ts = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    setMessages([
      {
        id: `reset-${Date.now()}`,
        role: "assistant",
        content:
          "Ready to verify a new claim! Paste any message, headline, or rumour below.",
        timestamp: ts,
      },
    ]);
  };

  return (
    <div
      id="ask-agent-widget"
      className="relative w-full overflow-hidden rounded-3xl border border-border bg-white shadow-2xl shadow-primary-500/8 flex flex-col"
      style={{ minHeight: 560, maxHeight: "85vh" }}
    >
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        accept="image/*,audio/*,.mp3,.wav,.m4a,.ogg,.aac"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="bg-gradient-to-r from-primary-900 via-primary-800 to-primary-900 px-5 py-3.5 flex items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="relative shrink-0">
            <img
              src="/verifeed_ai_bot.png"
              alt="VeriFeed AI"
              className="h-9 w-9 rounded-xl object-cover border border-primary-500/60 shadow"
            />
            <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-emerald-400 border-2 border-primary-900" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white tracking-tight">
                VeriFeed AI
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-white/10 border border-white/15 text-primary-300">
                <Sparkles className="w-2.5 h-2.5 text-emerald-400" />
                Verification Agent
              </span>
            </div>
            <p className="text-[10px] text-white/60 mt-0.5">
              {activeReportId
                ? `Report #${activeReportId} active — ask follow-up questions below`
                : "Ask me to verify any claim, rumour, or scam message"}
            </p>
          </div>
        </div>

        {activeReportId && (
          <button
            type="button"
            onClick={handleNewVerification}
            className="shrink-0 text-[11px] font-bold uppercase tracking-wide px-3 py-1.5 rounded-lg bg-white/10 border border-white/20 text-white hover:bg-white/20 transition-all"
          >
            + New Check
          </button>
        )}
      </div>

      {/* ── Chat thread ─────────────────────────────────────────────────── */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-4 bg-gray-50/60 scrollbar-thin"
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-2.5 ${
              msg.role === "user" ? "justify-end" : "justify-start"
            } w-full animate-in fade-in slide-in-from-bottom-1 duration-200`}
          >
            {msg.role === "assistant" && (
              <div className="h-7 w-7 rounded-xl bg-primary-100 border border-primary-200 flex items-center justify-center shrink-0 mt-1">
                <Bot className="w-3.5 h-3.5 text-primary-700" />
              </div>
            )}

            <div
              className={`flex flex-col gap-1.5 ${
                msg.role === "user"
                  ? "items-end max-w-[80%]"
                  : "items-start max-w-[88%]"
              }`}
            >
              {/* Clarification bubble / Verification card / Plain bubble */}
              {msg.role === "assistant" && msg.isClarificationRequest ? (
                <ClarificationBubble msg={msg} onSelect={(q) => handleSend(q)} />
              ) : msg.role === "assistant" && msg.isVerificationResult ? (
                <VerificationCard msg={msg} />
              ) : (
                <>
                  <div
                    className={`rounded-2xl px-4 py-2.5 text-[13px] leading-relaxed ${
                      msg.role === "user"
                        ? "bg-primary-600 text-white rounded-br-sm"
                        : "bg-white border border-border text-ink-800 rounded-bl-sm shadow-sm"
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  </div>

                  {/* Source links for follow-up answers */}
                  {msg.role === "assistant" &&
                    msg.sources &&
                    msg.sources.length > 0 && <SourceLinks sources={msg.sources} />}
                </>
              )}

              <span className="text-[10px] text-ink-400 font-mono px-1">
                {msg.timestamp}
              </span>
            </div>

            {msg.role === "user" && (
              <div className="h-7 w-7 rounded-xl bg-primary-600 text-white flex items-center justify-center shrink-0 mt-1">
                <User className="w-3.5 h-3.5" />
              </div>
            )}
          </div>
        ))}

        {/* Typing / loading indicator */}
        {loading && (
          <div className="flex gap-2.5 justify-start animate-in fade-in">
            <div className="h-7 w-7 rounded-xl bg-primary-100 border border-primary-200 flex items-center justify-center shrink-0">
              <Bot className="w-3.5 h-3.5 text-primary-700" />
            </div>
            <div className="bg-white border border-border rounded-2xl rounded-bl-sm px-4 py-3 text-[12px] text-ink-500 flex items-center gap-2 shadow-sm">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-primary-500" />
              <span>
                {activeReportId
                  ? "Looking up answer…"
                  : "Analyzing claim against sources…"}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* ── Sample prompts (shown before first verify) ──────────────────── */}
      {showSamples && (
        <div className="px-4 py-2.5 bg-white border-t border-border flex flex-wrap items-center gap-1.5 shrink-0">
          <HelpCircle className="w-3 h-3 text-ink-400 shrink-0" />
          <span className="text-[10px] text-ink-400 font-semibold uppercase tracking-wide mr-1">
            Try:
          </span>
          {SAMPLE_CLAIMS.map((claim, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleSend(claim)}
              disabled={loading}
              className="text-[11px] text-primary-800 bg-primary-50 hover:bg-primary-100 border border-primary-200 px-2.5 py-1 rounded-full transition-all disabled:opacity-50 font-medium truncate max-w-[200px]"
            >
              {claim.length > 36 ? claim.slice(0, 36) + "…" : claim}
            </button>
          ))}
        </div>
      )}

      {/* ── Follow-up suggestion pills ───────────────────────────────────── */}
      {!showSamples && suggestions.length > 0 && (
        <div className="px-4 py-2 bg-white border-t border-border flex flex-wrap items-center gap-1.5 shrink-0">
          <HelpCircle className="w-3 h-3 text-ink-400 shrink-0" />
          {suggestions.slice(0, 3).map((sug, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleSend(sug)}
              disabled={loading}
              className="text-[11px] text-primary-800 bg-primary-50 hover:bg-primary-100 border border-primary-200 px-2.5 py-1 rounded-full transition-all disabled:opacity-50 font-medium truncate max-w-[240px]"
            >
              {sug}
            </button>
          ))}
        </div>
      )}

      {/* ── Attached file chip ───────────────────────────────────────────── */}
      {attachedFile && (
        <div className="px-4 py-2 bg-primary-50 border-t border-primary-200 flex items-center gap-3 shrink-0">
          {attachedFile.isImage ? (
            <img
              src={attachedFile.dataUrl}
              alt=""
              className="h-8 w-8 rounded-lg object-cover border border-primary-200"
            />
          ) : (
            <span className="h-8 w-8 flex items-center justify-center rounded-lg bg-primary-100 text-lg">
              {attachedFile.isAudio ? "🎙️" : "📄"}
            </span>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-[12px] font-semibold text-primary-800 truncate">
              {attachedFile.name}
            </p>
            <p className="text-[10px] text-ink-500">{attachedFile.size}</p>
          </div>
          <button
            type="button"
            onClick={removeFile}
            className="p-1 rounded-full hover:bg-primary-100 text-ink-500 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* ── Input bar ────────────────────────────────────────────────────── */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="px-3 py-3 bg-white border-t border-border flex items-center gap-2 shrink-0"
      >
        {/* Attachment trigger */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          title="Attach image or voice note"
          className="flex items-center justify-center h-10 w-10 rounded-xl border border-border bg-gray-50 hover:bg-primary-50 hover:border-primary-300 text-ink-500 hover:text-primary-600 transition-all disabled:opacity-40 shrink-0"
        >
          <Paperclip className="w-4 h-4" />
        </button>

        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            activeReportId
              ? "Ask a follow-up question about this report…"
              : "Paste a claim, rumour, or scam message to verify…"
          }
          disabled={loading}
          className="flex-1 rounded-2xl border border-border bg-gray-50 px-4 py-2.5 text-[13px] text-ink-900 placeholder-ink-400 focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-400/20 transition-all disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={loading || (!input.trim() && !attachedFile)}
          className="flex items-center justify-center gap-1.5 h-10 rounded-xl bg-primary-600 hover:bg-primary-700 px-4 text-[12px] font-bold text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
        >
          {loading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </form>
    </div>
  );
}
