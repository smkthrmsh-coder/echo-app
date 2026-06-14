"use client";

import { useEffect, useRef, useState } from "react";
import { TONE_COLORS } from "@/types";

interface Props {
  src: string;
  tone: string;
  title: string;
}

export function AudioPlayer({ src, tone, title }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const accentColor = TONE_COLORS[tone] ?? "#6ee7b7";

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const onTime = () => setCurrentTime(audio.currentTime);
    const onDuration = () => setDuration(audio.duration);
    const onEnded = () => setPlaying(false);
    audio.addEventListener("timeupdate", onTime);
    audio.addEventListener("loadedmetadata", onDuration);
    audio.addEventListener("ended", onEnded);
    return () => {
      audio.removeEventListener("timeupdate", onTime);
      audio.removeEventListener("loadedmetadata", onDuration);
      audio.removeEventListener("ended", onEnded);
    };
  }, [src]);

  const toggle = async () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
    } else {
      await audio.play();
      setPlaying(true);
    }
  };

  const seek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = Number(e.target.value);
  };

  const fmt = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div
      className="rounded-2xl border p-5 space-y-4"
      style={{ borderColor: `${accentColor}44`, background: "#18181b" }}
    >
      <audio ref={audioRef} src={src} preload="metadata" />

      <p className="text-sm font-medium text-zinc-300 truncate">{title}</p>

      {/* Progress bar */}
      <div className="space-y-1">
        <input
          type="range"
          min={0}
          max={duration || 100}
          value={currentTime}
          onChange={seek}
          className="w-full h-1 rounded-full appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, ${accentColor} ${progress}%, #3f3f46 ${progress}%)`,
          }}
        />
        <div className="flex justify-between text-xs text-zinc-500">
          <span>{fmt(currentTime)}</span>
          <span>{fmt(duration)}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex justify-center">
        <button
          onClick={toggle}
          className="w-14 h-14 rounded-full flex items-center justify-center text-2xl font-bold transition-transform active:scale-95"
          style={{ backgroundColor: accentColor, color: "#000" }}
          aria-label={playing ? "Pause" : "Play"}
        >
          {playing ? "⏸" : "▶"}
        </button>
      </div>
    </div>
  );
}
