"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";

const MESSAGES = [
  "Listening...",
  "Understanding your situation...",
  "Finding the right words...",
  "Choosing the perfect voice...",
  "Creating your experience...",
  "Preparing your audio...",
];

const BARS = Array.from({ length: 11 });

export function CreationStep4() {
  const { isCreating, createError, resetCreation } = useEchoStore(
    useShallow((s) => ({
      isCreating: s.isCreating,
      createError: s.createError,
      resetCreation: s.resetCreation,
    })),
  );

  const [msgIndex, setMsgIndex] = useState(0);

  useEffect(() => {
    if (!isCreating) return;
    const interval = setInterval(() => {
      setMsgIndex((i) => Math.min(i + 1, MESSAGES.length - 1));
    }, 3000);
    return () => clearInterval(interval);
  }, [isCreating]);

  if (createError) {
    return (
      <div className="absolute inset-0 flex flex-col items-center justify-center px-8 text-center">
        <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mb-5">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#71717a" strokeWidth="1.8" strokeLinecap="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <p className="text-[17px] font-semibold text-white mb-2">Something went wrong</p>
        <p className="text-sm text-zinc-400 mb-8 max-w-[260px] leading-relaxed">{createError}</p>
        <button
          onClick={resetCreation}
          className="bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-200 px-6 py-3 rounded-xl text-sm transition-colors"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center px-6">
      {/* Waveform */}
      <div className="flex items-center gap-[4px] mb-10">
        {BARS.map((_, i) => (
          <motion.div
            key={i}
            className="w-[3px] rounded-full bg-amber-500"
            animate={{ scaleY: [0.12, 1, 0.12], opacity: [0.25, 1, 0.25] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.1, ease: "easeInOut" }}
            style={{ height: 52, transformOrigin: "center" }}
          />
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.p
          key={msgIndex}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.35 }}
          className="text-[15px] text-white text-center font-medium"
        >
          {MESSAGES[msgIndex]}
        </motion.p>
      </AnimatePresence>

      <p className="text-xs text-zinc-600 mt-3 text-center">Usually takes 15 – 25 seconds</p>
    </div>
  );
}
