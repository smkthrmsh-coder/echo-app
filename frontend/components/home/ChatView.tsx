"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useShallow } from "zustand/react/shallow";
import { useEchoStore } from "@/store/useEchoStore";
import { ChatMessage } from "./ChatMessage";
import { VoiceToggle } from "./VoiceToggle";
import type { EchoMessage } from "@/types";

function MicIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {active ? (
        <>
          <rect x="9" y="9" width="6" height="6" rx="1" />
          <rect x="3" y="3" width="18" height="18" rx="2" />
        </>
      ) : (
        <>
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </>
      )}
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

export function ChatView() {
  const {
    conversationTitle,
    messages,
    isSending,
    sendError,
    sendMessage,
    saveMemory,
    resetCreation,
    selectedIntention,
  } = useEchoStore(
    useShallow((s) => ({
      conversationTitle: s.conversationTitle,
      messages: s.messages,
      isSending: s.isSending,
      sendError: s.sendError,
      sendMessage: s.sendMessage,
      saveMemory: s.saveMemory,
      resetCreation: s.resetCreation,
      selectedIntention: s.selectedIntention,
    })),
  );

  const [input, setInput] = useState("");
  const [recording, setRecording] = useState(false);
  const [memoryModal, setMemoryModal] = useState<{ msg: EchoMessage; title: string } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  function stopCurrentAudio() {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
  }

  function handleAudioPlay(audio: HTMLAudioElement) {
    if (currentAudioRef.current && currentAudioRef.current !== audio) {
      currentAudioRef.current.pause();
    }
    currentAudioRef.current = audio;
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  function handleSend() {
    const text = input.trim();
    if (!text || isSending) return;
    stopCurrentAudio();
    setInput("");
    sendMessage(text);
  }

  function handleFollowUp(response: string) {
    stopCurrentAudio();
    if (response === "Hear another perspective") {
      sendMessage("I'd like to hear another perspective on this.");
    } else {
      sendMessage(response);
    }
    setTimeout(() => inputRef.current?.focus(), 300);
  }

  async function startRecording() {
    stopCurrentAudio();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => chunksRef.current.push(e.data);
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await useEchoStore.getState().sendVoiceMessage(blob);
      };
      mr.start();
      mediaRef.current = mr;
      setRecording(true);
    } catch {
      // mic denied
    }
  }

  function stopRecording() {
    mediaRef.current?.stop();
    setRecording(false);
  }

  function openMemoryModal(msg: EchoMessage) {
    setMemoryModal({ msg, title: msg.content.slice(0, 60) });
  }

  async function confirmSaveMemory() {
    if (!memoryModal) return;
    await saveMemory(memoryModal.title, memoryModal.msg.content, memoryModal.msg.id);
    setMemoryModal(null);
  }

  const lastAssistantIndex = messages.reduce(
    (last, msg, i) => (msg.role === "assistant" ? i : last),
    -1,
  );

  // Short title for header (max ~30 chars)
  const headerTitle = conversationTitle.length > 32
    ? conversationTitle.slice(0, 30).trimEnd() + "…"
    : conversationTitle;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-900/80 gap-3">
        <button
          onClick={resetCreation}
          className="flex items-center gap-1.5 text-zinc-500 hover:text-zinc-200 text-sm transition-colors flex-shrink-0"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M9 2L4.5 7 9 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span>New</span>
        </button>

        <h2 className="text-[13px] font-semibold text-zinc-300 text-center flex-1 truncate">
          {headerTitle}
        </h2>

        <div className="flex items-center gap-1.5 flex-shrink-0">
          <VoiceToggle />
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-5">
        {messages.map((msg, i) => (
          <ChatMessage
            key={msg.id}
            message={msg}
            onSaveMemory={openMemoryModal}
            onAudioPlay={handleAudioPlay}
            onFollowUp={handleFollowUp}
            autoPlay={msg.role === "assistant" && i === lastAssistantIndex && i === messages.length - 1}
            isLastAssistant={msg.role === "assistant" && i === lastAssistantIndex}
            experienceTitle={i === 1 ? conversationTitle : undefined}
          />
        ))}

        {/* Thinking indicator */}
        {isSending && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-1.5 px-1"
          >
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-1.5 h-1.5 rounded-full bg-zinc-600"
                animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.1, 0.8] }}
                transition={{ duration: 1.1, repeat: Infinity, delay: i * 0.18 }}
              />
            ))}
          </motion.div>
        )}

        {sendError && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-red-400 text-xs px-1"
          >
            {sendError}
          </motion.p>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-zinc-900/80 flex items-end gap-2">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
          }}
          placeholder="Share what's on your mind..."
          rows={1}
          className="flex-1 bg-zinc-900 border border-zinc-800 focus:border-zinc-700 rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-600 resize-none transition-colors focus:outline-none"
          style={{ maxHeight: 96 }}
        />

        <button
          onClick={recording ? stopRecording : startRecording}
          disabled={isSending}
          className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 border transition-all ${
            recording
              ? "border-red-500 text-red-400 animate-pulse"
              : "border-zinc-700 text-zinc-400 hover:border-zinc-600 hover:text-zinc-300"
          }`}
        >
          <MicIcon active={recording} />
        </button>

        <button
          onClick={handleSend}
          disabled={!input.trim() || isSending}
          className="w-10 h-10 rounded-full bg-amber-500 hover:bg-amber-400 disabled:opacity-25 flex items-center justify-center text-black flex-shrink-0 transition-all active:scale-95"
        >
          <SendIcon />
        </button>
      </div>

      {/* Save to memory modal */}
      <AnimatePresence>
        {memoryModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/80 flex items-end z-50"
            onClick={() => setMemoryModal(null)}
          >
            <motion.div
              initial={{ y: 40 }}
              animate={{ y: 0 }}
              exit={{ y: 40 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full bg-zinc-900 rounded-t-2xl px-6 pt-5 pb-8 border-t border-zinc-800"
            >
              <h3 className="text-[15px] font-semibold text-white mb-4">Save to memory</h3>
              <input
                value={memoryModal.title}
                onChange={(e) => setMemoryModal({ ...memoryModal, title: e.target.value })}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-white text-sm mb-4 focus:outline-none focus:border-amber-500/60"
                placeholder="Memory title"
              />
              <button
                onClick={confirmSaveMemory}
                className="w-full bg-amber-500 text-black font-semibold py-3.5 rounded-xl text-sm"
              >
                Save
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
