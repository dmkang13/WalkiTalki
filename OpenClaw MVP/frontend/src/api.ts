import type {
  AgentSummary,
  AgentFormValues,
  AgentListResponse,
  ChatResponse,
  ChatStreamEvent,
  ProductAgent,
  PublishResponse,
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
    throw new Error(await readError(response, `Request failed with ${response.status}`));
  }
  return response.json() as Promise<T>;
}

async function readError(response: Response, fallback: string): Promise<string> {
  const text = await response.text();
  if (!text) return fallback;
  try {
    const parsed = JSON.parse(text) as { detail?: unknown };
    if (typeof parsed.detail === 'string') return parsed.detail;
    if (
      parsed.detail &&
      typeof parsed.detail === 'object' &&
      'message' in parsed.detail &&
      typeof parsed.detail.message === 'string'
    ) {
      return parsed.detail.message;
    }
  } catch {
    return text;
  }
  return text;
}

export function getAgent(): Promise<AgentSummary> {
  return requestJson<AgentSummary>('/api/openclaw/agent');
}

export function createAgent(values: AgentFormValues): Promise<ProductAgent> {
  return requestJson<ProductAgent>('/api/openclaw/agents', {
    method: 'POST',
    body: JSON.stringify({
      name: values.name.trim(),
      target_language: values.target_language.trim(),
      native_language: values.native_language.trim() || null,
      custom_instructions: values.custom_instructions.trim() || null,
    }),
  });
}

export function publishAgent(agentId: string): Promise<PublishResponse> {
  return requestJson<PublishResponse>(`/api/openclaw/agents/${encodeURIComponent(agentId)}/publish`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export function listAgents(): Promise<AgentListResponse> {
  return requestJson<AgentListResponse>('/api/openclaw/agents');
}

export function getSharedAgent(shareSlug: string): Promise<ProductAgent> {
  return requestJson<ProductAgent>(`/api/openclaw/agents/${encodeURIComponent(shareSlug)}`);
}

export function startSession(customInstructions: string): Promise<SessionRead> {
  return requestJson<SessionRead>('/api/openclaw/session', {
    method: 'POST',
    body: JSON.stringify({
      custom_instructions: customInstructions.trim() || null,
    }),
  });
}

export function startAgentSession(shareSlug: string, customInstructions: string): Promise<SessionRead> {
  return requestJson<SessionRead>(`/api/openclaw/agents/${encodeURIComponent(shareSlug)}/session`, {
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

export async function sendChatStream(
  message: string,
  onDelta: (text: string) => void,
  shareSlug?: string,
): Promise<Record<string, number> | null> {
  const path = shareSlug
    ? `/api/openclaw/agents/${encodeURIComponent(shareSlug)}/chat/stream`
    : '/api/openclaw/chat/stream';
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    throw new Error(await readError(response, `Chat stream failed with ${response.status}`));
  }
  if (!response.body) {
    throw new Error('Chat stream did not return a readable body.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let usage: Record<string, number> | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      const event = parseStreamEvent(line);
      if (!event) continue;
      if (event.type === 'delta') {
        onDelta(event.text);
      } else if (event.type === 'done') {
        usage = event.usage ?? null;
      } else if (event.type === 'error') {
        throw new Error(event.message);
      }
    }
  }

  buffer += decoder.decode();
  const finalEvent = parseStreamEvent(buffer);
  if (finalEvent?.type === 'error') {
    throw new Error(finalEvent.message);
  }
  if (finalEvent?.type === 'done') {
    usage = finalEvent.usage ?? null;
  }

  return usage;
}

function parseStreamEvent(line: string): ChatStreamEvent | null {
  const trimmed = line.trim();
  if (!trimmed) return null;
  return JSON.parse(trimmed) as ChatStreamEvent;
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
