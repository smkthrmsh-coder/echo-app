"use client";

// Module-level singleton — survives React re-renders; persists for iOS audio playback
let _ctx: AudioContext | null = null;
const _connectedElements = new WeakSet<HTMLAudioElement>();

function getOrCreateContext(): AudioContext {
  if (!_ctx || _ctx.state === "closed") {
    _ctx = new AudioContext();
  }
  return _ctx;
}

/**
 * Create and resume the AudioContext during a user gesture.
 * Must be called within a gesture handler so iOS allows audio playback later
 * without a separate user interaction — iOS only needs a gesture to CREATE
 * the context, not to call play() on it subsequently.
 */
export function unlockAudio(): void {
  if (typeof window === "undefined") return;
  try {
    const ctx = getOrCreateContext();
    if (ctx.state === "suspended") ctx.resume();
  } catch {}
}

/**
 * Connect an <audio> element to the shared AudioContext, resume it, then play.
 * playbackRate is set before play() so it takes effect from the first frame.
 * Returns true if playback started successfully.
 */
export async function connectAndPlay(el: HTMLAudioElement, playbackRate = 1.0): Promise<boolean> {
  if (typeof window === "undefined") return false;
  try {
    const ctx = getOrCreateContext();
    if (ctx.state === "suspended") await ctx.resume();
    if (ctx.state !== "running") return false;
    if (!_connectedElements.has(el)) {
      const source = ctx.createMediaElementSource(el);
      source.connect(ctx.destination);
      _connectedElements.add(el);
    }
    el.playbackRate = playbackRate;
    await el.play();
    return true;
  } catch {
    return false;
  }
}
