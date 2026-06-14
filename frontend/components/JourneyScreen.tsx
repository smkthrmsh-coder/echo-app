"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";
import { JourneySessionPlayer } from "./home/JourneySessionPlayer";
import type { JourneyTemplate } from "@/types";

function StreakBadge({ streak }: { streak: number }) {
  return (
    <div className="flex items-center justify-between bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3 mb-5">
      <div>
        <p className="text-[13px] font-semibold text-white">
          {streak} day{streak !== 1 ? "s" : ""} streak
        </p>
        <p className="text-xs text-zinc-500 mt-0.5">Keep showing up — you&apos;re building something real.</p>
      </div>
      <div className="flex flex-col items-center">
        <span className="text-xl font-bold text-amber-400">{streak}</span>
        <span className="text-[10px] text-zinc-600 uppercase tracking-widest">days</span>
      </div>
    </div>
  );
}

function ActiveJourneyCard({ onOpenSession }: { onOpenSession: (slug: string) => void }) {
  const { activeJourney, abandonJourney } = useEchoStore(
    useShallow((s) => ({
      activeJourney: s.activeJourney,
      abandonJourney: s.abandonJourney,
    })),
  );

  if (!activeJourney) return null;

  const { journey, current_day, completed_days } = activeJourney;
  const progress = completed_days.length / journey.duration_days;
  const todayDone = completed_days.includes(current_day);

  return (
    <div className="mb-6">
      <p className="text-xs text-zinc-500 uppercase tracking-widest mb-3">Active Program</p>
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden">
        <div className="px-5 pt-5 pb-4">
          {/* Title row */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-[15px] font-bold text-white leading-tight">{journey.title}</p>
              <p className="text-xs text-zinc-500 mt-0.5">Day {current_day} of {journey.duration_days}</p>
            </div>
            <span className="text-xs font-semibold text-zinc-400 bg-zinc-800 rounded-full px-2.5 py-1">
              {Math.round(progress * 100)}%
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-4">
            <motion.div
              className="h-full rounded-full bg-amber-500"
              initial={{ width: 0 }}
              animate={{ width: `${progress * 100}%` }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            />
          </div>

          {/* Day dots */}
          <div className="flex gap-1 mb-4 flex-wrap">
            {Array.from({ length: journey.duration_days }).map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full transition-colors ${
                  completed_days.includes(i + 1) ? "bg-amber-500" : "bg-zinc-800"
                }`}
              />
            ))}
          </div>

          {todayDone ? (
            <div className="flex items-center gap-2 py-2.5 px-4 bg-zinc-800/50 rounded-lg">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="6.25" stroke="#4ade80" strokeWidth="1.5" />
                <path d="M4.5 7l2 2 3-3" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span className="text-sm text-green-400 font-medium">Today&apos;s session complete</span>
            </div>
          ) : (
            <motion.button
              whileTap={{ scale: 0.98 }}
              onClick={() => onOpenSession(activeJourney.journey_slug)}
              className="w-full py-3 rounded-lg bg-amber-500 hover:bg-amber-400 text-black text-sm font-semibold transition-colors flex items-center justify-center gap-2"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                <path d="M3 2l9 5-9 5z" />
              </svg>
              Start today&apos;s session
            </motion.button>
          )}
        </div>

        <div className="px-5 py-3 border-t border-zinc-800 flex justify-between items-center">
          <p className="text-xs text-zinc-500">{completed_days.length} of {journey.duration_days} days complete</p>
          <button
            onClick={() => abandonJourney(activeJourney.journey_slug)}
            className="text-xs text-zinc-600 hover:text-red-400 transition-colors"
          >
            Leave program
          </button>
        </div>
      </div>
    </div>
  );
}

function JourneyCard({ journey, onStart, loading }: { journey: JourneyTemplate; onStart: () => void; loading: boolean }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900">
      <div className="px-5 py-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1 min-w-0 pr-3">
            <p className="text-[14px] font-semibold text-white leading-tight">{journey.title}</p>
            <p className="text-xs text-zinc-500 mt-0.5">{journey.tagline}</p>
          </div>
          <span className="text-xs font-semibold text-zinc-400 bg-zinc-800 rounded-full px-2 py-0.5 flex-shrink-0">
            {journey.duration_days} days
          </span>
        </div>
        <p className="text-xs text-zinc-500 mb-4 leading-relaxed">{journey.description}</p>
        <motion.button
          whileTap={{ scale: 0.98 }}
          onClick={onStart}
          disabled={loading}
          className="w-full py-2.5 rounded-lg border border-zinc-700 text-zinc-300 text-sm font-medium hover:border-amber-500 hover:text-amber-400 transition-colors disabled:opacity-50"
        >
          {loading ? "Starting..." : "Start program"}
        </motion.button>
      </div>
    </div>
  );
}

export function JourneyScreen() {
  const {
    journeyTemplates,
    activeJourney,
    streak,
    journeysLoading,
    loadJourneys,
    loadActiveJourney,
    loadStreak,
    startJourney,
    openJourneySession,
    journeySession,
    journeySessionLoading,
    journeySessionError,
  } = useEchoStore(
    useShallow((s) => ({
      journeyTemplates: s.journeyTemplates,
      activeJourney: s.activeJourney,
      streak: s.streak,
      journeysLoading: s.journeysLoading,
      loadJourneys: s.loadJourneys,
      loadActiveJourney: s.loadActiveJourney,
      loadStreak: s.loadStreak,
      startJourney: s.startJourney,
      openJourneySession: s.openJourneySession,
      journeySession: s.journeySession,
      journeySessionLoading: s.journeySessionLoading,
      journeySessionError: s.journeySessionError,
    })),
  );

  const [starting, setStarting] = useState<string | null>(null);

  useEffect(() => {
    loadJourneys();
    loadActiveJourney();
    loadStreak();
  }, [loadJourneys, loadActiveJourney, loadStreak]);

  async function handleStart(slug: string) {
    setStarting(slug);
    try {
      await startJourney(slug);
      openJourneySession(slug);
    } finally {
      setStarting(null);
    }
  }

  return (
    <div className="relative flex flex-col h-full overflow-hidden">
      <div className="px-6 pt-6 pb-4">
        <h1 className="text-[18px] font-bold text-white">Programs</h1>
        <p className="text-xs text-zinc-500 mt-0.5">Guided journeys that build with you.</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-6">
        {/* Streak */}
        {streak && streak.current_streak > 0 && (
          <StreakBadge streak={streak.current_streak} />
        )}

        {/* Active journey */}
        <AnimatePresence>
          {activeJourney && (
            <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <ActiveJourneyCard onOpenSession={openJourneySession} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Browse */}
        {!activeJourney && (
          <>
            <p className="text-xs text-zinc-500 uppercase tracking-widest mb-3">All programs</p>
            {journeysLoading ? (
              <div className="text-center py-12 text-zinc-600 text-sm">Loading...</div>
            ) : (
              <div className="space-y-2.5">
                {(journeyTemplates ?? []).map((j) => (
                  <JourneyCard
                    key={j.slug}
                    journey={j}
                    onStart={() => handleStart(j.slug)}
                    loading={starting === j.slug}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {/* Other programs while one is active */}
        {activeJourney && (journeyTemplates ?? []).length > 1 && (
          <>
            <p className="text-xs text-zinc-500 uppercase tracking-widest mb-3 mt-2">Other programs</p>
            <div className="space-y-2">
              {(journeyTemplates ?? [])
                .filter((j) => j.slug !== activeJourney.journey_slug)
                .map((j) => (
                  <JourneyCard
                    key={j.slug}
                    journey={j}
                    onStart={() => handleStart(j.slug)}
                    loading={starting === j.slug}
                  />
                ))}
            </div>
          </>
        )}
      </div>

      {/* Session player overlay */}
      {(journeySession || journeySessionLoading || journeySessionError) && <JourneySessionPlayer />}
    </div>
  );
}
