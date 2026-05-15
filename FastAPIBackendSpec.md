# WalkiTalki FastAPI Backend Spec

## Source of Truth

This spec is derived from `MVP.md` only. Ignore `Architecture.md` for this work.

OpenAI implementation notes in this spec use the official OpenAI API docs:

- [Responses API](https://platform.openai.com/docs/api-reference/responses/create?api-mode=responses)
- [Images and vision](https://platform.openai.com/docs/guides/images-vision?api-mode=responses&format=file)
- [Responses vs Chat Completions](https://platform.openai.com/docs/guides/responses-vs-chat-completions)

## Goal

Build a FastAPI backend with PostgreSQL persistence that supports the MVP loop:

1. Validate a visitor-provided OpenAI API key.
2. Store one constrained Photo Language Agent spec.
3. Publish that agent and generate a direct share link.
4. Serve published agent specs by share slug.
5. Start a lesson session from a camera-captured or uploaded image.
6. Call OpenAI with the current visitor's API key.
7. Store generated lesson text and chat messages.
8. Continue follow-up chat using the active lesson context.

There are no users, accounts, teams, profiles, or auth objects in the MVP.

## Non-Goals

Do not build:

- User table
- Account login
- Password auth
- OAuth
- Marketplace
- Forking
- Flashcards
- Saved vocabulary
- Progress tracking
- Memory
- Vector stores
- Uploaded document knowledge base
- Arbitrary OpenAPI tools
- Scripts
- Audio or microphone processing
- Creator-funded usage
- Admin moderation

## Backend Ownership

The FastAPI backend owns:

- API key validation
- Ephemeral API key session handling
- Agent spec persistence
- Publish state
- Share slug generation
- Published-agent retrieval
- Published-agent listing
- Image upload validation
- OpenAI Responses API calls
- Lesson session persistence
- Chat message persistence
- Basic usage metadata when available

The backend does not own:

- React page rendering
- Frontend routing
- User account identity
- Long-term API key storage
- Marketplace discovery
- Future agent tool infrastructure

## Recommended Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- openai Python SDK
- Uvicorn for local development
- pytest for backend tests

Use the repo's conventions once implementation begins.

## OpenAI Boundary

Use OpenAI's Responses API for new model calls. Official docs describe it as the
recommended newer primitive for agent-like, multimodal applications and document
support for text and image inputs.

Backend responsibilities:

- Receive visitor-provided OpenAI API key through the key validation endpoint.
- Validate the key with a low-cost OpenAI request.
- Store the key only for the current backend session.
- Use that key when generating the lesson and follow-up chat.
- Never persist the raw API key in PostgreSQL.
- Never include the creator's key in a shared agent.

Model selection should be configurable by environment variable, with a sensible
vision-capable default chosen during implementation.

## API Key Session Design

Because the MVP has no user accounts, use a prototype session instead of user
identity.

Recommended behavior:

- Backend creates or reads an opaque `wt_session` cookie.
- Cookie is HTTP-only, secure in production, and same-site lax.
- Backend stores the raw OpenAI API key in a process-local encrypted or private
  in-memory session store keyed by `wt_session`.
- Backend derives a non-secret session hash from `wt_session` for ownership
  checks on draft agents and lesson sessions.
- PostgreSQL may store the non-secret session hash, but not the key.
- If the backend restarts, the visitor must reconnect their API key.
- If multiple backend workers are used, session storage needs a shared secret
  store later. Do not solve that in the MVP unless deployment requires it.

This is intentionally not long-term credential infrastructure.

## PostgreSQL Data Model

Use UUID primary keys unless the implementation has a strong reason not to.

### `agent_specs`

Stores the constrained Photo Language Agent spec.

Fields:

- `id`
- `owner_session_hash`
- `name`
- `target_language`
- `native_language`
- `custom_instructions`
- `status`: `draft` or `published`
- `share_slug`: nullable until publish, unique when present
- `created_at`
- `updated_at`
- `published_at`

Rules:

- No `user_id`.
- Draft agents are editable and publishable only by the matching
  `owner_session_hash`.
- Only one functional agent type exists in MVP.
- Disabled future capability icons are not persisted as tools.
- Published specs can be read by anyone with the share slug.

### `lesson_sessions`

Stores one generated lesson for one image against one published agent.

Fields:

- `id`
- `runtime_session_hash`
- `agent_spec_id`
- `share_slug`
- `image_mime_type`
- `image_size_bytes`
- `image_storage_ref`: nullable if image is not stored
- `lesson_markdown`
- `openai_initial_response_id`
- `created_at`
- `updated_at`

Rules:

- No `user_id`.
- Lesson sessions are readable and writable only by the matching
  `runtime_session_hash`.
- No long-term memory.
- No lesson progress.
- Image storage should be temporary if used at all.
- A lesson session belongs to the visitor's current prototype session
  operationally, but not through a persisted user account.

### `chat_messages`

Stores messages for one lesson session.

Fields:

- `id`
- `lesson_session_id`
- `role`: `user` or `assistant`
- `content`
- `openai_response_id`: nullable
- `created_at`

Rules:

- Store the initial generated lesson as an assistant message.
- Store each follow-up user message and assistant response.
- Access is allowed only when the parent lesson session matches the current
  `runtime_session_hash`.
- Do not store system prompts as user-visible chat messages.

### `usage_events`

Stores basic usage visibility when available.

Fields:

- `id`
- `lesson_session_id`
- `openai_response_id`
- `model`
- `input_tokens`
- `output_tokens`
- `total_tokens`
- `created_at`

Rules:

- Usage events are informational.
- Do not block the MVP if token usage is unavailable for a response.
- Do not attach usage to a persisted user account.

## API Endpoints

Prefix all endpoints with `/api`.

### Runtime API Key

`POST /api/runtime/openai-key/validate`

Purpose:
- Validate the visitor's OpenAI API key and store it for the current backend
  prototype session.

Request:

```json
{
  "apiKey": "sk-..."
}
```

Response:

```json
{
  "hasApiKey": true
}
```

Errors:

- `400` missing key
- `401` invalid key
- `502` OpenAI validation unavailable

`GET /api/runtime/openai-key/status`

Response:

```json
{
  "hasApiKey": true
}
```

`DELETE /api/runtime/openai-key`

Purpose:
- Remove the current session's API key from backend memory.

Response:

```json
{
  "hasApiKey": false
}
```

### Agents

`POST /api/agents`

Purpose:
- Create a draft Photo Language Agent spec.

Request:

```json
{
  "name": "Photo Language Tutor",
  "targetLanguage": "Korean",
  "nativeLanguage": "English",
  "customInstructions": "Use simple examples."
}
```

Response:

```json
{
  "id": "uuid",
  "name": "Photo Language Tutor",
  "targetLanguage": "Korean",
  "nativeLanguage": "English",
  "customInstructions": "Use simple examples.",
  "status": "draft"
}
```

Validation:

- `name` required
- `targetLanguage` required
- `nativeLanguage` optional
- `name` max length 80 characters
- `targetLanguage` max length 80 characters
- `nativeLanguage` max length 80 characters
- `customInstructions` optional, max length 1,000 characters

`PATCH /api/agents/{agent_id}`

Purpose:
- Update an unpublished draft.

Rules:

- Allow editing draft fields.
- Require the current session hash to match `owner_session_hash`.
- If already published, either reject edits or create an explicit simple update
  behavior. Prefer rejecting in the MVP to keep sharing stable.

`POST /api/agents/{agent_id}/publish`

Purpose:
- Mark the agent as published and create a direct share slug.

Response:

```json
{
  "id": "uuid",
  "status": "published",
  "shareSlug": "abc123",
  "shareUrl": "https://example.com/agents/abc123"
}
```

Rules:

- Generate unguessable share slugs.
- Require the current session hash to match `owner_session_hash`.
- Publishing does not create a marketplace listing.
- Publishing does not create a user-owned public profile.
- Publishing does not include any API key or lesson session.

### Shared Agents

`GET /api/shared-agents/{share_slug}`

Purpose:
- Return the published agent spec for any visitor with the direct link.

Response:

```json
{
  "id": "uuid",
  "shareSlug": "abc123",
  "name": "Photo Language Tutor",
  "targetLanguage": "Korean",
  "nativeLanguage": "English",
  "customInstructions": "Use simple examples.",
  "status": "published"
}
```

Errors:

- `404` share slug not found
- `404` agent exists but is not published

`GET /api/shared-agents`

Purpose:
- Return every published agent in the MVP.

Response:

```json
{
  "agents": [
    {
      "id": "uuid",
      "shareSlug": "abc123",
      "name": "Photo Language Tutor",
      "targetLanguage": "Korean",
      "nativeLanguage": "English",
      "customInstructions": "Use simple examples.",
      "status": "published"
    }
  ]
}
```

Rules:

- Return only published agents.
- Order newest published agents first.
- This is not a marketplace endpoint. Do not add ratings, profiles, ranking,
  categories, or search in the MVP.

### Lesson Sessions

`POST /api/shared-agents/{share_slug}/lesson-sessions`

Purpose:
- Start a new lesson session by receiving a camera-captured or uploaded image and
  generating the initial lesson.

Request:
- Multipart form data:
  - `image`: required file

Response:

```json
{
  "id": "uuid",
  "agentId": "uuid",
  "lessonMarkdown": "## Vocabulary\n...",
  "usage": {
    "model": "configured-default",
    "inputTokens": 100,
    "outputTokens": 200,
    "totalTokens": 300
  },
  "messages": [
    {
      "id": "uuid",
      "role": "assistant",
      "content": "## Vocabulary\n...",
      "createdAt": "2026-05-14T00:00:00Z"
    }
  ]
}
```

Rules:

- Requires current prototype session to have an OpenAI API key.
- Validate image MIME type and size before calling OpenAI.
- Supported image types should match OpenAI image input support where practical:
  PNG, JPEG, WEBP, and non-animated GIF.
- Maximum image size is 10 MB.
- Return a friendly error if OpenAI rejects the image.
- Store generated lesson text and initial assistant message.
- Store the current `runtime_session_hash` on the lesson session.

`GET /api/lesson-sessions/{lesson_session_id}`

Purpose:
- Return lesson session and messages for the current browser flow.

Response:

```json
{
  "id": "uuid",
  "agentId": "uuid",
  "lessonMarkdown": "## Vocabulary\n...",
  "usage": {
    "model": "configured-default",
    "inputTokens": 100,
    "outputTokens": 200,
    "totalTokens": 300
  },
  "messages": [
    {
      "id": "uuid",
      "role": "assistant",
      "content": "## Vocabulary\n...",
      "createdAt": "2026-05-14T00:00:00Z"
    }
  ]
}
```

MVP note:
- Without user accounts, this endpoint is mainly for refresh/retry ergonomics.
  It should not become a broad history API.
- Require the current session hash to match `runtime_session_hash`.

`POST /api/lesson-sessions/{lesson_session_id}/messages`

Purpose:
- Continue chat about the generated lesson.

Request:

```json
{
  "content": "Can you give me a simpler example?"
}
```

Validation:

- `content` is required.
- `content` max length is 1,000 characters.

Response:

```json
{
  "message": {
    "id": "uuid",
    "role": "assistant",
    "content": "Sure...",
    "createdAt": "2026-05-14T00:00:00Z"
  },
  "usage": {
    "model": "configured-default",
    "inputTokens": 50,
    "outputTokens": 100,
    "totalTokens": 150
  }
}
```

Rules:

- Requires current prototype session to have an OpenAI API key.
- Require the current session hash to match `runtime_session_hash`.
- Store the user message before calling OpenAI.
- Store the assistant response after OpenAI returns.
- Use the agent spec, original lesson, and recent chat messages as context.
- Do not use persistent memory or vector recall.

## Prompt Requirements

### Initial Lesson Prompt

The backend should construct the model instructions from the published agent
spec.

The model should:

- Identify important visible objects.
- Name those objects in the target language.
- Define the words in plain language.
- Provide text-only pronunciation guidance when useful.
- Give practical phrases using visible objects.
- Ask one or two follow-up practice questions.
- Avoid claiming it saved flashcards, memory, progress, or vocabulary.

Initial output can be markdown. Structured JSON is not required for MVP unless
the frontend later needs richer rendering.

### Follow-Up Prompt

The backend should send:

- Agent instructions
- Product guardrails
- Original generated lesson
- Recent chat messages
- User's new question

The model should answer only within the lesson/chat context unless the user asks
for a general language explanation.

Custom instructions are preferences only. They must not override product
guardrails, including no flashcard saving, no memory, no external APIs, no audio,
no progress tracking, and no claims that the app persisted vocabulary.

## Image Handling

MVP approach:

- Validate MIME type.
- Validate file size.
- Convert upload to a format accepted by the OpenAI request.
- Prefer not to persist images long-term.
- If storing temporarily, write an `image_storage_ref` and use a cleanup task
  later.

Do not build a permanent media library.

## Security and Privacy Rules

- Never store raw OpenAI API keys in PostgreSQL.
- Never log raw OpenAI API keys.
- Never return raw OpenAI API keys to the frontend.
- Never attach API keys to agent specs.
- Never share creator image, lesson, or chat history through the share link.
- Treat share slugs as bearer links.
- Use unguessable share slugs.
- Limit upload size.
- Sanitize and bound text fields.

## Error Response Shape

Use a consistent error shape:

```json
{
  "error": {
    "code": "missing_api_key",
    "message": "Connect your OpenAI API key before generating a lesson."
  }
}
```

Recommended error codes:

- `missing_api_key`
- `invalid_api_key`
- `agent_not_found`
- `agent_not_published`
- `invalid_image_type`
- `image_too_large`
- `openai_request_failed`
- `lesson_session_not_found`
- `validation_error`

## Environment Variables

- `DATABASE_URL`
- `OPENAI_DEFAULT_MODEL`
- `APP_BASE_URL`
- `SESSION_COOKIE_NAME`
- `SESSION_SECRET`
- `MAX_IMAGE_BYTES`, default `10485760`
- `CORS_ALLOWED_ORIGINS`

Do not require a server-owned `OPENAI_API_KEY` for normal MVP lesson generation.
The visitor's key powers the request.

## Testing Requirements

Unit tests:

- Agent create validation
- Agent draft ownership checks
- Publish share slug generation
- Shared-agent retrieval
- Published-agent list
- API key session status behavior
- Image validation
- Lesson session ownership checks
- Prompt construction
- Error response formatting

Integration tests:

- Create agent -> publish -> fetch by share slug
- Create multiple agents -> publish -> list published agents
- Missing API key blocks lesson generation
- Image upload creates lesson session when OpenAI client is mocked
- Follow-up chat stores user and assistant messages when OpenAI client is mocked
- A different session cannot edit another session's draft or continue another
  session's lesson

Do not hit real OpenAI in default test runs.

## Acceptance Criteria

- Backend starts locally and connects to PostgreSQL.
- Alembic migrations create MVP tables.
- A visitor can validate an OpenAI API key into a prototype session.
- Raw API keys are not written to PostgreSQL.
- A draft Photo Language Agent can be created.
- A draft can be published into a direct share slug.
- A published agent can be fetched by share slug without login.
- Every published agent can be listed without login.
- A lesson session can be created from an uploaded image using the current
  visitor's API key.
- Camera-captured images use the same backend upload endpoint as file uploads.
- Generated lesson text is stored.
- Follow-up messages are stored.
- No user account table is required.
- No flashcard, memory, vector, marketplace, or forking tables are required.

## Backend Subagent Handoff

The backend subagent should implement only FastAPI, PostgreSQL, migrations,
OpenAI integration, and tests. It should not implement React screens or client
styling. Frontend and backend should coordinate through the endpoint contract in
this spec.
