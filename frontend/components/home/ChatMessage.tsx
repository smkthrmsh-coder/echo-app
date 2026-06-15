"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { resolveAudioUrl } from "@/lib/api";
import type { EchoMessage } from "@/types";
import { TONE_COLORS } from "@/types";

interface Props {
  message: EchoMessage;
  onSaveMemory: (msg: EchoMessage) => void;
  autoPlay?: boolean;
}

function PlayIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
      <path d="M2 1.5l8 4.5-8 4.5z" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
      <rect x="2" y="1" width="3" height="10" rx="1" />
      <rect x="7" y="1" width="3" height="10" rx="1" />
    </svg>
  );
}

function ReplayIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z" />
    </svg>
  );
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

const SPEEDS = [0.8, 1.0, 1.25, 1.5] as const;

export function ChatMessage({ message, onSaveMemory, autoPlay = false }: Props) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [speedIdx, setSpeedIdx] = useState(1);

  const isUser = message.role === "user";
  const audioUrl = message.audio_url ? resolveAudioUrl(message.audio_url) : null;
  const accentColor = TONE_COLORS[message.tone] ?? "#d97706";

  useEffect(() => {
    if (autoPlay && audioUrl && audioRef.current) {
      audioRef.current.play().catch(() => {});
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
    audioRef.current.play().catch(() => {});
  }

  function cycleSpeed() {
    setSpeedIdx((i) => (i + 1) % SPEEDS.length);
  }

  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-end"
      >
        <div className="bg-zinc-800 border border-zinc-700/60 rounded-2xl rounded-tr-sm px-4 py-3 max-w-[80%]">
          <p className="text-sm text-zinc-100 leading-relaxed">{cleanDisplay(message.content)}</p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-2"
    >
      {/* Message bubble */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl rounded-tl-sm px-4 py-3 max-w-[90%]">
        <p className="text-sm text-zinc-200 leading-relaxed">{cleanDisplay(message.content)}</p>

        {/* Companion + tone attribution */}
        <div className="flex items-center gap-2 mt-2.5 pt-2.5 border-t border-zinc-800/60">
          <span className="inline-block w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: accentColor }} />
          {message.voice_name ? (
            <span className="text-[11px] text-zinc-400 font-medium">{message.voice_name}</span>
          ) : null}
          {message.tone && (
            <>
              {message.voice_name && <span className="text-[11px] text-zinc-700">·</span>}
              <span className="text-[11px] text-zinc-500 capitalize">{message.tone}</span>
            </>
          )}
        </div>
      </div>

      {/* Audio player */}
      {audioUrl && (
        <div className="flex flex-col gap-1.5 max-w-[90%]">
          <audio
            ref={audioRef}
            src={audioUrl}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onEnded={() => { setPlaying(false); setProgress(0); }}
            onTimeUpdate={() => {
              if (!audioRef.current?.duration) return;
              setProgress(audioRef.current.currentTime / audioRef.current.duration);
            }}
          />

          {/* Controls row */}
          <div className="flex items-center gap-2">
            {/* Play/Pause */}
            <button
              onClick={togglePlay}
              className="w-8 h-8 rounded-full flex items-center justify-center text-black flex-shrink-0 transition-transform active:scale-95"
              style={{ backgroundColor: accentColor }}
            >
              {playing ? <PauseIcon /> : <PlayIcon />}
            </button>

            {/* Progress bar */}
            <div
              className="flex-1 h-1 rounded-full bg-zinc-800 cursor-pointer"
              onClick={(e) => {
                if (!audioRef.current) return;
                const rect = e.currentTarget.getBoundingClientRect();
                audioRef.current.currentTime = ((e.clientX - rect.left) / rect.width) * (audioRef.current.duration || 0);
              }}
            >
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${progress * 100}%`, backgroundColor: accentColor }}
              />
            </div>

            {/* Duration */}
            {message.duration_seconds && (
              <span className="text-[11px] text-zinc-600 flex-shrink-0 tabular-nums">
                {Math.round(message.duration_seconds)}s
              </span>
            )}
          </div>

          {/* Secondary controls */}
          <div className="flex items-center gap-3 pl-10">
            <button
              onClick={replay}
              className="text-zinc-600 hover:text-zinc-400 transition-colors"
              title="Replay"
            >
              <ReplayIcon />
            </button>
            <button
              onClick={cycleSpeed}
              className="text-[11px] text-zinc-600 hover:text-zinc-400 transition-colors tabular-nums font-mono"
              title="Playback speed"
            >
              {SPEEDS[speedIdx]}×
            </button>
          </div>
        </div>
      )}

      {/* Save to memory */}
      <button
        onClick={() => onSaveMemory(message)}
        className="text-[11px] text-zinc-600 hover:text-zinc-400 transition-colors w-fit ml-1"
      >
        Save to memory
      </button>
    </motion.div>
  );
}
