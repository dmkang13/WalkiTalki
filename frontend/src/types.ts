export type ApiKeyStatus = {
  hasApiKey: boolean;
};

export type AgentDraft = {
  id: string;
  name: string;
  targetLanguage: string;
  nativeLanguage?: string;
  customInstructions?: string;
  status: "draft" | "published";
};

export type PublishedAgent = AgentDraft & {
  shareSlug: string;
};

export type PublishResponse = {
  id: string;
  status: "published";
  shareSlug: string;
  shareUrl: string;
};

export type Usage = {
  model: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
};

export type LessonSession = {
  id: string;
  agentId: string;
  lessonMarkdown: string;
  usage?: Usage;
  messages: ChatMessage[];
};

export type MessageResponse = {
  message: ChatMessage;
  usage?: Usage;
};

export type AgentFormValues = {
  name: string;
  targetLanguage: string;
  nativeLanguage: string;
  customInstructions: string;
};
