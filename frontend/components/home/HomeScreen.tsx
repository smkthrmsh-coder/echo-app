"use client";

import { AnimatePresence } from "framer-motion";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";
import { WelcomeView } from "./WelcomeView";
import { IntentionStep } from "./IntentionStep";
import { CreationStep4 } from "./CreationStep4";
import { ChatView } from "./ChatView";

export function HomeScreen() {
  const { homeMode, isCreating, createError } = useEchoStore(
    useShallow((s) => ({
      homeMode: s.homeMode,
      isCreating: s.isCreating,
      createError: s.createError,
    })),
  );

  if (homeMode === "chat") {
    return (
      <div className="flex flex-col h-full overflow-hidden">
        <ChatView />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden relative">
      <AnimatePresence mode="wait">
        {homeMode === "welcome" && <WelcomeView key="welcome" />}
        {homeMode === "creation" && (isCreating || createError) && (
          <CreationStep4 key="generating" />
        )}
        {homeMode === "creation" && !isCreating && !createError && (
          <IntentionStep key="intention" />
        )}
      </AnimatePresence>
    </div>
  );
}
