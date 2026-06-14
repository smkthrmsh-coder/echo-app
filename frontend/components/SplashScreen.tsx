"use client";

import { motion } from "framer-motion";

export function SplashScreen() {

  const bars = Array.from({ length: 9 });

  return (
    <div className="flex flex-col items-center justify-center h-full bg-black select-none">
      {/* Waveform */}
      <div className="flex items-center gap-[5px] mb-10 h-14">
        {bars.map((_, i) => (
          <motion.div
            key={i}
            className="w-[3px] rounded-full bg-amber-400"
            animate={{
              scaleY: [0.2, 1, 0.2],
              opacity: [0.4, 1, 0.4],
            }}
            transition={{
              duration: 1.2,
              repeat: Infinity,
              delay: i * 0.1,
              ease: "easeInOut",
            }}
            style={{ height: 48, transformOrigin: "center" }}
          />
        ))}
      </div>

      <motion.h1
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.6 }}
        className="text-4xl font-bold tracking-tight text-white mb-2"
      >
        Echo
      </motion.h1>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7, duration: 0.6 }}
        className="text-sm text-zinc-500 tracking-wide"
      >
        Find the voice you need today.
      </motion.p>
    </div>
  );
}
