"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useEchoStore } from "@/store/useEchoStore";
import { apiLogin, apiSignup } from "@/lib/api";
import { setAuthToken } from "@/lib/auth";

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

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
      <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
      <path d="M3.964 10.706A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.038l3.007-2.332z" fill="#FBBC05"/>
      <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.962L3.964 7.294C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
    </svg>
  );
}

type AuthTab = "signin" | "signup";

export function LoginScreen() {
  const loginWithToken = useEchoStore((s) => s.loginWithToken);
  const loginWithGoogle = useEchoStore((s) => s.loginWithGoogle);

  const [tab, setTab] = useState<AuthTab>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      let resp;
      if (tab === "signin") {
        resp = await apiLogin(email.trim(), password);
      } else {
        if (!email.trim() || password.length < 4) {
          setError("Please fill in all fields (password min 4 characters).");
          setLoading(false);
          return;
        }
        resp = await apiSignup(email.trim(), password, displayName.trim() || undefined);
      }
      setAuthToken(resp.access_token);
      loginWithToken(
        resp.access_token,
        resp.user.display_name || resp.user.email.split("@")[0],
        resp.user.id,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full bg-black overflow-y-auto">

      {/* Brand header */}
      <div className="relative px-6 pt-12 pb-8 overflow-hidden flex-shrink-0">
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
          <div className="flex items-center gap-[5px] mb-4">
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
        transition={{ delay: 0.1, duration: 0.4 }}
        className="px-6 mb-6 space-y-2.5 flex-shrink-0"
      >
        {FEATURES.map((f) => (
          <div key={f} className="flex items-start gap-3">
            <CheckIcon />
            <span className="text-sm text-zinc-300 leading-snug">{f}</span>
          </div>
        ))}
      </motion.div>

      <div className="h-px bg-zinc-900 mx-6 mb-6 flex-shrink-0" />

      {/* Auth form */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.18, duration: 0.4 }}
        className="px-6 flex-1"
      >
        {/* Tab switcher */}
        <div className="flex bg-zinc-900 rounded-xl p-1 mb-5">
          {(["signin", "signup"] as AuthTab[]).map((t) => (
            <button
              key={t}
              onClick={() => { setTab(t); setError(""); }}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                tab === t
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {t === "signin" ? "Sign In" : "Create Account"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <AnimatePresence mode="wait">
            {tab === "signup" && (
              <motion.div
                key="displayName"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
              >
                <label className="block text-sm text-zinc-400 font-medium mb-1.5">Your name (optional)</label>
                <input
                  type="text"
                  autoComplete="name"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3.5 text-white placeholder-zinc-600 text-sm focus:outline-none focus:border-amber-500 transition-colors"
                  placeholder="What should Echo call you?"
                />
              </motion.div>
            )}
          </AnimatePresence>

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
              autoComplete={tab === "signin" ? "current-password" : "new-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3.5 text-white placeholder-zinc-600 text-sm focus:outline-none focus:border-amber-500 transition-colors"
              placeholder={tab === "signup" ? "Choose a password (min 4 chars)" : "Enter your password"}
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
            {loading ? (tab === "signin" ? "Signing in..." : "Creating account...") : (tab === "signin" ? "Sign In" : "Create Account")}
          </motion.button>
        </form>

        {/* Divider */}
        <div className="flex items-center gap-3 my-4">
          <div className="flex-1 h-px bg-zinc-800" />
          <span className="text-xs text-zinc-600">or</span>
          <div className="flex-1 h-px bg-zinc-800" />
        </div>

        {/* Google OAuth */}
        <motion.button
          onClick={loginWithGoogle}
          whileTap={{ scale: 0.98 }}
          className="w-full flex items-center justify-center gap-2.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 text-white font-medium rounded-xl py-3.5 text-sm transition-all"
        >
          <GoogleIcon />
          Continue with Google
        </motion.button>

        <p className="text-xs text-zinc-600 text-center mt-5 pb-6">
          Secured · Built for personal wellbeing
        </p>
      </motion.div>
    </div>
  );
}
