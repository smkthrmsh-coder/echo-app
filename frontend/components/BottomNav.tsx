"use client";

import { motion } from "framer-motion";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";
import type { Tab } from "@/store/useEchoStore";

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  {
    id: "home",
    label: "Home",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
  },
  {
    id: "journeys",
    label: "Journeys",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    ),
  },
  {
    id: "insights",
    label: "Insights",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
  },
  {
    id: "profile",
    label: "Profile",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
];

export function BottomNav() {
  const { tab, setTab } = useEchoStore(useShallow((s) => ({ tab: s.tab, setTab: s.setTab })));

  return (
    <div
      className="flex items-center justify-around px-2 pt-3 border-t border-zinc-900 bg-black/95 backdrop-blur-sm"
      style={{ paddingBottom: "max(12px, env(safe-area-inset-bottom, 12px))" }}
    >
      {TABS.map((t) => {
        const active = tab === t.id;
        return (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className="flex flex-col items-center gap-1 min-w-[60px] py-1 relative"
          >
            <span className={`transition-colors ${active ? "text-amber-400" : "text-zinc-600"}`}>
              {t.icon}
            </span>
            <span
              className={`text-[9px] uppercase tracking-widest font-medium transition-colors ${
                active ? "text-amber-400" : "text-zinc-600"
              }`}
            >
              {t.label}
            </span>
            {active && (
              <motion.div
                layoutId="nav-dot"
                className="absolute -bottom-1 w-1 h-1 rounded-full bg-amber-400"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
          </button>
        );
      })}
    </div>
  );
}
