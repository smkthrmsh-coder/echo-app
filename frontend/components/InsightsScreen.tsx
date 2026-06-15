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

function StatCard({ label, value, sub, accent }: { label: string; value: string | number; sub?: string; accent?: string }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl px-4 py-4">
      <p className="text-[11px] text-zinc-500 uppercase tracking-widest mb-2">{label}</p>
      <p className="text-[26px] font-bold leading-none" style={{ color: accent ?? "#ffffff" }}>{value}</p>
      {sub && <p className="text-[11px] text-zinc-500 mt-1.5">{sub}</p>}
    </div>
  );
}

function WeekActivity({ activity }: { activity: boolean[] }) {
  const days = ["M", "T", "W", "T", "F", "S", "S"];
  const today = new Date().getDay();
  const orderedDays = [...days.slice(today), ...days.slice(0, today)].slice(-7);

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl px-5 py-4">
      <div className="flex justify-between items-end">
        {activity.map((active, i) => (
          <div key={i} className="flex flex-col items-center gap-2">
            <motion.div
              initial={{ scaleY: 0 }}
              animate={{ scaleY: 1 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
              className="w-8 rounded-lg origin-bottom"
              style={{
                height: active ? "32px" : "16px",
                backgroundColor: active ? "#f59e0b" : "#27272a",
              }}
            />
            <span className="text-[10px] text-zinc-600">{orderedDays[i]}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function CompanionCard({ name }: { name: string }) {
  const COMPANION_EMOJIS: Record<string, string> = {
    Sofia: "✨", Marcus: "🌊", Alex: "⚡", Luna: "🌙",
    James: "🎯", Charlie: "😊", Nova: "🔥", River: "🌿", Atlas: "🏔",
  };
  const emoji = COMPANION_EMOJIS[name] ?? "🎙";
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl px-5 py-4 flex items-center gap-4">
      <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center flex-shrink-0">
        <span className="text-xl">{emoji}</span>
      </div>
      <div>
        <p className="text-[11px] text-zinc-500 uppercase tracking-widest mb-0.5">Favourite companion</p>
        <p className="text-[16px] font-bold text-white">{name}</p>
        <p className="text-xs text-zinc-500 mt-0.5">Your most-used voice</p>
      </div>
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
      <h3 className="text-[17px] font-bold text-white mb-2">Reflection unlocks soon</h3>
      <p className="text-sm text-zinc-400 leading-relaxed mb-7 max-w-[260px]">
        Have {conversationsUntilUnlock} more conversation{conversationsUntilUnlock !== 1 ? "s" : ""} with Echo to unlock your personal patterns and emotion trends.
      </p>

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
        <h1 className="text-[18px] font-bold text-white">Reflection</h1>
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

            {/* Overview stats */}
            <div>
              <SectionTitle>Overview</SectionTitle>
              <div className="grid grid-cols-2 gap-2.5">
                <StatCard
                  label="Sessions"
                  value={insights.total_conversations}
                  sub="total conversations"
                  accent="#f59e0b"
                />
                <StatCard
                  label="Streak"
                  value={`${insights.current_streak}d`}
                  sub="days in a row"
                  accent="#34d399"
                />
                <StatCard
                  label="Listened"
                  value={`${insights.total_audio_minutes.toFixed(0)}m`}
                  sub="total audio"
                  accent="#a78bfa"
                />
                <StatCard
                  label="Memories"
                  value={insights.total_memories}
                  sub="moments saved"
                  accent="#60a5fa"
                />
              </div>
            </div>

            {/* Weekly activity */}
            {insights.weekly_activity && (
              <div>
                <SectionTitle>This week</SectionTitle>
                <WeekActivity activity={insights.weekly_activity} />
              </div>
            )}

            {/* Favourite companion */}
            {insights.favourite_companion && (
              <div>
                <SectionTitle>Your companion</SectionTitle>
                <CompanionCard name={insights.favourite_companion} />
              </div>
            )}

            {/* Emotion breakdown */}
            {insights.emotion_breakdown.length > 0 && (
              <div>
                <SectionTitle>Emotional themes</SectionTitle>
                <div className="bg-zinc-900 border border-zinc-800 rounded-2xl px-5 py-4 space-y-4">
                  {insights.emotion_breakdown.map((item) => (
                    <div key={item.emotion}>
                      <div className="flex justify-between mb-1.5">
                        <span className="text-sm text-zinc-200 capitalize">{item.emotion}</span>
                        <span className="text-xs text-zinc-500">{item.pct.toFixed(0)}%</span>
                      </div>
                      <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
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
                <div className="bg-zinc-900 border border-zinc-800 rounded-2xl px-5 py-4">
                  <div className="flex flex-wrap gap-2">
                    {insights.top_tones.map((t) => (
                      <span
                        key={t.tone}
                        className="text-xs px-3 py-1.5 bg-zinc-800 border border-zinc-700/60 rounded-full text-zinc-300"
                      >
                        {t.emoji} {t.tone}
                        <span className="text-zinc-600 ml-1.5">{t.count}×</span>
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Voices */}
            {insights.top_voices.length > 0 && (
              <div>
                <SectionTitle>Voices used</SectionTitle>
                <div className="bg-zinc-900 border border-zinc-800 rounded-2xl px-5 py-4 divide-y divide-zinc-800/80">
                  {insights.top_voices.map((v, i) => (
                    <div key={v.name} className="flex items-center py-3 first:pt-0 last:pb-0">
                      <span className="text-xs text-zinc-700 w-5 font-mono">{i + 1}</span>
                      <span className="text-sm text-zinc-200 flex-1 font-medium">{v.name}</span>
                      <span className="text-xs text-zinc-500">{v.count} sessions</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Session stats */}
            <div>
              <SectionTitle>Session details</SectionTitle>
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl px-5 py-4 divide-y divide-zinc-800/80">
                <div className="flex justify-between items-center py-3 first:pt-0">
                  <span className="text-sm text-zinc-400">Total messages</span>
                  <span className="text-sm font-semibold text-white">{insights.total_messages}</span>
                </div>
                <div className="flex justify-between items-center py-3">
                  <span className="text-sm text-zinc-400">Avg session length</span>
                  <span className="text-sm font-semibold text-white">{insights.average_session_length} min</span>
                </div>
                {insights.most_active_style && (
                  <div className="flex justify-between items-center py-3 last:pb-0">
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
