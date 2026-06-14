"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";
import { SPEAKING_STYLES } from "@/types";
import type { VoicePreference, CommunicationStylePreference } from "@/types";

const VOICE_OPTIONS: { value: VoicePreference; label: string }[] = [
  { value: "auto",   label: "Auto" },
  { value: "female", label: "Female" },
  { value: "male",   label: "Male" },
];

const STYLE_OPTIONS: { value: CommunicationStylePreference; label: string }[] = [
  { value: "auto", label: "Auto" },
  ...SPEAKING_STYLES.map((s) => ({ value: s.id as CommunicationStylePreference, label: s.label })),
];

export function VoiceToggle() {
  const {
    voicePreference,
    setVoicePreference,
    communicationStylePreference,
    setCommunicationStylePreference,
  } = useEchoStore(
    useShallow((s) => ({
      voicePreference: s.voicePreference,
      setVoicePreference: s.setVoicePreference,
      communicationStylePreference: s.communicationStylePreference,
      setCommunicationStylePreference: s.setCommunicationStylePreference,
    })),
  );
  const [open, setOpen] = useState(false);

  const voiceLabel = VOICE_OPTIONS.find((o) => o.value === voicePreference)?.label ?? "Auto";
  const isAllAuto = voicePreference === "auto" && communicationStylePreference === "auto";
  const buttonLabel = isAllAuto ? "Auto" : voiceLabel;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-zinc-900/80 border border-zinc-800 text-xs text-zinc-400 hover:text-zinc-200 hover:border-zinc-700 transition-all backdrop-blur-sm"
      >
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
          <circle cx="6" cy="6" r="5.25" stroke="currentColor" strokeWidth="1.5" />
          <path d="M6 4v2.5l1.5 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <span>{buttonLabel}</span>
        <svg
          width="8"
          height="8"
          viewBox="0 0 8 8"
          fill="none"
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
            className="absolute right-0 top-full mt-1.5 bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden shadow-2xl shadow-black/60 min-w-[160px] z-50"
          >
            {/* Voice section */}
            <div className="px-3 pt-2.5 pb-1">
              <p className="text-[9px] text-zinc-600 uppercase tracking-widest font-medium">Voice</p>
            </div>
            {VOICE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => { setVoicePreference(opt.value); setOpen(false); }}
                className={`w-full text-left px-4 py-2 text-xs transition-colors flex items-center justify-between gap-2 ${
                  voicePreference === opt.value
                    ? "text-amber-400 bg-amber-500/8"
                    : "text-zinc-300 hover:bg-zinc-800"
                }`}
              >
                <span>{opt.label}</span>
                {voicePreference === opt.value && (
                  <div className="w-1 h-1 rounded-full bg-amber-400 flex-shrink-0" />
                )}
              </button>
            ))}

            {/* Divider */}
            <div className="mx-3 my-1 border-t border-zinc-800" />

            {/* Style section */}
            <div className="px-3 pt-1 pb-1">
              <p className="text-[9px] text-zinc-600 uppercase tracking-widest font-medium">Style</p>
            </div>
            {STYLE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => { setCommunicationStylePreference(opt.value); setOpen(false); }}
                className={`w-full text-left px-4 py-2 text-xs transition-colors flex items-center justify-between gap-2 ${
                  communicationStylePreference === opt.value
                    ? "text-amber-400 bg-amber-500/8"
                    : "text-zinc-300 hover:bg-zinc-800"
                }`}
              >
                <span>{opt.label}</span>
                {communicationStylePreference === opt.value && (
                  <div className="w-1 h-1 rounded-full bg-amber-400 flex-shrink-0" />
                )}
              </button>
            ))}
            <div className="pb-1" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Dismiss overlay */}
      {open && (
        <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
      )}
    </div>
  );
}
