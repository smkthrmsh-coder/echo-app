"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";

function PlayIcon() {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="currentColor">
      <path d="M6 3.5l16 9.5-16 9.5z" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="currentColor">
      <rect x="5" y="3" width="5" height="20" rx="2" />
      <rect x="16" y="3" width="5" height="20" rx="2" />
    </svg>
  );
}

function formatTime(secs: number) {
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function JourneySessionPlayer() {
  const {
    journeySession,
    journeySessionLoading,
    journeySessionError,
    closeJourneySession,
    journeyCheckin,
    activeJourney,
  } = useEchoStore(
    useShallow((s) => ({
      journeySession: s.journeySession,
      journeySessionLoading: s.journeySessionLoading,
      journeySessionError: s.journeySessionError,
      closeJourneySession: s.closeJourneySession,
      journeyCheckin: s.journeyCheckin,
      activeJourney: s.activeJourney,
    })),
  );

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [completed, setCompleted] = useState(false);

  // Reset completed state when a new session opens
  useEffect(() => {
    setCompleted(false);
    setPlaying(false);
    setProgress(0);
    setCurrentTime(0);
  }, [journeySession?.slug, journeySession?.day]);

  async function handleAudioEnd() {
    setPlaying(false);
    setProgress(1);
    if (!journeySession) return;
    try {
      await journeyCheckin(journeySession.slug);
    } catch {
      // silent — state still marked as complete visually
    }
    setCompleted(true);
    setTimeout(() => closeJourneySession(), 2800);
  }

  function togglePlay() {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(() => {});
    }
  }

  const visible = journeySession || journeySessionLoading || journeySessionError;
  if (!visible) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="journey-session"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 20 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="absolute inset-0 z-50 bg-black flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-6 pb-2 flex-shrink-0">
          <div>
            <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-medium">
              {activeJourney?.journey.title ?? journeySession?.slug ?? "Program"}
            </p>
            {journeySession && (
              <p className="text-xs text-zinc-500 mt-0.5">Day {journeySession.day}</p>
            )}
          </div>
          {!completed && (
            <button
              onClick={closeJourneySession}
              className="w-8 h-8 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500 hover:text-zinc-200 transition-colors"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
          )}
        </div>

        {/* Error state */}
        {journeySessionError && !journeySessionLoading && (
          <div className="flex-1 flex flex-col items-center justify-center px-8 text-center gap-4">
            <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 6v5M10 14h.01" stroke="#f87171" strokeWidth="1.8" strokeLinecap="round" />
                <circle cx="10" cy="10" r="9" stroke="#f87171" strokeWidth="1.5" />
              </svg>
            </div>
            <div>
              <p className="text-white font-medium text-sm">Couldn&apos;t load session</p>
              <p className="text-zinc-500 text-xs mt-1 leading-relaxed max-w-[220px]">{journeySessionError}</p>
            </div>
            <button
              onClick={closeJourneySession}
              className="mt-2 px-5 py-2 rounded-lg border border-zinc-800 text-zinc-400 text-sm hover:text-white hover:border-zinc-700 transition-colors"
            >
              Close
            </button>
          </div>
        )}

        {/* Loading */}
        {journeySessionLoading && (
          <div className="flex-1 flex flex-col items-center justify-center gap-5 px-8">
            <div className="flex items-end gap-1">
              {[0, 1, 2, 3, 4].map((i) => (
                <motion.div
                  key={i}
                  className="w-1 bg-zinc-700 rounded-full"
                  animate={{ height: ["10px", "32px", "10px"] }}
                  transition={{ duration: 1, repeat: Infinity, delay: i * 0.13, ease: "easeInOut" }}
                />
              ))}
            </div>
            <p className="text-zinc-500 text-sm">Preparing your session...</p>
          </div>
        )}

        {/* Session player */}
        {journeySession && !journeySessionLoading && (
          <>
            <audio
              ref={audioRef}
              src={journeySession.audioUrl}
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
              onEnded={handleAudioEnd}
              onTimeUpdate={() => {
                if (!audioRef.current?.duration) return;
                setCurrentTime(audioRef.current.currentTime);
                setProgress(audioRef.current.currentTime / audioRef.current.duration);
              }}
            />

            {/* Completed state */}
            {completed ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex-1 flex flex-col items-center justify-center px-8 text-center gap-5"
              >
                <div className="w-16 h-16 rounded-full bg-green-500/15 border border-green-500/25 flex items-center justify-center">
                  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                    <path d="M6 14l5.5 5.5L22 9" stroke="#4ade80" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <div>
                  <p className="text-white font-semibold text-[17px]">Session complete</p>
                  <p className="text-zinc-500 text-sm mt-1.5 leading-relaxed">
                    Day {journeySession.day} done.{"\n"}See you tomorrow.
                  </p>
                </div>
              </motion.div>
            ) : (
              <div className="flex-1 flex flex-col justify-between px-6 pb-6">
                {/* Waveform + topic */}
                <div className="flex-1 flex flex-col items-center justify-center gap-8 px-4">
                  <div className="flex items-end gap-1.5">
                    {[0, 1, 2, 3, 4, 5, 6].map((i) => (
                      <motion.div
                        key={i}
                        className="w-0.5 rounded-full bg-zinc-600"
                        animate={
                          playing
                            ? { height: ["6px", `${10 + Math.abs(Math.sin(i * 0.9)) * 14}px`, "6px"] }
                            : { height: "6px" }
                        }
                        transition={
                          playing
                            ? { duration: 0.65 + i * 0.06, repeat: Infinity, delay: i * 0.09, ease: "easeInOut" }
                            : { duration: 0.22, ease: "easeOut" }
                        }
                      />
                    ))}
                  </div>

                  <div className="text-center max-w-xs">
                    <p className="text-zinc-400 text-sm leading-relaxed">{journeySession.todayPrompt}</p>
                  </div>
                </div>

                {/* Controls */}
                <div className="space-y-5">
                  {/* Progress */}
                  <div>
                    <div
                      className="w-full h-1 bg-zinc-800 rounded-full cursor-pointer mb-2"
                      onClick={(e) => {
                        if (!audioRef.current) return;
                        const rect = e.currentTarget.getBoundingClientRect();
                        audioRef.current.currentTime =
                          ((e.clientX - rect.left) / rect.width) * (audioRef.current.duration || 0);
                      }}
                    >
                      <div
                        className="h-full rounded-full bg-amber-500 transition-all"
                        style={{ width: `${progress * 100}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[11px] text-zinc-600 tabular-nums">
                      <span>{formatTime(currentTime)}</span>
                      <span>{formatTime(journeySession.durationSeconds)}</span>
                    </div>
                  </div>

                  {/* Play button */}
                  <div className="flex items-center justify-center">
                    <motion.button
                      whileTap={{ scale: 0.93 }}
                      onClick={togglePlay}
                      className="w-16 h-16 rounded-full bg-amber-500 hover:bg-amber-400 flex items-center justify-center text-black transition-colors pl-1"
                    >
                      {playing ? <PauseIcon /> : <PlayIcon />}
                    </motion.button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
