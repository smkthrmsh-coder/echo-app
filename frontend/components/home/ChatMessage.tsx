"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { resolveAudioUrl } from "@/lib/api";
import type { EchoMessage } from "@/types";
import { TONE_COLORS } from "@/types";
import { connectAndPlay, stopAmbient } from "@/hooks/useAmbientSound";

interface Props {
  message: EchoMessage;
  onSaveMemory: (msg: EchoMessage) => void;
  onAudioPlay?: (audio: HTMLAudioElement) => void;
  onFollowUp?: (response: string) => void;
  autoPlay?: boolean;
  isLastAssistant?: boolean;
  experienceTitle?: string;
}

const FOLLOW_UP_OPTIONS = [
  { label: "Feeling better", emoji: "✨" },
  { label: "A little better", emoji: "🌱" },
  { label: "About the same", emoji: "💭" },
  { label: "Hear another perspective", emoji: "🔄" },
] as const;

const SPEEDS = [0.8, 1.0, 1.25, 1.5] as const;

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function cleanDisplay(text: string): string {
  return text
    .replace(/<break\s+[^>]*\/?>/g, "")
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/`([^`]+)`/g, "$1")
    .trim();
}

function PlayIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 12 12" fill="currentColor">
      <path d="M2.5 1.8l7 4.2-7 4.2z" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
      <rect x="2" y="1.5" width="2.8" height="9" rx="1" />
      <rect x="7.2" y="1.5" width="2.8" height="9" rx="1" />
    </svg>
  );
}

function ReplayIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46A7.93 7.93 0 0020 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74A7.93 7.93 0 004 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z" />
    </svg>
  );
}

export function ChatMessage({
  message,
  onSaveMemory,
  onAudioPlay,
  onFollowUp,
  autoPlay = false,
  isLastAssistant = false,
  experienceTitle,
}: Props) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(message.duration_seconds ?? 0);
  const [speedIdx, setSpeedIdx] = useState(1);
  const [audioError, setAudioError] = useState(false);
  const [ended, setEnded] = useState(false);

  const isUser = message.role === "user";
  const audioUrl = message.audio_url ? resolveAudioUrl(message.audio_url) : null;
  const accentColor = TONE_COLORS[message.tone] ?? "#d97706";

  // Auto-play via AudioContext (bypasses iOS autoplay restriction)
  useEffect(() => {
    if (!autoPlay || !audioUrl || !audioRef.current) return;
    const audio = audioRef.current;

    const tryPlay = () => {
      // connectAndPlay awaits ctx.resume() then calls play() — works on iOS
      connectAndPlay(audio).then((started) => {
        if (!started) {
          // AudioContext not available (e.g. first load before any gesture)
          // Try native play as last resort — will work on desktop, may fail on iOS
          audio.play().catch(() => {});
        }
      });
    };

    if (audio.readyState >= 2) {
      tryPlay();
    } else {
      audio.addEventListener("canplay", tryPlay, { once: true });
      return () => audio.removeEventListener("canplay", tryPlay);
    }
  }, [autoPlay, audioUrl]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = SPEEDS[speedIdx];
    }
  }, [speedIdx]);

  function togglePlay() {
    if (!audioRef.current) return;
    if (playing) audioRef.current.pause();
    else audioRef.current.play().catch(() => {});
  }

  function replay() {
    if (!audioRef.current) return;
    audioRef.current.currentTime = 0;
    setEnded(false);
    audioRef.current.play().catch(() => {});
  }

  function seek(e: React.MouseEvent<HTMLDivElement>) {
    if (!audioRef.current) return;
    const rect = e.currentTarget.getBoundingClientRect();
    audioRef.current.currentTime = ((e.clientX - rect.left) / rect.width) * (audioRef.current.duration || 0);
  }

  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-end"
      >
        <div className="bg-zinc-800 border border-zinc-700/50 rounded-2xl rounded-tr-sm px-4 py-3 max-w-[82%]">
          <p className="text-sm text-zinc-100 leading-relaxed">{cleanDisplay(message.content)}</p>
        </div>
      </motion.div>
    );
  }

  const remaining = duration - currentTime;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="flex flex-col gap-2.5"
    >
      {/* Transcript bubble */}
      <div
        className="rounded-2xl rounded-tl-sm px-4 py-3.5 max-w-[92%]"
        style={{
          background: "linear-gradient(135deg, rgba(24,24,27,0.95) 0%, rgba(20,20,22,0.98) 100%)",
          border: "1px solid rgba(63,63,70,0.5)",
        }}
      >
        {/* Tone chip */}
        {message.tone && (
          <div className="flex items-center gap-1.5 mb-2.5">
            <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ backgroundColor: accentColor }} />
            <span className="text-[10px] font-medium tracking-wide uppercase" style={{ color: accentColor, opacity: 0.9 }}>
              {message.tone}
            </span>
          </div>
        )}

        {/* Transcript — broken into paragraphs for breathing room */}
        {cleanDisplay(message.content)
          .split(/(?<=\.) +(?=[A-Z"])/)
          .reduce<string[]>((acc, s) => {
            const last = acc[acc.length - 1];
            if (!last || last.split(" ").length > 20) {
              acc.push(s);
            } else {
              acc[acc.length - 1] = last + " " + s;
            }
            return acc;
          }, [])
          .map((para, i) => (
            <p key={i} className={`text-sm text-zinc-200 leading-relaxed ${i > 0 ? "mt-2" : ""}`}>
              {para}
            </p>
          ))}
      </div>

      {/* Premium audio player */}
      {audioUrl && !audioError && (
        <div
          className="max-w-[92%] rounded-2xl px-4 py-3.5"
          style={{
            background: "linear-gradient(135deg, rgba(17,17,19,0.97) 0%, rgba(13,13,15,0.99) 100%)",
            border: "1px solid rgba(63,63,70,0.4)",
          }}
        >
          <audio
            ref={audioRef}
            src={audioUrl}
            preload="auto"
            onPlay={() => {
              setPlaying(true);
              stopAmbient(1200); // fade out ambient when voice starts
              if (audioRef.current) onAudioPlay?.(audioRef.current);
            }}
            onPause={() => setPlaying(false)}
            onEnded={() => { setPlaying(false); setEnded(true); }}
            onError={() => setAudioError(true)}
            onLoadedMetadata={() => {
              if (audioRef.current?.duration) setDuration(audioRef.current.duration);
            }}
            onTimeUpdate={() => {
              if (!audioRef.current) return;
              const ct = audioRef.current.currentTime;
              const dur = audioRef.current.duration || 0;
              setCurrentTime(ct);
              setProgress(dur ? ct / dur : 0);
            }}
          />

          {/* Experience title */}
          {experienceTitle && (
            <p className="text-[10px] font-medium text-zinc-500 tracking-wide uppercase mb-2.5 truncate">
              {experienceTitle}
            </p>
          )}

          {/* Controls row */}
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="w-9 h-9 rounded-full flex items-center justify-center text-black flex-shrink-0 transition-transform active:scale-90"
              style={{ backgroundColor: accentColor }}
            >
              {playing ? <PauseIcon /> : <PlayIcon />}
            </button>

            {/* Scrubber + times */}
            <div className="flex-1 flex flex-col gap-1.5">
              <div
                className="h-[3px] rounded-full cursor-pointer overflow-hidden"
                style={{ backgroundColor: "rgba(63,63,70,0.5)" }}
                onClick={seek}
              >
                <motion.div
                  className="h-full rounded-full"
                  style={{ width: `${progress * 100}%`, backgroundColor: accentColor }}
                  transition={{ duration: 0.1 }}
                />
              </div>
              <div className="flex justify-between">
                <span className="text-[10px] text-zinc-600 tabular-nums">{formatTime(currentTime)}</span>
                <span className="text-[10px] text-zinc-600 tabular-nums">
                  -{formatTime(Math.max(0, remaining))}
                </span>
              </div>
            </div>
          </div>

          {/* Secondary controls */}
          <div className="flex items-center gap-4 mt-2.5 pl-12">
            <button onClick={replay} className="flex items-center gap-1 text-zinc-600 hover:text-zinc-400 transition-colors">
              <ReplayIcon />
            </button>
            <button
              onClick={() => setSpeedIdx((i) => (i + 1) % SPEEDS.length)}
              className="text-[11px] text-zinc-600 hover:text-zinc-400 transition-colors tabular-nums font-mono"
            >
              {SPEEDS[speedIdx]}×
            </button>
          </div>
        </div>
      )}

      {/* End-of-experience follow-up — appears when last audio finishes */}
      <AnimatePresence>
        {isLastAssistant && ended && onFollowUp && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="max-w-[92%]"
          >
            <p className="text-[12px] text-zinc-500 mb-2.5 px-0.5">How are you feeling now?</p>
            <div className="flex flex-wrap gap-2">
              {FOLLOW_UP_OPTIONS.map(({ label, emoji }) => (
                <button
                  key={label}
                  onClick={() => onFollowUp(label)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-zinc-800 bg-zinc-900/60 text-[12px] text-zinc-300 hover:border-zinc-700 hover:text-white transition-all active:scale-95"
                >
                  <span>{emoji}</span>
                  <span>{label}</span>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Save to memory */}
      {message.role === "assistant" && (
        <button
          onClick={() => onSaveMemory(message)}
          className="text-[11px] text-zinc-700 hover:text-zinc-500 transition-colors w-fit ml-0.5"
        >
          Save to memory
        </button>
      )}
    </motion.div>
  );
}
