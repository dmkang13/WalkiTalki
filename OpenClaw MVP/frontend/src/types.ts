export type AgentSummary = {
  agent_id: string;
  name: string;
  description: string;
  target_language: string;
  native_language?: string | null;
  required_capabilities: string[];
  validation_skill_name: string;
  validation_skill_source: string;
};

export type SessionRead = {
  local_session_id: string;
  openclaw_session_id: string;
  agent_id: string;
  runtime_status: string;
  provider_status: string;
  login_url?: string | null;
  model?: string | null;
  provider?: string | null;
  custom_instructions_provided: boolean;
  skill_status: string;
};

export type ChatMessage = {
  role: 'user' | 'assistant' | 'system';
  content: string;
};

export type AgentFormValues = {
  name: string;
  target_language: string;
  native_language: string;
  custom_instructions: string;
};

export type ProductAgent = {
  id: string;
  name: string;
  description: string;
  target_language: string;
  native_language?: string | null;
  custom_instructions?: string | null;
  status: 'draft' | 'published';
  share_slug?: string | null;
};

export type AgentListResponse = {
  agents: ProductAgent[];
};

export type PublishResponse = {
  id: string;
  status: 'published';
  share_slug: string;
  share_url: string;
};

export type ChatResponse = {
  message: string;
  runtime_status: string;
  provider_status: string;
  usage?: Record<string, number> | null;
};

export type ChatStreamEvent =
  | {
      type: 'delta';
      text: string;
    }
  | {
      type: 'done';
      usage?: Record<string, number> | null;
    }
  | {
      type: 'error';
      code?: string;
      message: string;
    };

export type SkillValidationResponse = {
  message: string;
  skill_status: string;
  skill_name: string;
  skill_source: string;
  evidence: string;
};
