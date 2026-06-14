"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useEchoStore } from "@/store/useEchoStore";

const FEATURES = [
  "Voice that responds to how you actually feel",
  "Guided programs for sleep, focus & confidence",
  "Tracks your emotional patterns over time",
];

function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="flex-shrink-0 mt-0.5">
      <circle cx="8" cy="8" r="7.25" stroke="#d97706" strokeWidth="1.5" />
      <path d="M5 8l2 2 4-4" stroke="#d97706" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function LoginScreen() {
  const login = useEchoStore((s) => s.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    setTimeout(() => {
      const ok = login(email, password);
      if (!ok) setError("Incorrect email or password.");
      setLoading(false);
    }, 600);
  }

  return (
    <div className="flex flex-col h-full bg-black overflow-y-auto">

      {/* Brand header */}
      <div className="relative px-6 pt-14 pb-10 overflow-hidden flex-shrink-0">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse 70% 50% at 50% 0%, rgba(217,119,6,0.14), transparent)" }}
        />
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="relative z-10"
        >
          {/* Waveform mark */}
          <div className="flex items-center gap-[5px] mb-5">
            {[0.4, 0.7, 1, 0.85, 0.55].map((h, i) => (
              <motion.div
                key={i}
                className="w-[3px] rounded-full bg-amber-500"
                animate={{ scaleY: [h, 1, h], opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.8, repeat: Infinity, delay: i * 0.18, ease: "easeInOut" }}
                style={{ height: 22, transformOrigin: "center" }}
              />
            ))}
          </div>
          <h1 className="text-[28px] font-bold text-white tracking-tight leading-none mb-1">Echo</h1>
          <p className="text-sm text-zinc-400">Your personal AI voice companion</p>
        </motion.div>
      </div>

      {/* Feature list */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.12, duration: 0.4 }}
        className="px-6 mb-8 space-y-3 flex-shrink-0"
      >
        {FEATURES.map((f) => (
          <div key={f} className="flex items-start gap-3">
            <CheckIcon />
            <span className="text-sm text-zinc-300 leading-snug">{f}</span>
          </div>
        ))}
      </motion.div>

      {/* Divider */}
      <div className="h-px bg-zinc-900 mx-6 mb-7 flex-shrink-0" />

      {/* Sign in form */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.4 }}
        className="px-6 flex-1"
      >
        <h2 className="text-[17px] font-semibold text-white mb-5">Sign in to continue</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-zinc-400 font-medium mb-1.5">Email address</label>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3.5 text-white placeholder-zinc-600 text-sm focus:outline-none focus:border-amber-500 transition-colors"
              placeholder="you@example.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-zinc-400 font-medium mb-1.5">Password</label>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3.5 text-white placeholder-zinc-600 text-sm focus:outline-none focus:border-amber-500 transition-colors"
              placeholder="Enter your password"
              required
            />
          </div>

          {error && (
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-400 text-sm">
              {error}
            </motion.p>
          )}

          <motion.button
            type="submit"
            disabled={loading}
            whileTap={{ scale: 0.98 }}
            className="w-full bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-semibold rounded-xl py-3.5 text-sm transition-colors"
          >
            {loading ? "Signing in..." : "Sign In"}
          </motion.button>
        </form>

        <p className="text-xs text-zinc-600 text-center mt-5">
          Secured · Built for personal wellbeing
        </p>
      </motion.div>

      <div className="h-8 flex-shrink-0" />
    </div>
  );
}
