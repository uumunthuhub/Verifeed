"use client";

import React, { useState, useRef, useEffect } from "react";
import { askVerificationFollowup, ReportAskMessage } from "@/lib/api";
import { Bot, Send, Sparkles, User, RefreshCw, AlertCircle, HelpCircle } from "lucide-react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

interface ReportAskAgentProps {
  reportId: string | number;
  query?: string;
  verdict?: string;
  claimVerdict?: string;
  messageAuthenticityVerdict?: string;
  riskLevel?: "High" | "Medium" | "Low";
  summary?: string;
  recommendedActions?: Array<{
    action: string;
    priority: string;
    reason?: string;
  }>;
  extractedEntities?: {
    sender?: string;
    phone_numbers?: string[];
    urls?: string[];
    institution_names?: string[];
  };
}

const DEFAULT_SUGGESTIONS = [
  "What specific red flags were found in this message?",
  "How can I safely report this scam to authorities?",
  "What should I do if I already clicked the link or provided details?",
  "How can I verify the official support number for this institution?",
];

export function ReportAskAgent({
  reportId,
  query,
  verdict,
  claimVerdict,
  messageAuthenticityVerdict,
  riskLevel = "Medium",
  summary,
  recommendedActions,
  extractedEntities,
}: ReportAskAgentProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>(DEFAULT_SUGGESTIONS);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize initial welcoming AI context message
  useEffect(() => {
    const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    
    let welcomeText = `Hello! I am your **VeriFeed AI Verification Assistant**. VeriFeed has found evidence regarding this claim or question for Report **#${reportId}**:\n\n`;

    if (summary) {
      welcomeText += `> "${summary}"\n\n`;
    }

    if (riskLevel === "High") {
      welcomeText += `⚠️ **Risk Warning**: This claim/message has been flagged as **High Risk** (${
        verdict || claimVerdict || "High Risk Scam"
      }). You can ask me follow-up questions about red flags, how to protect your money/credentials, or how to contact official institutions safely.`;
    } else if (riskLevel === "Low") {
      welcomeText += `✅ **Low Risk / Official Match**: This message has passed authenticity checks. Ask me any follow-up questions if you want to verify official contact channels or understand the evidence.`;
    } else {
      welcomeText += `ℹ️ **Medium Risk / Unconfirmed**: This claim requires caution. Ask me follow-up questions to explore what evidence is missing or how to verify it independently.`;
    }

    setMessages([
      {
        id: "welcome-1",
        role: "assistant",
        content: welcomeText,
        timestamp: timeStr,
      },
    ]);
  }, [reportId, riskLevel, verdict, claimVerdict, summary]);

  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat thread to bottom when messages change
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [messages, loading]);


  const handleSend = async (textToSend?: string) => {
    const questionText = textToSend !== undefined ? textToSend : input;
    if (!questionText.trim() || loading) return;

    const userTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: questionText.trim(),
      timestamp: userTime,
    };

    setMessages((prev) => [...prev, userMsg]);
    if (textToSend === undefined) setInput("");
    setLoading(true);

    // Format chat history for API context
    const historyPayload: ReportAskMessage[] = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const res = await askVerificationFollowup(reportId, questionText.trim(), historyPayload);
      const aiTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      if (res && res.answer) {
        let answerText = res.answer;
        if (!answerText.toLowerCase().includes("verifeed has found evidence")) {
          answerText = `VeriFeed has found evidence regarding this claim or question:\n\n${answerText}`;
        }

        setMessages((prev) => [
          ...prev,
          {
            id: `ai-${Date.now()}`,
            role: "assistant",
            content: answerText,
            timestamp: aiTime,
          },
        ]);
        if (res.suggested_followups && res.suggested_followups.length > 0) {
          setSuggestions(res.suggested_followups);
        }
      } else {
        // Fallback grounded answer
        let fallback = `VeriFeed has found evidence regarding this claim or question:\n\nBased on the findings in Report #${reportId}, `;
        if (riskLevel === "High") {
          fallback += `this claim is high risk. Do not share any secret PINs, bank details, or send mobile money fees. Contact official support numbers directly.`;
        } else {
          fallback += `we recommend cross-checking any claims with official disclaimers or verified news outlets before taking action.`;
        }

        setMessages((prev) => [
          ...prev,
          {
            id: `ai-${Date.now()}`,
            role: "assistant",
            content: fallback,
            timestamp: aiTime,
          },
        ]);
      }
    } catch (err) {
      console.error("Error in interactive report Q&A:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div id="report-ai-widget" className="mt-8 rounded-2xl border border-primary-200/80 bg-white shadow-xl overflow-hidden transition-all">

      {/* Compact Stylish Header */}
      <div className="bg-linear-to-r from-primary-900 via-primary-800 to-primary-900 px-4 py-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="relative shrink-0">
            <img
              src="/verifeed_ai_bot.png"
              alt="VeriFeed AI"
              className="h-8 w-8 rounded-xl object-cover border border-primary-500/60 shadow"
            />
            <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-emerald-400 border border-primary-900" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-white tracking-tight leading-none">VeriFeed AI</span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-white/10 border border-white/15 text-primary-300">
              <Sparkles className="w-2.5 h-2.5 text-emerald-400" />
              Q&amp;A
            </span>
          </div>
        </div>

        {/* Risk Pill */}
        <span className={`shrink-0 px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wide ${
          riskLevel === "High" ? "bg-red-500/25 text-red-300 border border-red-500/30" :
          riskLevel === "Medium" ? "bg-amber-500/25 text-amber-300 border border-amber-500/30" :
          "bg-emerald-500/25 text-emerald-300 border border-emerald-500/30"
        }`}>
          {riskLevel} Risk
        </span>
      </div>

      {/* Chat Thread */}
      <div ref={scrollContainerRef} className="px-4 py-4 max-h-[400px] overflow-y-auto space-y-3 bg-white border-b border-border scrollbar-thin">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-1 duration-200`}
          >
            {msg.role === "assistant" && (
              <div className="h-6 w-6 rounded-lg bg-primary-100 border border-primary-200 flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-3 h-3 text-primary-700" />
              </div>
            )}

            <div
              className={`max-w-[78%] rounded-xl px-3.5 py-2.5 text-[13px] leading-relaxed ${
                msg.role === "user"
                  ? "bg-primary-600 text-white rounded-br-sm"
                  : "bg-gray-50 border border-border text-ink-900 rounded-bl-sm"
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>
              <div
                className={`text-[10px] mt-1.5 font-mono opacity-60 ${
                  msg.role === "user" ? "text-right" : "text-left"
                }`}
              >
                {msg.timestamp}
              </div>
            </div>

            {msg.role === "user" && (
              <div className="h-6 w-6 rounded-lg bg-primary-600 text-white flex items-center justify-center shrink-0 mt-0.5">
                <User className="w-3 h-3" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-2 justify-start animate-in fade-in">
            <div className="h-6 w-6 rounded-lg bg-primary-100 border border-primary-200 flex items-center justify-center shrink-0">
              <Bot className="w-3 h-3 text-primary-700" />
            </div>
            <div className="bg-gray-50 border border-border rounded-xl px-3.5 py-2.5 rounded-bl-sm text-[12px] text-ink-500 flex items-center gap-2">
              <RefreshCw className="w-3 h-3 animate-spin text-primary-500" />
              <span>Thinking…</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Pills */}
      {suggestions.length > 0 && (
        <div className="px-4 py-2.5 bg-white border-b border-border flex flex-wrap items-center gap-1.5">
          <HelpCircle className="w-3 h-3 text-ink-400 shrink-0" />
          {suggestions.map((sug, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSend(sug)}
              disabled={loading}
              className="text-[11px] text-primary-800 bg-primary-50 hover:bg-primary-100 border border-primary-200 px-2.5 py-1 rounded-full transition-all disabled:opacity-50 font-medium"
            >
              {sug}
            </button>
          ))}
        </div>
      )}

      {/* Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="px-3 py-3 bg-white flex items-center gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Ask about Report #${reportId}…`}
          disabled={loading}
          className="flex-1 rounded-xl border border-border bg-gray-50 px-3.5 py-2.5 text-[13px] text-ink-900 placeholder-ink-400 focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-400/20 transition-all disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="flex items-center justify-center gap-1.5 rounded-xl bg-primary-600 hover:bg-primary-700 px-4 py-2.5 text-[12px] font-bold text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <>
              <Send className="w-3.5 h-3.5" />
            </>
          )}
        </button>
      </form>
    </div>
  );
}
