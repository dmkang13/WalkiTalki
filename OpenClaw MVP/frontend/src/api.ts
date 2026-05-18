import type {
  AgentSummary,
  ChatResponse,
  ImageLessonResponse,
  SessionRead,
  SkillValidationResponse,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001';

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getAgent(): Promise<AgentSummary> {
  return requestJson<AgentSummary>('/api/openclaw/agent');
}

export function startSession(customInstructions: string): Promise<SessionRead> {
  return requestJson<SessionRead>('/api/openclaw/session', {
    method: 'POST',
    body: JSON.stringify({
      custom_instructions: customInstructions.trim() || null,
    }),
  });
}

export function confirmLogin(): Promise<SessionRead> {
  return requestJson<SessionRead>('/api/openclaw/session/confirm-login', {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export function sendChat(message: string): Promise<ChatResponse> {
  return requestJson<ChatResponse>('/api/openclaw/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export async function sendImageLesson(file: File): Promise<ImageLessonResponse> {
  const body = new FormData();
  body.append('image', file);
  const response = await fetch(`${API_BASE}/api/openclaw/image-lesson`, {
    method: 'POST',
    credentials: 'include',
    body,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Image upload failed with ${response.status}`);
  }
  return response.json() as Promise<ImageLessonResponse>;
}

export function validateSkill(): Promise<SkillValidationResponse> {
  return requestJson<SkillValidationResponse>('/api/openclaw/skill-validation', {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export function resetSession(): Promise<{ ok: boolean }> {
  return requestJson<{ ok: boolean }>('/api/openclaw/session/reset', {
    method: 'POST',
    body: JSON.stringify({}),
  });
}
