"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";
import { JourneySessionPlayer } from "./home/JourneySessionPlayer";
import { fetchJourneyRecommendations } from "@/lib/api";
import type { JourneyTemplate } from "@/types";

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function StreakBadge({ streak }: { streak: number }) {
  return (
    <div className="flex items-center justify-between bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3.5 mb-5">
      <div>
        <p className="text-[13px] font-semibold text-white">
          {streak} day{streak !== 1 ? "s" : ""} in a row
        </p>
        <p className="text-xs text-zinc-500 mt-0.5">Keep showing up — you&apos;re building something real.</p>
      </div>
      <div className="w-10 h-10 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
        <span className="text-lg">🔥</span>
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

  const { journey, current_day, completed_days, remaining_days, progress_pct, estimated_completion } = activeJourney;
  const todayDone = completed_days.includes(current_day);

  return (
    <div className="mb-6">
      <p className="text-[11px] text-zinc-500 uppercase tracking-widest mb-3">Active Program</p>
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900 overflow-hidden">
        {/* Color accent strip */}
        <div className="h-1 w-full" style={{ backgroundColor: journey.color }} />

        <div className="px-5 pt-4 pb-4">
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-start gap-3">
              <span className="text-2xl">{journey.emoji}</span>
              <div>
                <p className="text-[15px] font-bold text-white leading-tight">{journey.title}</p>
                <p className="text-xs text-zinc-500 mt-0.5">Day {current_day} of {journey.duration_days}</p>
              </div>
            </div>
            <span className="text-xs font-bold tabular-nums" style={{ color: journey.color }}>
              {progress_pct}%
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden mb-3">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: journey.color }}
              initial={{ width: 0 }}
              animate={{ width: `${progress_pct}%` }}
              transition={{ duration: 0.7, ease: "easeOut" }}
            />
          </div>

          {/* Day dots */}
          <div className="flex gap-1 mb-4 flex-wrap">
            {Array.from({ length: journey.duration_days }).map((_, i) => (
              <div
                key={i}
                className="w-2 h-2 rounded-full transition-colors"
                style={{
                  backgroundColor: completed_days.includes(i + 1) ? journey.color : "#27272a",
                }}
              />
            ))}
          </div>

          {/* Outcome */}
          <div className="flex items-start gap-2 mb-4 bg-zinc-800/40 rounded-lg px-3 py-2.5">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="flex-shrink-0 mt-0.5">
              <path d="M7 1l1.6 3.3L12 4.9l-2.5 2.4.6 3.4L7 9.1 3.9 10.7l.6-3.4L2 4.9l3.4-.6L7 1z"
                fill={journey.color} opacity="0.8" />
            </svg>
            <p className="text-xs text-zinc-400 leading-relaxed">{journey.outcome}</p>
          </div>

          {/* Meta row */}
          <div className="flex gap-4 mb-4">
            <div>
              <p className="text-[10px] text-zinc-600 uppercase tracking-widest">Remaining</p>
              <p className="text-sm font-semibold text-zinc-300 mt-0.5">{remaining_days} days</p>
            </div>
            {estimated_completion && (
              <div>
                <p className="text-[10px] text-zinc-600 uppercase tracking-widest">Completes</p>
                <p className="text-sm font-semibold text-zinc-300 mt-0.5">{formatDate(estimated_completion)}</p>
              </div>
            )}
            <div>
              <p className="text-[10px] text-zinc-600 uppercase tracking-widest">Done</p>
              <p className="text-sm font-semibold text-zinc-300 mt-0.5">{completed_days.length} of {journey.duration_days}</p>
            </div>
          </div>

          {todayDone ? (
            <div className="flex items-center gap-2 py-2.5 px-4 bg-green-500/10 border border-green-500/20 rounded-lg">
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
              className="w-full py-3 rounded-xl text-black text-sm font-semibold transition-colors flex items-center justify-center gap-2"
              style={{ backgroundColor: journey.color }}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                <path d="M3 2l9 5-9 5z" />
              </svg>
              Start today&apos;s session
            </motion.button>
          )}
        </div>

        <div className="px-5 py-3 border-t border-zinc-800 flex justify-end">
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

function JourneyCard({
  journey,
  onStart,
  loading,
  recommendedReason,
}: {
  journey: JourneyTemplate;
  onStart: () => void;
  loading: boolean;
  recommendedReason?: string;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 overflow-hidden">
      {/* Color strip */}
      <div className="h-0.5 w-full" style={{ backgroundColor: journey.color }} />

      <div className="px-5 py-4">
        {/* Recommended badge */}
        {recommendedReason && (
          <div className="flex items-center gap-1.5 mb-3">
            <span className="text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded-full text-black"
              style={{ backgroundColor: journey.color }}>
              For you
            </span>
            <span className="text-[11px] text-zinc-500">{recommendedReason}</span>
          </div>
        )}

        {/* Header */}
        <div className="flex items-start gap-3 mb-2.5">
          <span className="text-xl flex-shrink-0">{journey.emoji}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between">
              <p className="text-[14px] font-semibold text-white leading-tight">{journey.title}</p>
              <span className="text-[11px] text-zinc-500 ml-2 flex-shrink-0 mt-0.5">{journey.duration_days}d</span>
            </div>
            <p className="text-xs text-zinc-500 mt-0.5">{journey.tagline}</p>
          </div>
        </div>

        {/* Outcome */}
        <p className="text-xs text-zinc-400 leading-relaxed mb-3">{journey.outcome}</p>

        {/* Expandable description */}
        <AnimatePresence initial={false}>
          {expanded && (
            <motion.p
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="text-xs text-zinc-500 leading-relaxed mb-3 overflow-hidden"
            >
              {journey.description}
            </motion.p>
          )}
        </AnimatePresence>

        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[11px] text-zinc-600 hover:text-zinc-400 transition-colors mb-4"
        >
          {expanded ? "Less" : "More details"}
        </button>

        <motion.button
          whileTap={{ scale: 0.98 }}
          onClick={onStart}
          disabled={loading}
          className="w-full py-2.5 rounded-xl border text-sm font-medium transition-colors disabled:opacity-50"
          style={{
            borderColor: journey.color,
            color: journey.color,
          }}
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
  const [recommendations, setRecommendations] = useState<{ slug: string; reason: string }[]>([]);

  useEffect(() => {
    loadJourneys();
    loadActiveJourney();
    loadStreak();
    fetchJourneyRecommendations().then(setRecommendations).catch(() => {});
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

  const recMap = Object.fromEntries(recommendations.map((r) => [r.slug, r.reason]));
  const templates = journeyTemplates ?? [];
  const availableTemplates = activeJourney
    ? templates.filter((j) => j.slug !== activeJourney.journey_slug)
    : templates;

  const recommendedTemplates = availableTemplates.filter((j) => recMap[j.slug]);
  const otherTemplates = availableTemplates.filter((j) => !recMap[j.slug]);

  return (
    <div className="relative flex flex-col h-full overflow-hidden">
      <div className="px-6 pt-6 pb-4">
        <h1 className="text-[18px] font-bold text-white">Programs</h1>
        <p className="text-xs text-zinc-500 mt-0.5">Guided journeys that build with you.</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-5">
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

        {journeysLoading && templates.length === 0 ? (
          <div className="text-center py-12 text-zinc-600 text-sm">Loading...</div>
        ) : (
          <>
            {/* Recommended for you */}
            {!activeJourney && recommendedTemplates.length > 0 && (
              <div>
                <p className="text-[11px] text-zinc-500 uppercase tracking-widest mb-3">Recommended for you</p>
                <div className="space-y-3">
                  {recommendedTemplates.map((j) => (
                    <JourneyCard
                      key={j.slug}
                      journey={j}
                      onStart={() => handleStart(j.slug)}
                      loading={starting === j.slug}
                      recommendedReason={recMap[j.slug]}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* All programs */}
            {otherTemplates.length > 0 && (
              <div>
                <p className="text-[11px] text-zinc-500 uppercase tracking-widest mb-3">
                  {activeJourney ? "Other programs" : recommendedTemplates.length > 0 ? "All programs" : "All programs"}
                </p>
                <div className="space-y-3">
                  {otherTemplates.map((j) => (
                    <JourneyCard
                      key={j.slug}
                      journey={j}
                      onStart={() => handleStart(j.slug)}
                      loading={starting === j.slug}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* When active journey and no other templates */}
            {activeJourney && availableTemplates.length === 0 && (
              <p className="text-xs text-zinc-600 text-center py-4">All programs started!</p>
            )}
          </>
        )}
      </div>

      {/* Session player overlay */}
      {(journeySession || journeySessionLoading || journeySessionError) && <JourneySessionPlayer />}
    </div>
  );
}
