"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";

const STAGE_MESSAGES = [
  { text: "Listening...", delay: 0 },
  { text: "Understanding your story...", delay: 4000 },
  { text: "Finding the right words...", delay: 8000 },
  { text: "Choosing the perfect voice...", delay: 12000 },
  { text: "Preparing your experience...", delay: 16000 },
];

export function CreationStep4() {
  const { isCreating, createError, resetCreation } = useEchoStore(
    useShallow((s) => ({
      isCreating: s.isCreating,
      createError: s.createError,
      resetCreation: s.resetCreation,
    })),
  );

  const [msgIndex, setMsgIndex] = useState(0);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    if (!isCreating) return;
    setMsgIndex(0);
    timersRef.current.forEach(clearTimeout);
    timersRef.current = STAGE_MESSAGES.map(({ delay }, i) =>
      setTimeout(() => setMsgIndex(i), delay),
    );
    return () => timersRef.current.forEach(clearTimeout);
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
    <div className="absolute inset-0 flex flex-col items-center justify-center px-6 select-none">
      {/* Breathing orb */}
      <div className="relative flex items-center justify-center mb-14">
        {/* Outer glow rings */}
        {[1, 2, 3].map((ring) => (
          <motion.div
            key={ring}
            className="absolute rounded-full border border-amber-500/10"
            style={{ width: 80 + ring * 40, height: 80 + ring * 40 }}
            animate={{ scale: [1, 1.08, 1], opacity: [0.15, 0.04, 0.15] }}
            transition={{
              duration: 3.5,
              repeat: Infinity,
              delay: ring * 0.5,
              ease: "easeInOut",
            }}
          />
        ))}
        {/* Core orb */}
        <motion.div
          className="relative z-10 w-20 h-20 rounded-full"
          style={{
            background: "radial-gradient(circle at 40% 38%, #fbbf24 0%, #d97706 55%, #92400e 100%)",
            boxShadow: "0 0 32px rgba(251,191,36,0.20), 0 0 80px rgba(251,191,36,0.08)",
          }}
          animate={{
            scale: [1, 1.06, 1],
            boxShadow: [
              "0 0 32px rgba(251,191,36,0.20), 0 0 80px rgba(251,191,36,0.08)",
              "0 0 48px rgba(251,191,36,0.30), 0 0 120px rgba(251,191,36,0.14)",
              "0 0 32px rgba(251,191,36,0.20), 0 0 80px rgba(251,191,36,0.08)",
            ],
          }}
          transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      {/* Stage message */}
      <AnimatePresence mode="wait">
        <motion.p
          key={msgIndex}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
          className="text-[16px] text-white text-center font-medium tracking-tight"
        >
          {STAGE_MESSAGES[msgIndex].text}
        </motion.p>
      </AnimatePresence>

      {/* Progress dots */}
      <div className="flex items-center gap-1.5 mt-5">
        {STAGE_MESSAGES.map((_, i) => (
          <motion.div
            key={i}
            className="rounded-full bg-zinc-700"
            animate={{
              width: i === msgIndex ? 16 : 4,
              opacity: i <= msgIndex ? 1 : 0.3,
              backgroundColor: i === msgIndex ? "#f59e0b" : "#3f3f46",
            }}
            style={{ height: 4 }}
            transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
          />
        ))}
      </div>

      <p className="text-[11px] text-zinc-600 mt-8">Usually takes 10 – 20 seconds</p>
    </div>
  );
}
