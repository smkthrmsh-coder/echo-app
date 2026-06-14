"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";

function LockIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="text-zinc-500">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-4">
      <p className="text-[11px] text-zinc-500 uppercase tracking-widest mb-1.5">{label}</p>
      <p className="text-[22px] font-bold text-white leading-none">{value}</p>
      {sub && <p className="text-xs text-zinc-500 mt-1">{sub}</p>}
    </div>
  );
}

function LockedState({ conversationsUntilUnlock }: { conversationsUntilUnlock: number }) {
  const done = 3 - conversationsUntilUnlock;
  return (
    <div className="flex flex-col items-center justify-center px-8 text-center pt-12 pb-8">
      <div className="w-14 h-14 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mb-5">
        <LockIcon />
      </div>
      <h3 className="text-[17px] font-bold text-white mb-2">Insights unlock soon</h3>
      <p className="text-sm text-zinc-400 leading-relaxed mb-7 max-w-[260px]">
        Have {conversationsUntilUnlock} more conversation{conversationsUntilUnlock !== 1 ? "s" : ""} with Echo to unlock your personal patterns and emotion trends.
      </p>

      {/* Progress */}
      <div className="w-full max-w-[220px]">
        <div className="flex justify-between text-xs text-zinc-500 mb-2">
          <span>{done} of 3 conversations</span>
          <span>{Math.round((done / 3) * 100)}%</span>
        </div>
        <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-amber-500 rounded-full transition-all"
            style={{ width: `${Math.max(4, (done / 3) * 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <p className="text-[11px] text-zinc-500 uppercase tracking-widest mb-3">{children}</p>;
}

export function InsightsScreen() {
  const { insights, insightsLoading, loadInsights } = useEchoStore(
    useShallow((s) => ({
      insights: s.insights,
      insightsLoading: s.insightsLoading,
      loadInsights: s.loadInsights,
    })),
  );

  useEffect(() => {
    loadInsights();
  }, [loadInsights]);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="px-6 pt-6 pb-4">
        <h1 className="text-[18px] font-bold text-white">Insights</h1>
        <p className="text-xs text-zinc-500 mt-0.5">Your emotional patterns over time.</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-6">
        {insightsLoading && !insights && (
          <div className="text-center py-12 text-zinc-500 text-sm">Loading...</div>
        )}

        {insights?.locked && (
          <LockedState conversationsUntilUnlock={insights.conversations_until_unlock} />
        )}

        {insights && !insights.locked && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">

            {/* Stats grid */}
            <div>
              <SectionTitle>Overview</SectionTitle>
              <div className="grid grid-cols-2 gap-2.5">
                <StatCard label="Sessions" value={insights.total_conversations} sub="total conversations" />
                <StatCard label="Streak" value={`${insights.current_streak}d`} sub="days in a row" />
                <StatCard label="Listened" value={`${insights.total_audio_minutes.toFixed(0)}m`} sub="total audio" />
                <StatCard label="Memories" value={insights.total_memories} sub="moments saved" />
              </div>
            </div>

            {/* Emotion breakdown */}
            {insights.emotion_breakdown.length > 0 && (
              <div>
                <SectionTitle>Emotions</SectionTitle>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl px-5 py-4 space-y-3.5">
                  {insights.emotion_breakdown.map((item) => (
                    <div key={item.emotion}>
                      <div className="flex justify-between mb-1.5">
                        <span className="text-sm text-zinc-200 capitalize">{item.emotion}</span>
                        <span className="text-xs text-zinc-500">{item.pct.toFixed(0)}%</span>
                      </div>
                      <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-amber-500 rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${item.pct}%` }}
                          transition={{ duration: 0.5, ease: "easeOut" }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top tones */}
            {insights.top_tones.length > 0 && (
              <div>
                <SectionTitle>Common tones</SectionTitle>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl px-5 py-4">
                  <div className="flex flex-wrap gap-2">
                    {insights.top_tones.map((t) => (
                      <span
                        key={t.tone}
                        className="text-xs px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-full text-zinc-300"
                      >
                        {t.tone}
                        <span className="text-zinc-600 ml-1">{t.count}x</span>
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Top voices */}
            {insights.top_voices.length > 0 && (
              <div>
                <SectionTitle>Voices used</SectionTitle>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl px-5 py-4 divide-y divide-zinc-800">
                  {insights.top_voices.map((v, i) => (
                    <div key={v.name} className="flex items-center py-2.5 first:pt-0 last:pb-0">
                      <span className="text-xs text-zinc-600 w-5">{i + 1}</span>
                      <span className="text-sm text-zinc-200 flex-1">{v.name}</span>
                      <span className="text-xs text-zinc-500">{v.count} sessions</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Session stats */}
            <div>
              <SectionTitle>Session stats</SectionTitle>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl px-5 py-4 divide-y divide-zinc-800">
                <div className="flex justify-between items-center py-2.5 first:pt-0">
                  <span className="text-sm text-zinc-400">Avg messages per session</span>
                  <span className="text-sm font-semibold text-white">{insights.average_session_length}</span>
                </div>
                <div className="flex justify-between items-center py-2.5">
                  <span className="text-sm text-zinc-400">Total messages</span>
                  <span className="text-sm font-semibold text-white">{insights.total_messages}</span>
                </div>
                {insights.most_active_style && (
                  <div className="flex justify-between items-center py-2.5 last:pb-0">
                    <span className="text-sm text-zinc-400">Favourite style</span>
                    <span className="text-sm font-semibold text-white capitalize">{insights.most_active_style}</span>
                  </div>
                )}
              </div>
            </div>

          </motion.div>
        )}
      </div>
    </div>
  );
}
