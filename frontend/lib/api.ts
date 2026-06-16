import type {
  ConversationDetail,
  ConversationSummary,
  EchoMemory,
  EchoMessage,
  GenerateResponse,
  InsightsData,
  JourneyTemplate,
  StreakData,
  TranscribeResponse,
  UserJourney,
} from "@/types";
import { getAuthToken } from "./auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export async function apiSignup(email: string, password: string, display_name?: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password, display_name }),
  });
}

export async function apiLogin(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function getGoogleAuthUrl(): string {
  return `${API_BASE}/api/auth/google`;
}

// Legacy voice generation
export async function generateExperience(prompt: string): Promise<GenerateResponse> {
  return apiFetch<GenerateResponse>("/api/generate", {
    method: "POST",
    body: JSON.stringify({ prompt }),
  });
}

export async function transcribeAudio(blob: Blob): Promise<TranscribeResponse> {
  const form = new FormData();
  form.append("audio", blob, "recording.webm");
  const token = getAuthToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}/api/transcribe`, { method: "POST", body: form, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<TranscribeResponse>;
}

export function resolveAudioUrl(url: string): string {
  if (url.startsWith("http")) return url;
  return `${API_BASE}${url}`;
}

// ─── Conversations ────────────────────────────────────────────────────────────

export async function createConversation(data: {
  initial_prompt: string;
  speaking_styles?: string[];
  gender?: string;
  energy_level?: number;
  persona_id?: string | null;
  emotion?: string | null;
  title?: string;
  username?: string;
}): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>("/api/conversations", {
    method: "POST",
    body: JSON.stringify({
      speaking_styles: [],
      gender: "female",
      energy_level: 3,
      ...data,
    }),
  });
}

export async function listConversations(): Promise<ConversationSummary[]> {
  return apiFetch<ConversationSummary[]>("/api/conversations");
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>(`/api/conversations/${id}`);
}

export async function updateConversation(
  id: string,
  data: { title?: string; is_pinned?: boolean; reset_voice?: boolean; gender?: string },
): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>(`/api/conversations/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteConversation(id: string): Promise<void> {
  await apiFetch(`/api/conversations/${id}`, { method: "DELETE" });
}

export async function sendMessage(
  conversationId: string,
  content: string,
  emotionalMode: boolean = false,
): Promise<EchoMessage> {
  return apiFetch<EchoMessage>(`/api/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content, emotional_mode: emotionalMode }),
  });
}

// ─── Memories ────────────────────────────────────────────────────────────────

export async function createMemory(data: {
  title: string;
  content: string;
  category?: string;
  source_message_id?: string;
  source_conversation_id?: string;
}): Promise<EchoMemory> {
  return apiFetch<EchoMemory>("/api/memories", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listMemories(): Promise<EchoMemory[]> {
  return apiFetch<EchoMemory[]>("/api/memories");
}

export async function deleteMemory(id: string): Promise<void> {
  await apiFetch(`/api/memories/${id}`, { method: "DELETE" });
}

// ─── Journeys ────────────────────────────────────────────────────────────────

export async function fetchJourneys(): Promise<JourneyTemplate[]> {
  return apiFetch<JourneyTemplate[]>("/api/journeys");
}

export async function fetchActiveJourney(): Promise<UserJourney | null> {
  try {
    return await apiFetch<UserJourney>("/api/journeys/active");
  } catch {
    return null;
  }
}

export async function startJourney(slug: string): Promise<UserJourney> {
  return apiFetch<UserJourney>(`/api/journeys/${slug}/start`, { method: "POST" });
}

export async function journeyCheckin(slug: string): Promise<UserJourney> {
  return apiFetch<UserJourney>(`/api/journeys/${slug}/checkin`, { method: "POST" });
}

export async function abandonJourney(slug: string): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(`/api/journeys/${slug}/abandon`, { method: "POST" });
}

export async function generateJourneySession(slug: string): Promise<{
  audio_url: string;
  duration_seconds: number;
  day: number;
  today_prompt: string;
}> {
  return apiFetch(`/api/journeys/${slug}/session`, { method: "POST" });
}

export async function fetchJourneyRecommendations(): Promise<{ slug: string; reason: string }[]> {
  try {
    return await apiFetch<{ slug: string; reason: string }[]>("/api/journeys/recommendations");
  } catch {
    return [];
  }
}

// ─── Insights ─────────────────────────────────────────────────────────────────

export async function fetchInsights(): Promise<InsightsData> {
  return apiFetch<InsightsData>("/api/insights");
}

// ─── Streaks ─────────────────────────────────────────────────────────────────

export async function fetchStreak(): Promise<StreakData> {
  return apiFetch<StreakData>("/api/streaks");
}

export async function streakCheckin(): Promise<StreakData> {
  return apiFetch<StreakData>("/api/streaks/checkin", { method: "POST" });
}
