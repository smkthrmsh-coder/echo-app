"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { useEchoStore } from "@/store/useEchoStore";

const BARS = [0.3, 0.6, 1, 0.8, 0.5, 0.9, 0.4, 0.7, 0.6];

export function WelcomeView() {
  const dismissWelcome = useEchoStore((s) => s.dismissWelcome);

  // Auto-dismiss after 3.5 seconds
  useEffect(() => {
    const t = setTimeout(dismissWelcome, 3500);
    return () => clearTimeout(t);
  }, [dismissWelcome]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="absolute inset-0 flex flex-col items-center justify-center bg-black px-8 select-none"
      onClick={dismissWelcome}
    >
      {/* Waveform */}
      <div className="flex items-center gap-[5px] mb-8">
        {BARS.map((h, i) => (
          <motion.div
            key={i}
            className="w-[3px] rounded-full bg-amber-500"
            animate={{ scaleY: [h, 1, h], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.8, repeat: Infinity, delay: i * 0.16, ease: "easeInOut" }}
            style={{ height: 32, transformOrigin: "center" }}
          />
        ))}
      </div>

      <motion.h1
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="text-[28px] font-bold text-white text-center leading-tight mb-2"
      >
        Good to have you here.
      </motion.h1>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.5 }}
        className="text-sm text-zinc-400 text-center"
      >
        Find the voice you need today.
      </motion.p>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.8, duration: 0.5 }}
        className="text-xs text-zinc-700 text-center mt-10"
      >
        Tap anywhere to begin
      </motion.p>
    </motion.div>
  );
}
