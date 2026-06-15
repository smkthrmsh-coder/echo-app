// ─── Echo V1 Types ───────────────────────────────────────────────────────────

export interface EchoMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  audio_url?: string | null;
  duration_seconds?: number | null;
  voice_name: string;
  tone: string;
  created_at: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  preview: string;
  message_count: number;
  is_pinned: boolean;
  emotion?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail {
  id: string;
  title: string;
  speaking_styles: string[];
  gender: string;
  energy_level: number;
  persona_id?: string | null;
  emotion?: string | null;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
  messages: EchoMessage[];
}

export interface EchoMemory {
  id: string;
  title: string;
  content: string;
  category: string;
  source_message_id?: string | null;
  source_conversation_id?: string | null;
  created_at: string;
}

// ─── Journey types ────────────────────────────────────────────────────────────

export interface JourneyTemplate {
  slug: string;
  title: string;
  emoji: string;
  tagline: string;
  description: string;
  outcome: string;
  tags: string[];
  duration_days: number;
  category: string;
  color: string;
}

export interface UserJourney {
  id: string;
  journey_slug: string;
  journey: JourneyTemplate;
  current_day: number;
  completed_days: number[];
  is_active: boolean;
  started_at: string;
  last_session_at: string | null;
  today_prompt: string | null;
  remaining_days: number;
  progress_pct: number;
  estimated_completion: string | null;
}

export interface StreakData {
  current_streak: number;
  total_days: number;
}

export interface JourneySession {
  slug: string;
  day: number;
  todayPrompt: string;
  audioUrl: string;
  durationSeconds: number;
}

// ─── Insights types ───────────────────────────────────────────────────────────

export interface InsightsData {
  locked: boolean;
  conversations_until_unlock: number;
  total_conversations: number;
  total_messages: number;
  total_memories: number;
  current_streak: number;
  top_tones: { tone: string; count: number; emoji: string }[];
  top_voices: { name: string; count: number }[];
  emotion_breakdown: { emotion: string; count: number; pct: number }[];
  most_active_style: string;
  average_session_length: number;
  total_audio_minutes: number;
  favourite_companion: string;
  weekly_activity: boolean[];
}

// ─── Creation flow — V1 ───────────────────────────────────────────────────────

export const INTENTIONS = [
  { id: "peace",         title: "Peace",               subtitle: "Quiet your mind." },
  { id: "confidence",    title: "Confidence",          subtitle: "Feel ready for what's ahead." },
  { id: "motivation",    title: "Motivation",          subtitle: "Find your drive." },
  { id: "comfort",       title: "Comfort",             subtitle: "You're not alone." },
  { id: "focus",         title: "Focus",               subtitle: "Remove distractions." },
  { id: "sleep",         title: "Better Sleep",        subtitle: "Slow your thoughts." },
  { id: "energy",        title: "Energy",              subtitle: "Recharge your day." },
  { id: "clarity",       title: "Clarity",             subtitle: "Untangle your thoughts." },
  { id: "encouragement", title: "Encouragement",       subtitle: "Keep moving forward." },
  { id: "listen",        title: "Someone To Listen",   subtitle: "I'm here with you." },
  { id: "other",         title: "Something Else",      subtitle: "Tell me in your own words." },
] as const;

export type IntentionId = (typeof INTENTIONS)[number]["id"];

export const SPEAKING_STYLES = [
  { id: "calm",     label: "Calm & Supportive" },
  { id: "friendly", label: "Friendly" },
  { id: "direct",   label: "Straightforward" },
  { id: "mentor",   label: "Wise Mentor" },
  { id: "coach",    label: "Motivational Coach" },
  { id: "gentle",   label: "Gentle Listener" },
  { id: "funny",    label: "Funny" },
] as const;

export type CommunicationStylePreference = "auto" | "calm" | "friendly" | "direct" | "mentor" | "coach" | "gentle" | "funny";

export type VoicePreference = "auto" | "female" | "male";

// ─── Legacy display maps (ChatMessage) ───────────────────────────────────────

export const TONE_COLORS: Record<string, string> = {
  energetic: "#F59E0B", calm: "#6EE7B7", fierce: "#EF4444",
  comforting: "#A78BFA", melancholic: "#94A3B8", playful: "#FBBF24",
  mysterious: "#818CF8", romantic: "#F472B6", anxious: "#FB923C", hopeful: "#34D399",
};

// ─── Legacy (kept for API compat) ────────────────────────────────────────────

export interface TranscribeResponse {
  text: string;
  confidence: number | null;
  language: string | null;
}

export interface GenerateResponse {
  generation_id: string;
  audio_url: string;
  duration_seconds: number | null;
  prompt: string;
}
