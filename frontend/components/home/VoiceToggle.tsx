"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";
import type { VoicePreference } from "@/types";

const VOICE_OPTIONS: { value: VoicePreference; label: string; icon: string }[] = [
  { value: "auto",   label: "Auto",   icon: "✦" },
  { value: "female", label: "Female", icon: "♀" },
  { value: "male",   label: "Male",   icon: "♂" },
];

export function VoiceToggle() {
  const { voicePreference, setVoicePreference } = useEchoStore(
    useShallow((s) => ({
      voicePreference: s.voicePreference,
      setVoicePreference: s.setVoicePreference,
    })),
  );
  const [open, setOpen] = useState(false);

  const current = VOICE_OPTIONS.find((o) => o.value === voicePreference) ?? VOICE_OPTIONS[0];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-zinc-900/80 border border-zinc-800 text-xs text-zinc-400 hover:text-zinc-200 hover:border-zinc-700 transition-all"
      >
        <span className="text-[9px] text-zinc-600 tracking-wide">VOICE</span>
        <span className="text-[10px]">{current.icon}</span>
        <span>{current.label}</span>
        <svg
          width="8" height="8" viewBox="0 0 8 8" fill="none"
          className={`transition-transform ${open ? "rotate-180" : ""}`}
        >
          <path d="M1.5 2.5L4 5l2.5-2.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
        </svg>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.96 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-1.5 bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden shadow-2xl shadow-black/60 min-w-[130px] z-50"
          >
            <div className="px-3 pt-2.5 pb-1">
              <p className="text-[9px] text-zinc-600 uppercase tracking-widest font-medium">Voice</p>
            </div>
            {VOICE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => { setVoicePreference(opt.value); setOpen(false); }}
                className={`w-full text-left px-4 py-2.5 text-xs transition-colors flex items-center justify-between gap-3 ${
                  voicePreference === opt.value
                    ? "text-amber-400 bg-amber-500/8"
                    : "text-zinc-300 hover:bg-zinc-800"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-[11px] w-3">{opt.icon}</span>
                  <span>{opt.label}</span>
                </div>
                {voicePreference === opt.value && (
                  <div className="w-1 h-1 rounded-full bg-amber-400 flex-shrink-0" />
                )}
              </button>
            ))}
            <div className="pb-1" />
          </motion.div>
        )}
      </AnimatePresence>

      {open && <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />}
    </div>
  );
}
