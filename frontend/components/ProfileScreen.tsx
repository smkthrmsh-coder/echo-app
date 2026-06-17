"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";
import { HistoryScreen } from "./HistoryScreen";
import { SPEAKING_STYLES } from "@/types";
import type { VoicePreference, CommunicationStylePreference } from "@/types";

const VOICE_OPTIONS: { value: VoicePreference; label: string; desc: string }[] = [
  { value: "auto",   label: "Automatic",  desc: "Echo chooses the best voice for each experience." },
  { value: "female", label: "Female",     desc: "Always use a female voice." },
  { value: "male",   label: "Male",       desc: "Always use a male voice." },
];

const STYLE_OPTIONS: { value: CommunicationStylePreference; label: string; desc: string }[] = [
  { value: "auto",     label: "Automatic",           desc: "Echo selects the best style for every experience." },
  ...SPEAKING_STYLES.map((s) => ({ value: s.id as CommunicationStylePreference, label: s.label, desc: "" })),
];

export function ProfileScreen() {
  const {
    displayName,
    memories,
    loadMemories,
    logout,
    voicePreference,
    setVoicePreference,
    communicationStylePreference,
    setCommunicationStylePreference,
    speechRateOverride,
    setSpeechRateOverride,
  } = useEchoStore(
    useShallow((s) => ({
      displayName: s.displayName,
      memories: s.memories,
      loadMemories: s.loadMemories,
      logout: s.logout,
      voicePreference: s.voicePreference,
      setVoicePreference: s.setVoicePreference,
      communicationStylePreference: s.communicationStylePreference,
      setCommunicationStylePreference: s.setCommunicationStylePreference,
      speechRateOverride: s.speechRateOverride,
      setSpeechRateOverride: s.setSpeechRateOverride,
    })),
  );

  const [loading, setLoading] = useState(true);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    loadMemories().finally(() => setLoading(false));
  }, [loadMemories]);

  if (showHistory) {
    return (
      <div className="flex flex-col h-full">
        <div className="px-6 pt-5 pb-3 border-b border-zinc-900 flex items-center gap-3">
          <button
            onClick={() => setShowHistory(false)}
            className="flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M9 2L4.5 7 9 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Back
          </button>
          <h1 className="text-[15px] font-semibold text-white">Conversations</h1>
        </div>
        <div className="flex-1 overflow-hidden">
          <HistoryScreen />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-6 pt-6 pb-5 border-b border-zinc-900">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center">
              <span className="text-zinc-300 text-sm font-bold">{displayName.charAt(0).toUpperCase()}</span>
            </div>
            <div>
              <p className="text-[14px] font-semibold text-white">{displayName}</p>
              <p className="text-xs text-zinc-500">Free plan</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="text-xs text-zinc-500 hover:text-white transition-colors px-3 py-1.5 rounded-lg border border-zinc-800 hover:border-zinc-700"
          >
            Sign out
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">

        {/* Premium CTA */}
        <div className="mx-4 mt-4 rounded-xl border border-amber-900/40 overflow-hidden"
          style={{ background: "linear-gradient(135deg, #1c0e00, #0d0700)" }}>
          <div className="px-5 py-4">
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="text-[11px] text-amber-500 uppercase tracking-widest font-semibold mb-0.5">Echo Premium</p>
                <p className="text-[15px] font-bold text-white">Unlock everything</p>
              </div>
              <span className="text-xs text-amber-500/70 bg-amber-500/10 border border-amber-500/20 rounded-full px-2 py-0.5 font-medium mt-0.5">
                Soon
              </span>
            </div>
            <p className="text-xs text-zinc-400 mb-4 leading-relaxed">
              Unlimited journeys, priority voice, advanced insights, and custom personas.
            </p>
            <button className="w-full py-2.5 rounded-lg bg-amber-500 text-black text-xs font-bold opacity-50 cursor-not-allowed">
              Coming Soon
            </button>
          </div>
        </div>

        {/* Voice & Experience */}
        <div className="px-4 mt-5">
          <p className="text-[11px] text-zinc-500 uppercase tracking-widest mb-3">Voice &amp; Experience</p>

          {/* Voice preference */}
          <p className="text-xs text-zinc-600 mb-2 px-1">Voice</p>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden divide-y divide-zinc-800 mb-3">
            {VOICE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setVoicePreference(opt.value)}
                className="w-full flex items-start gap-3 px-4 py-3.5 text-left hover:bg-zinc-800/40 transition-colors"
              >
                <div className={`w-4 h-4 rounded-full border-2 flex-shrink-0 mt-0.5 transition-all ${
                  voicePreference === opt.value ? "border-amber-400 bg-amber-400" : "border-zinc-600"
                }`}>
                  {voicePreference === opt.value && (
                    <svg viewBox="0 0 16 16" fill="none" className="w-full h-full p-[3px]">
                      <path d="M3 8l3.5 3.5L13 5" stroke="#000" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-[13px] font-medium transition-colors ${voicePreference === opt.value ? "text-white" : "text-zinc-300"}`}>
                    {opt.label}
                    {opt.value === "auto" && (
                      <span className="ml-2 text-[10px] text-amber-500 bg-amber-500/10 border border-amber-500/20 rounded-full px-1.5 py-0.5 align-middle">
                        Default
                      </span>
                    )}
                  </p>
                  {voicePreference === opt.value && opt.desc && (
                    <p className="text-xs text-zinc-500 mt-0.5 leading-relaxed">{opt.desc}</p>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Communication style */}
          <p className="text-xs text-zinc-600 mb-2 px-1">Communication Style</p>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden divide-y divide-zinc-800">
            {STYLE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setCommunicationStylePreference(opt.value)}
                className="w-full flex items-start gap-3 px-4 py-3.5 text-left hover:bg-zinc-800/40 transition-colors"
              >
                <div className={`w-4 h-4 rounded-full border-2 flex-shrink-0 mt-0.5 transition-all ${
                  communicationStylePreference === opt.value ? "border-amber-400 bg-amber-400" : "border-zinc-600"
                }`}>
                  {communicationStylePreference === opt.value && (
                    <svg viewBox="0 0 16 16" fill="none" className="w-full h-full p-[3px]">
                      <path d="M3 8l3.5 3.5L13 5" stroke="#000" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-[13px] font-medium transition-colors ${communicationStylePreference === opt.value ? "text-white" : "text-zinc-300"}`}>
                    {opt.label}
                    {opt.value === "auto" && (
                      <span className="ml-2 text-[10px] text-amber-500 bg-amber-500/10 border border-amber-500/20 rounded-full px-1.5 py-0.5 align-middle">
                        Default
                      </span>
                    )}
                  </p>
                  {communicationStylePreference === opt.value && opt.desc && (
                    <p className="text-xs text-zinc-500 mt-0.5 leading-relaxed">{opt.desc}</p>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Speech Speed */}
        <div className="px-4 mt-5">
          <p className="text-[11px] text-zinc-500 uppercase tracking-widest mb-3">Speech Speed</p>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[13px] font-medium text-zinc-300">Speed</span>
              <div className="flex items-center gap-2">
                {speechRateOverride !== null && (
                  <button
                    onClick={() => setSpeechRateOverride(null)}
                    className="text-[11px] text-zinc-500 hover:text-zinc-300 transition-colors"
                  >
                    Reset
                  </button>
                )}
                <span className="text-[13px] font-semibold text-amber-400 tabular-nums min-w-[44px] text-right">
                  {speechRateOverride !== null ? `${speechRateOverride.toFixed(2)}×` : "Auto"}
                </span>
              </div>
            </div>
            <input
              type="range"
              min="0.75"
              max="1.40"
              step="0.05"
              value={speechRateOverride ?? 1.0}
              onChange={(e) => setSpeechRateOverride(parseFloat(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <div className="flex justify-between mt-1.5">
              <span className="text-[10px] text-zinc-600">0.75× Slower</span>
              <span className="text-[10px] text-zinc-600">Faster 1.40×</span>
            </div>
            <p className="text-[11px] text-zinc-600 mt-2.5 leading-relaxed">
              {speechRateOverride !== null
                ? "Applies to all experiences. Reset to let each experience set its own speed."
                : "Each experience sets its own speed. Drag to override globally."}
            </p>
          </div>
        </div>

        {/* Navigation links */}
        <div className="px-4 mt-4">
          <p className="text-[11px] text-zinc-500 uppercase tracking-widest mb-3">Account</p>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden divide-y divide-zinc-800">
            <button
              onClick={() => setShowHistory(true)}
              className="w-full flex items-center justify-between px-4 py-3.5 hover:bg-zinc-800/40 transition-colors"
            >
              <span className="text-sm text-zinc-200">Conversations</span>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="text-zinc-600">
                <path d="M5 2.5l4.5 4.5L5 11.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
            <button className="w-full flex items-center justify-between px-4 py-3.5 hover:bg-zinc-800/40 transition-colors">
              <span className="text-sm text-zinc-400">Export Data</span>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="text-zinc-700">
                <path d="M5 2.5l4.5 4.5L5 11.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
            <button className="w-full flex items-center justify-between px-4 py-3.5 hover:bg-zinc-800/40 transition-colors">
              <span className="text-sm text-zinc-400">Privacy</span>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="text-zinc-700">
                <path d="M5 2.5l4.5 4.5L5 11.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </div>

        {/* Memories */}
        <div className="px-4 mt-5">
          <div className="flex items-center justify-between mb-3">
            <p className="text-[11px] text-zinc-500 uppercase tracking-widest">Saved Memories</p>
            <span className="text-xs text-zinc-600 font-medium tabular-nums">{memories.length}</span>
          </div>

          {loading && <div className="text-center py-8 text-zinc-600 text-sm">Loading...</div>}

          {!loading && memories.length === 0 && (
            <div className="text-center py-10 bg-zinc-900/50 border border-zinc-800/50 rounded-xl">
              <p className="text-zinc-400 text-sm">No memories saved yet.</p>
              <p className="text-zinc-600 text-xs mt-1">Save moments from any conversation.</p>
            </div>
          )}

          <div className="space-y-2 pb-4">
            {memories.map((mem) => (
              <motion.div
                key={mem.id}
                initial={{ opacity: 0, y: 3 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3.5"
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <p className="text-[13px] font-semibold text-white leading-snug">{mem.title}</p>
                  {mem.category && mem.category !== "general" && (
                    <span className="text-[10px] text-zinc-500 bg-zinc-800 px-2 py-0.5 rounded-full flex-shrink-0 font-medium uppercase tracking-widest">
                      {mem.category}
                    </span>
                  )}
                </div>
                <p className="text-xs text-zinc-400 line-clamp-2 leading-relaxed">{mem.content}</p>
                <p className="text-[11px] text-zinc-600 mt-2">
                  {new Date(mem.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                </p>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-6 text-center border-t border-zinc-900 mt-2">
          <p className="text-xs text-zinc-700">Echo v1.0 · Find the voice you need today.</p>
        </div>
      </div>
    </div>
  );
}
