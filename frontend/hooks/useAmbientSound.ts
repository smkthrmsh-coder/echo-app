"use client";

import type { IntentionId } from "@/types";

// Harmonic frequencies tuned per emotional intention
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

// Module-level singleton — survives React re-renders
let _ctx: AudioContext | null = null;
let _masterGain: GainNode | null = null;
let _oscillators: OscillatorNode[] = [];
const _connectedElements = new WeakSet<HTMLAudioElement>();

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
 */
export function startAmbient(intention: IntentionId | null): void {
  if (typeof window === "undefined") return;

  const key = intention ?? "other";
  const freqs = INTENTION_HARMONICS[key] ?? INTENTION_HARMONICS.other;
  const gain = INTENTION_GAIN[key] ?? 0.012;

  try {
    const ctx = getOrCreateContext();
    if (ctx.state === "suspended") ctx.resume();

    // Stop any previous oscillators
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

    // Fade in over 600ms
    _masterGain!.gain.cancelScheduledValues(ctx.currentTime);
    _masterGain!.gain.setValueAtTime(0, ctx.currentTime);
    _masterGain!.gain.linearRampToValueAtTime(1, ctx.currentTime + 0.6);
  } catch {
    // AudioContext blocked — silent fail
  }
}

/**
 * Fade out and stop the ambient pad.
 * Call when voice audio begins playing.
 */
export function stopAmbient(durationMs = 1200): void {
  try {
    if (!_ctx || !_masterGain || _oscillators.length === 0) return;
    const ctx = _ctx;
    const mg = _masterGain;
    const dur = durationMs / 1000;
    mg.gain.cancelScheduledValues(ctx.currentTime);
    mg.gain.setValueAtTime(mg.gain.value, ctx.currentTime);
    mg.gain.linearRampToValueAtTime(0, ctx.currentTime + dur);
    const oscs = [..._oscillators];
    _oscillators = [];
    setTimeout(() => {
      oscs.forEach((o) => { try { o.stop(); } catch {} });
    }, durationMs + 100);
  } catch {}
}

/**
 * Connect an <audio> element to the shared AudioContext, resume it, then play.
 *
 * Why this works on iOS:
 * - AudioContext was created + unlocked during the "Hear What You Need" button press
 * - iOS only requires a gesture to CREATE the context, not to use it later
 * - MediaElementSource connected to an unlocked context can play at any time
 * - We await ctx.resume() before play() so the context is guaranteed running
 *
 * Returns true if playback started successfully.
 */
export async function connectAndPlay(el: HTMLAudioElement): Promise<boolean> {
  if (typeof window === "undefined") return false;
  try {
    const ctx = getOrCreateContext();

    // Must be awaited — iOS context can be suspended and resume() is async
    if (ctx.state === "suspended") await ctx.resume();
    if (ctx.state !== "running") return false;

    // Connect once — createMediaElementSource throws if called twice on same element
    if (!_connectedElements.has(el)) {
      const source = ctx.createMediaElementSource(el);
      source.connect(ctx.destination);
      _connectedElements.add(el);
    }

    await el.play();
    return true;
  } catch {
    // Falls back to native play button — visible to user
    return false;
  }
}
