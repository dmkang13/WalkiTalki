import type {
  AgentDraft,
  AgentFormValues,
  ApiKeyStatus,
  LessonSession,
  MessageResponse,
  PublishedAgentList,
  PublishedAgent,
  PublishResponse
} from "../types";

type RequestOptions = RequestInit & {
  friendlyError?: string;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response: Response;

  try {
    response = await fetch(path, {
      credentials: "include",
      headers: options.body instanceof FormData ? options.headers : { "Content-Type": "application/json", ...options.headers },
      ...options
    });
  } catch {
    throw new Error("Network request failed. Check your connection and try again.");
  }

  if (!response.ok) {
    throw new Error(options.friendlyError ?? friendlyMessageForStatus(response.status));
  }

  return (await response.json()) as T;
}

function friendlyMessageForStatus(status: number) {
  if (status === 401) return "Your API key session expired. Connect your key again to continue.";
  if (status === 404) return "We could not find that published agent.";
  if (status >= 500) return "The server could not complete the request. Try again in a moment.";
  return "The request could not be completed. Please check the form and try again.";
}

function cleanAgentPayload(values: AgentFormValues) {
  return {
    name: values.name.trim(),
    targetLanguage: values.targetLanguage.trim(),
    nativeLanguage: values.nativeLanguage.trim() || undefined,
    customInstructions: values.customInstructions.trim() || undefined
  };
}

export const api = {
  getApiKeyStatus: () => request<ApiKeyStatus>("/api/runtime/openai-key/status"),
  validateApiKey: (apiKey: string) =>
    request<ApiKeyStatus>("/api/runtime/openai-key/validate", {
      method: "POST",
      body: JSON.stringify({ apiKey }),
      friendlyError: "That key could not be validated. Check it and try again."
    }),
  clearApiKey: () =>
    request<ApiKeyStatus>("/api/runtime/openai-key", {
      method: "DELETE"
    }),
  createAgent: (values: AgentFormValues) =>
    request<AgentDraft>("/api/agents", {
      method: "POST",
      body: JSON.stringify(cleanAgentPayload(values))
    }),
  publishAgent: (agentId: string) =>
    request<PublishResponse>(`/api/agents/${encodeURIComponent(agentId)}/publish`, {
      method: "POST"
    }),
  getSharedAgent: (shareSlug: string) =>
    request<PublishedAgent>(`/api/shared-agents/${encodeURIComponent(shareSlug)}`, {
      friendlyError: "This shared agent is unavailable or is not published."
    }),
  listSharedAgents: () =>
    request<PublishedAgentList>("/api/shared-agents", {
      friendlyError: "Published agents could not be loaded."
    }),
  createLessonSession: (shareSlug: string, image: File | Blob) => {
    const data = new FormData();
    data.append("image", image, image instanceof File ? image.name : "camera-capture.jpg");
    return request<LessonSession>(`/api/shared-agents/${encodeURIComponent(shareSlug)}/lesson-sessions`, {
      method: "POST",
      body: data,
      friendlyError: "The lesson could not be generated. Make sure your API key is connected and try again."
    });
  },
  sendMessage: (lessonSessionId: string, content: string) =>
    request<MessageResponse>(`/api/lesson-sessions/${encodeURIComponent(lessonSessionId)}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
      friendlyError: "The assistant could not answer that message. Try again."
    })
};
