"use client";

import { TONE_COLORS } from "@/types";

const TONE_EMOJI: Record<string, string> = {
  energetic: "⚡", calm: "·", fierce: "·", comforting: "·",
  melancholic: "·", playful: "·", mysterious: "·", romantic: "·",
  anxious: "·", hopeful: "·",
};

interface Props {
  tone: string;
  label?: string;
  size?: "sm" | "md";
}

export function EmotionBadge({ tone, label, size = "md" }: Props) {
  const color = TONE_COLORS[tone] ?? "#94a3b8";
  const emoji = TONE_EMOJI[tone] ?? "🎵";
  const text = label ?? tone;

  const padding = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${padding}`}
      style={{ backgroundColor: `${color}22`, color, border: `1px solid ${color}44` }}
    >
      <span>{emoji}</span>
      <span className="capitalize">{text}</span>
    </span>
  );
}
