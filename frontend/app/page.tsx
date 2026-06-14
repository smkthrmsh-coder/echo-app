"use client";

import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useEchoStore } from "@/store/useEchoStore";
import { SplashScreen } from "@/components/SplashScreen";
import { LoginScreen } from "@/components/LoginScreen";
import { BottomNav } from "@/components/BottomNav";
import { HomeScreen } from "@/components/home/HomeScreen";
import { JourneyScreen } from "@/components/JourneyScreen";
import { InsightsScreen } from "@/components/InsightsScreen";
import { ProfileScreen } from "@/components/ProfileScreen";

const TAB_MOTION = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.2 },
};

function MainApp() {
  const tab = useEchoStore((s) => s.tab);

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-hidden relative">
        <AnimatePresence mode="wait">
          {tab === "home" && (
            <motion.div key="home" className="absolute inset-0" {...TAB_MOTION}>
              <HomeScreen />
            </motion.div>
          )}
          {tab === "journeys" && (
            <motion.div key="journeys" className="absolute inset-0" {...TAB_MOTION}>
              <JourneyScreen />
            </motion.div>
          )}
          {tab === "insights" && (
            <motion.div key="insights" className="absolute inset-0" {...TAB_MOTION}>
              <InsightsScreen />
            </motion.div>
          )}
          {tab === "profile" && (
            <motion.div key="profile" className="absolute inset-0" {...TAB_MOTION}>
              <ProfileScreen />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      <BottomNav />
    </div>
  );
}

export default function EchoApp() {
  const screen = useEchoStore((s) => s.screen);

  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, []);

  return (
    // Mobile: full black screen. Desktop: dark bg with centered phone frame.
    <div className="bg-black h-dvh md:bg-zinc-950 md:h-auto md:min-h-screen md:flex md:items-center md:justify-center md:p-4">
      <div
        className="relative bg-black overflow-hidden flex flex-col w-full h-dvh md:w-[390px] md:h-[844px] md:rounded-[40px]"
        style={{
          boxShadow:
            "0 0 0 1px rgba(255,255,255,0.06), 0 32px 80px rgba(0,0,0,0.8), 0 0 60px rgba(245,166,35,0.04)",
        }}
      >
        {/* Dynamic Island / notch safe area — only on real phones, hidden inside desktop frame */}
        <div
          className="flex-shrink-0 md:hidden"
          style={{ height: "env(safe-area-inset-top, 0px)" }}
        />

        {/* Screen content fills remaining height */}
        <div className="flex-1 relative overflow-hidden">
          <AnimatePresence mode="wait">
            {screen === "splash" && (
              <motion.div
                key="splash"
                className="absolute inset-0"
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
              >
                <SplashScreen />
              </motion.div>
            )}
            {screen === "login" && (
              <motion.div
                key="login"
                className="absolute inset-0"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                <LoginScreen />
              </motion.div>
            )}
            {screen === "home" && (
              <motion.div
                key="main"
                className="absolute inset-0"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                <MainApp />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
