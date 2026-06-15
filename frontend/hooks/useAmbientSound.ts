"use client";

import { useEffect, useRef } from "react";
import type { IntentionId } from "@/types";

// Harmonic frequencies tuned per emotional intention
// Low-volume sine pad — barely audible, fills silence intentionally
const INTENTION_HARMONICS: Record<string, number[]> = {
  peace:        [174, 285, 396],
  comfort:      [220, 277, 330],
  sleep:        [136, 204, 272],
  listen:       [192, 256, 320],
  focus:        [432, 528, 648],
  clarity:      [396, 528, 660],
  encouragement:[264, 330, 440],
  motivation:   [330, 415, 495],
  confidence:   [264, 396, 528],
  energy:       [330, 440, 550],
  other:        [220, 330, 440],
};

const INTENTION_GAIN: Record<string, number> = {
  sleep: 0.018, peace: 0.016, comfort: 0.015, listen: 0.015,
  focus: 0.012, clarity: 0.012, encouragement: 0.012,
  motivation: 0.010, confidence: 0.010, energy: 0.008,
  other: 0.012,
};

interface AmbientHandle {
  fadeOut: (durationMs?: number) => void;
}

// Module-level context — survives React re-renders, avoids duplicate contexts
let _ctx: AudioContext | null = null;
let _masterGain: GainNode | null = null;
let _oscillators: OscillatorNode[] = [];

function getOrCreateContext(): AudioContext {
  if (!_ctx || _ctx.state === "closed") {
    _ctx = new AudioContext();
    _masterGain = _ctx.createGain();
    _masterGain.gain.value = 0;
    _masterGain.connect(_ctx.destination);
  }
  return _ctx;
}

/**
 * Start ambient harmonic pad for the given intention.
 * Must be called synchronously within a user gesture handler.
 * Returns a handle to fade the sound out.
 */
export function startAmbient(intention: IntentionId | null): AmbientHandle {
  if (typeof window === "undefined") return { fadeOut: () => {} };

  const key = intention ?? "other";
  const freqs = INTENTION_HARMONICS[key] ?? INTENTION_HARMONICS.other;
  const gain = INTENTION_GAIN[key] ?? 0.012;

  try {
    const ctx = getOrCreateContext();
    if (ctx.state === "suspended") ctx.resume();

    // Stop any existing oscillators
    _oscillators.forEach((o) => { try { o.stop(); } catch {} });
    _oscillators = [];

    freqs.forEach((freq) => {
      const osc = ctx.createOscillator();
      const oscGain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = freq;
      oscGain.gain.value = gain;
      osc.connect(oscGain);
      oscGain.connect(_masterGain!);
      osc.start();
      _oscillators.push(osc);
    });

    // Fade in over 800ms
    _masterGain!.gain.cancelScheduledValues(ctx.currentTime);
    _masterGain!.gain.setValueAtTime(0, ctx.currentTime);
    _masterGain!.gain.linearRampToValueAtTime(1, ctx.currentTime + 0.8);
  } catch {
    // AudioContext blocked — silently fail
  }

  return {
    fadeOut: (durationMs = 1500) => {
      try {
        if (!_ctx || !_masterGain) return;
        const ctx = _ctx;
        const mg = _masterGain;
        const dur = durationMs / 1000;
        mg.gain.cancelScheduledValues(ctx.currentTime);
        mg.gain.setValueAtTime(mg.gain.value, ctx.currentTime);
        mg.gain.linearRampToValueAtTime(0, ctx.currentTime + dur);
        setTimeout(() => {
          _oscillators.forEach((o) => { try { o.stop(); } catch {} });
          _oscillators = [];
        }, durationMs + 100);
      } catch {}
    },
  };
}

/**
 * Hook that starts ambient on mount and fades out on unmount.
 * Pass `active=false` to suppress (e.g. when audio is playing).
 */
export function useAmbientSound(
  intention: IntentionId | null,
  active: boolean,
): void {
  const handleRef = useRef<AmbientHandle | null>(null);

  useEffect(() => {
    if (!active || !intention) return;
    handleRef.current = startAmbient(intention);
    return () => {
      handleRef.current?.fadeOut(1200);
    };
  }, [intention, active]);
}
