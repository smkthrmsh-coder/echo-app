"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";
import { INTENTIONS } from "@/types";
import type { IntentionId } from "@/types";
import { unlockAudio } from "@/hooks/useAmbientSound";

export function IntentionStep() {
  const {
    selectedIntention,
    customIntention,
    setSelectedIntention,
    setCustomIntention,
    startGeneration,
    isCreating,
  } = useEchoStore(
    useShallow((s) => ({
      selectedIntention: s.selectedIntention,
      customIntention: s.customIntention,
      setSelectedIntention: s.setSelectedIntention,
      setCustomIntention: s.setCustomIntention,
      startGeneration: s.startGeneration,
      isCreating: s.isCreating,
    })),
  );

  const canContinue = selectedIntention !== null;

  function handleCardClick(id: IntentionId) {
    if (selectedIntention === id) return;
    setSelectedIntention(id);
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.22 }}
      className="absolute inset-0 flex flex-col"
    >
      {/* Header */}
      <div className="px-6 pt-10 pb-5 flex-shrink-0">
        <h2 className="text-[22px] font-bold text-white leading-snug mb-1">
          What are you looking for today?
        </h2>
        <p className="text-sm text-zinc-400">Choose what feels closest.</p>
      </div>

      {/* Intention cards */}
      <div className="flex-1 overflow-y-auto px-6 pb-2 space-y-2">
        {INTENTIONS.map((intention) => {
          const active = selectedIntention === intention.id;

          return (
            <div
              key={intention.id}
              className={`rounded-2xl border transition-colors duration-200 ${
                active
                  ? "border-amber-500/40 bg-zinc-900"
                  : "border-zinc-800/50 bg-zinc-900/30 hover:border-zinc-700/70 hover:bg-zinc-900/60"
              }`}
            >
              {/* Card header — clickable */}
              <div
                className="px-5 py-4 cursor-pointer select-none"
                onClick={() => handleCardClick(intention.id as IntentionId)}
              >
                <p
                  className={`text-[16px] font-semibold leading-tight transition-colors ${
                    active ? "text-white" : "text-zinc-200"
                  }`}
                >
                  {intention.title}
                </p>
                <p
                  className={`text-[13px] mt-0.5 leading-snug transition-colors ${
                    active ? "text-zinc-400" : "text-zinc-500"
                  }`}
                >
                  {intention.subtitle}
                </p>
              </div>

              {/* Inline expansion — textarea */}
              <AnimatePresence>
                {active && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
                    style={{ overflow: "hidden" }}
                  >
                    <div className="px-5 pb-4">
                      <div className="w-full h-px bg-zinc-800 mb-3" />
                      <textarea
                        autoFocus
                        value={customIntention}
                        onChange={(e) => setCustomIntention(e.target.value)}
                        placeholder="Tell me a little about what's going on."
                        rows={3}
                        className="w-full bg-transparent text-sm text-white placeholder-zinc-600 resize-none focus:outline-none leading-relaxed"
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>

      {/* CTA */}
      <div className="px-6 pb-6 pt-3 flex-shrink-0">
        <motion.button
          whileTap={{ scale: 0.98 }}
          onClick={() => {
            unlockAudio(); // create AudioContext in gesture handler — required for iOS
            startGeneration();
          }}
          disabled={!canContinue || isCreating}
          className="w-full bg-amber-500 hover:bg-amber-400 disabled:opacity-25 text-black font-semibold rounded-xl py-3.5 text-[15px] transition-all"
        >
          Hear What You Need
        </motion.button>
      </div>
    </motion.div>
  );
}
