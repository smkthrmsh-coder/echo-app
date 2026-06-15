"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { useShallow } from "zustand/react/shallow";
import type {
  CommunicationStylePreference,
  ConversationSummary,
  EchoMemory,
  EchoMessage,
  InsightsData,
  IntentionId,
  JourneySession,
  JourneyTemplate,
  StreakData,
  UserJourney,
  VoicePreference,
} from "@/types";
import { INTENTIONS } from "@/types";
import {
  abandonJourney as apiAbandonJourney,
  createConversation,
  createMemory,
  deleteConversation as apiDeleteConversation,
  fetchActiveJourney,
  fetchInsights,
  fetchJourneys,
  fetchStreak,
  generateJourneySession,
  getConversation,
  journeyCheckin as apiJourneyCheckin,
  listConversations,
  listMemories,
  resolveAudioUrl,
  sendMessage as apiSendMessage,
  startJourney as apiStartJourney,
  transcribeAudio,
  updateConversation,
} from "@/lib/api";

export { useShallow };

const HARDCODED_EMAIL = "admin_sam@icloud.com";
const HARDCODED_PASSWORD = "1234";

export type Screen = "splash" | "login" | "home";
export type Tab = "home" | "journeys" | "insights" | "profile";
export type HomeMode = "welcome" | "creation" | "chat";

interface EchoStore {
  screen: Screen;
  tab: Tab;

  isLoggedIn: boolean;
  login: (email: string, password: string) => boolean;
  logout: () => void;

  homeMode: HomeMode;
  selectedIntention: IntentionId | null;
  customIntention: string;
  isCreating: boolean;
  createError: string | null;

  setSelectedIntention: (id: IntentionId) => void;
  setCustomIntention: (text: string) => void;
  startGeneration: () => Promise<void>;
  resetCreation: () => void;
  dismissWelcome: () => void;

  voicePreference: VoicePreference;
  setVoicePreference: (p: VoicePreference) => void;
  communicationStylePreference: CommunicationStylePreference;
  setCommunicationStylePreference: (s: CommunicationStylePreference) => void;

  conversationId: string | null;
  conversationTitle: string;
  messages: EchoMessage[];
  isSending: boolean;
  sendError: string | null;
  recordingForChat: boolean;
  sendMessage: (content: string) => Promise<void>;
  sendVoiceMessage: (blob: Blob) => Promise<void>;
  setRecordingForChat: (v: boolean) => void;

  conversations: ConversationSummary[];
  loadConversations: () => Promise<void>;
  openConversation: (id: string) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  renameConversation: (id: string, title: string) => Promise<void>;
  pinConversation: (id: string, pinned: boolean) => Promise<void>;

  memories: EchoMemory[];
  loadMemories: () => Promise<void>;
  saveMemory: (title: string, content: string, source_message_id?: string) => Promise<void>;

  journeyTemplates: JourneyTemplate[];
  activeJourney: UserJourney | null;
  journeysLoading: boolean;
  loadJourneys: () => Promise<void>;
  loadActiveJourney: () => Promise<void>;
  startJourney: (slug: string) => Promise<void>;
  journeyCheckin: (slug: string) => Promise<void>;
  abandonJourney: (slug: string) => Promise<void>;

  journeySession: JourneySession | null;
  journeySessionLoading: boolean;
  journeySessionError: string | null;
  openJourneySession: (slug: string) => Promise<void>;
  closeJourneySession: () => void;

  streak: StreakData | null;
  loadStreak: () => Promise<void>;

  insights: InsightsData | null;
  insightsLoading: boolean;
  loadInsights: () => Promise<void>;

  setTab: (tab: Tab) => void;
  goHome: () => void;
}

export const useEchoStore = create<EchoStore>()(
  persist(
    (set, get) => ({
  screen: "splash",
  tab: "home",

  isLoggedIn: false,
  login: (email, password) => {
    if (email.trim() === HARDCODED_EMAIL && password === HARDCODED_PASSWORD) {
      set({ isLoggedIn: true, screen: "home", homeMode: "welcome" });
      return true;
    }
    return false;
  },
  logout: () =>
    set({
      isLoggedIn: false,
      screen: "login",
      homeMode: "welcome",
      selectedIntention: null,
      customIntention: "",
    }),

  homeMode: "welcome",
  selectedIntention: null,
  customIntention: "",
  isCreating: false,
  createError: null,

  setSelectedIntention: (id) => set({ selectedIntention: id, customIntention: "" }),
  setCustomIntention: (text) => set({ customIntention: text }),
  dismissWelcome: () => set({ homeMode: "creation" }),

  startGeneration: async () => {
    const { selectedIntention, customIntention, voicePreference, communicationStylePreference } = get();
    set({ isCreating: true, createError: null });

    const intention = INTENTIONS.find((i) => i.id === selectedIntention);
    const prompt = customIntention.trim()
      ? `${intention?.title ?? "Support"}: ${customIntention.trim()}`
      : intention
        ? `${intention.title}. ${intention.subtitle}`
        : "I need some support right now.";

    const speaking_styles = communicationStylePreference !== "auto" ? [communicationStylePreference] : [];

    try {
      const conv = await createConversation({
        initial_prompt: prompt,
        speaking_styles,
        gender: voicePreference !== "auto" ? voicePreference : undefined,
        emotion: selectedIntention ?? undefined,
      });
      set({
        conversationId: conv.id,
        conversationTitle: conv.title,
        messages: conv.messages,
        homeMode: "chat",
        isCreating: false,
      });
    } catch (e) {
      set({
        isCreating: false,
        createError: e instanceof Error ? e.message : "Something went wrong",
      });
    }
  },

  resetCreation: () =>
    set({
      homeMode: "creation",
      selectedIntention: null,
      customIntention: "",
      isCreating: false,
      createError: null,
      conversationId: null,
      conversationTitle: "",
      messages: [],
    }),

  voicePreference: "auto",
  setVoicePreference: (p) => {
    set({ voicePreference: p });
    const { conversationId } = get();
    if (conversationId) {
      updateConversation(conversationId, {
        reset_voice: true,
        gender: p !== "auto" ? p : undefined,
      }).catch(() => {});
    }
  },
  communicationStylePreference: "auto",
  setCommunicationStylePreference: (s) => set({ communicationStylePreference: s }),

  conversationId: null,
  conversationTitle: "",
  messages: [],
  isSending: false,
  sendError: null,
  recordingForChat: false,

  sendMessage: async (content) => {
    const { conversationId } = get();
    if (!conversationId) return;
    set({ isSending: true, sendError: null });
    const userMsg: EchoMessage = {
      id: `tmp-${Date.now()}`,
      conversation_id: conversationId,
      role: "user",
      content,
      voice_name: "",
      tone: "",
      created_at: new Date().toISOString(),
    };
    set((s) => ({ messages: [...s.messages, userMsg] }));
    try {
      const reply = await apiSendMessage(conversationId, content, true);
      set((s) => ({ messages: [...s.messages, reply], isSending: false }));
    } catch (e) {
      const raw = e instanceof Error ? e.message : "Failed to send";
      const friendly =
        raw.includes("paid_plan") || raw.includes("402")
          ? "Voice unavailable on this plan. Try a different style."
          : raw.length > 120
          ? "Something went wrong. Please try again."
          : raw;
      set({ isSending: false, sendError: friendly });
    }
  },

  sendVoiceMessage: async (blob) => {
    set({ recordingForChat: false, isSending: true, sendError: null });
    try {
      const { text } = await transcribeAudio(blob);
      if (!text.trim()) {
        set({ isSending: false, sendError: "No speech detected" });
        return;
      }
      await get().sendMessage(text);
    } catch (e) {
      set({
        isSending: false,
        sendError: e instanceof Error ? e.message : "Transcription failed",
      });
    }
  },

  setRecordingForChat: (v) => set({ recordingForChat: v }),

  conversations: [],
  loadConversations: async () => {
    try {
      const convs = await listConversations();
      set({ conversations: convs });
    } catch { /* silent */ }
  },
  openConversation: async (id) => {
    try {
      const conv = await getConversation(id);
      set({
        conversationId: conv.id,
        conversationTitle: conv.title,
        messages: conv.messages,
        homeMode: "chat",
        tab: "home",
        screen: "home",
      });
    } catch { /* silent */ }
  },
  deleteConversation: async (id) => {
    await apiDeleteConversation(id);
    set((s) => ({ conversations: s.conversations.filter((c) => c.id !== id) }));
    if (get().conversationId === id) get().resetCreation();
  },
  renameConversation: async (id, title) => {
    await updateConversation(id, { title });
    set((s) => ({
      conversations: s.conversations.map((c) => (c.id === id ? { ...c, title } : c)),
    }));
    if (get().conversationId === id) set({ conversationTitle: title });
  },
  pinConversation: async (id, pinned) => {
    await updateConversation(id, { is_pinned: pinned });
    set((s) => ({
      conversations: s.conversations.map((c) => (c.id === id ? { ...c, is_pinned: pinned } : c)),
    }));
  },

  memories: [],
  loadMemories: async () => {
    try {
      const mems = await listMemories();
      set({ memories: mems });
    } catch { /* silent */ }
  },
  saveMemory: async (title, content, source_message_id) => {
    const { conversationId } = get();
    const mem = await createMemory({
      title,
      content,
      source_message_id,
      source_conversation_id: conversationId ?? undefined,
    });
    set((s) => ({ memories: [mem, ...s.memories] }));
  },

  journeyTemplates: [],
  activeJourney: null,
  journeysLoading: false,
  loadJourneys: async () => {
    set({ journeysLoading: true });
    try {
      const templates = await fetchJourneys();
      set({ journeyTemplates: templates ?? [], journeysLoading: false });
    } catch {
      set({ journeysLoading: false });
    }
  },
  loadActiveJourney: async () => {
    const journey = await fetchActiveJourney();
    set({ activeJourney: journey });
  },
  startJourney: async (slug) => {
    const journey = await apiStartJourney(slug);
    set({ activeJourney: journey });
  },
  journeyCheckin: async (slug) => {
    const journey = await apiJourneyCheckin(slug);
    set({ activeJourney: journey.is_active ? journey : null });
  },
  abandonJourney: async (slug) => {
    await apiAbandonJourney(slug);
    set({ activeJourney: null });
  },

  journeySession: null,
  journeySessionLoading: false,
  journeySessionError: null,
  openJourneySession: async (slug) => {
    set({ journeySessionLoading: true, journeySession: null, journeySessionError: null });
    try {
      const res = await generateJourneySession(slug);
      set({
        journeySession: {
          slug,
          day: res.day,
          todayPrompt: res.today_prompt,
          audioUrl: resolveAudioUrl(res.audio_url),
          durationSeconds: res.duration_seconds,
        },
        journeySessionLoading: false,
      });
    } catch (e) {
      set({
        journeySessionLoading: false,
        journeySessionError: e instanceof Error ? e.message : "Failed to generate session",
      });
    }
  },
  closeJourneySession: () =>
    set({ journeySession: null, journeySessionLoading: false, journeySessionError: null }),

  streak: null,
  loadStreak: async () => {
    try {
      const streak = await fetchStreak();
      set({ streak });
    } catch { /* silent */ }
  },

  insights: null,
  insightsLoading: false,
  loadInsights: async () => {
    set({ insightsLoading: true });
    try {
      const insights = await fetchInsights();
      set({ insights, insightsLoading: false });
    } catch {
      set({ insightsLoading: false });
    }
  },

  setTab: (tab) => {
    set({ tab, screen: "home" });
    if (tab === "profile") get().loadMemories();
    if (tab === "journeys") {
      get().loadJourneys();
      get().loadActiveJourney();
      get().loadStreak();
    }
    if (tab === "insights") get().loadInsights();
  },
  goHome: () => set({ screen: "home", tab: "home" }),
    }),
    {
      name: "echo-preferences",
      partialize: (state) => ({
        voicePreference: state.voicePreference,
        communicationStylePreference: state.communicationStylePreference,
      }),
    }
  )
);

// Splash → login after 2s. Runs once at module load — immune to React Strict
// Mode because Zustand modules are never double-evaluated by React.
if (typeof window !== "undefined") {
  setTimeout(() => {
    if (useEchoStore.getState().screen === "splash") {
      useEchoStore.setState({ screen: "login" });
    }
  }, 2000);
}
