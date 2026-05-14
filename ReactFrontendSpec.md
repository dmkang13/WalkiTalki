# WalkiTalki React Frontend Spec

## Source of Truth

This spec is derived from `MVP.md` only. Ignore `Architecture.md` for this work.

## Goal

Build a React frontend that proves the MVP loop:

1. User connects their own OpenAI API key.
2. User builds one constrained Photo Language Agent.
3. User publishes the agent.
4. User copies a direct share link.
5. Recipient opens the link, connects their own OpenAI API key, and starts a
   photo lesson chat.
6. User uploads or captures a photo.
7. App shows a generated language lesson.
8. User can chat about the image and lesson.

The frontend should feel like an agent builder, but the only functional agent
type is the Photo Language Agent.

## Non-Goals

Do not build:

- Account creation
- Login
- User profiles
- Full agent library
- Marketplace
- Forking
- Flashcards
- Saved vocabulary
- Progress tracking
- Functional arbitrary tools
- Audio or microphone flows
- OpenAPI import
- Scripts
- Vector stores
- Memory
- Mobile-native app

## Frontend Ownership

The React app owns:

- Page routing
- Form UX
- API key connection UX
- Agent builder UI
- Disabled future capability icon grid
- Publish and share-link UX
- Shared-agent landing UX
- Required camera capture UX
- Image upload UX
- Lesson and chat UI
- Client-side validation and loading/error states
- Basic usage/cost notice display

The frontend does not own:

- PostgreSQL persistence
- OpenAI API calls
- API key validation against OpenAI
- Share-token generation
- Lesson generation
- Chat response generation

## Recommended Stack

- React
- TypeScript
- Vite
- React Router
- Plain `fetch` wrapped in small custom hooks for server state
- Plain React state for forms
- Plain TypeScript and hand-written validation for client-side validation
- Heroicons for icons
- CSS modules for styling

Use the existing repo conventions once implementation begins.

Do not add Next.js, TanStack Query, React Hook Form, Zod, lucide-react, Tailwind,
or another equivalent library unless the MVP grows beyond the simple flows
described here.

## Information Architecture

### Required Routes

`/`
- Entry route.
- If no API key session is active, show API key connection.
- If API key session is active, route user to the builder or show a prominent
  "Create Photo Language Agent" action.

`/build`
- Photo Language Agent builder.
- Lets the user configure the single supported agent type.

`/agents/:shareSlug`
- Published/shared agent landing screen.
- Used by both creator and recipient.
- Shows the published agent summary and start-chat action.
- If no API key session is active, prompts the current visitor to connect their
  own key.

`/agents/:shareSlug/chat`
- Lesson chat screen for a published/shared agent.
- Lets the visitor capture or upload an image, view the generated lesson, and
  ask follow-up questions.

### Optional Routes

`/agents/:shareSlug/share`
- Optional dedicated share confirmation screen.
- Not required if share-link copy is handled on the published agent screen.

## Core Screens

### 1. API Key Connection Screen

Purpose:
- Make BYOK explicit before any AI compute happens.

UI requirements:
- OpenAI API key input.
- Short notice that the user pays OpenAI directly through their own key.
- Connect button.
- Loading state while validating.
- Error state for invalid key.
- Success state once connected.
- Clear "No key, no lesson generation" message.

Behavior:
- Submit key to backend validation endpoint.
- Never store the raw API key in localStorage.
- After success, treat the browser session as key-connected.
- If the page refreshes, ask backend whether the current session still has a key.

### 2. Photo Language Agent Builder

Purpose:
- Let a user create the only functional MVP agent.

Editable fields:
- Agent name
- Target language
- Optional native language
- Optional custom instructions

Recommended defaults:
- Agent name: `Photo Language Tutor`
- Target language: user-selected, no hidden default unless product decides one
- Native language: optional
- Custom instructions: empty

Validation:
- Agent name is required.
- Target language is required.
- Agent name max length is 80 characters.
- Target language max length is 80 characters.
- Native language max length is 80 characters.
- Custom instructions max length is 1,000 characters.

Layout:
- Main form on the left or top.
- Agent summary preview on the right or below.
- Future capability icon grid visible but disabled.
- Publish button disabled until required fields are valid.

### 3. Disabled Capability Icon Grid

Purpose:
- Give users the feeling that agents are built from interchangeable blocks
  without actually enabling those blocks in the MVP.

Icons to show:
- Image Input: enabled
- Flashcards: disabled
- Memory: disabled
- Documents: disabled
- Vector Recall: disabled
- Audio: disabled
- API Tools: disabled
- Scripts: disabled
- Classroom: disabled
- Progress: disabled

Behavior:
- Enabled Image Input may show as active.
- Disabled icons must not open configuration panels.
- Disabled icons may show a tooltip such as "Not included in this MVP."
- Disabled icons must not alter the saved agent spec.
- Disabled icons must not be included in runtime tool payloads.

### 4. Published Agent Landing Screen

Purpose:
- Show the runnable agent after publish and support sharing.

UI requirements:
- Agent name
- Target language
- Native language if present
- Custom instruction summary if present
- "Start chat" button
- "Copy share link" button
- Usage notice that the current visitor's OpenAI API key will be used

Behavior:
- If current visitor has no API key session, show API key connection prompt
  before enabling start-chat.
- Copy button copies the direct link to `/agents/:shareSlug`.
- Show copied confirmation.

### 5. Shared-Agent Landing Screen

Purpose:
- Let someone else open the link and run the shared agent with their own key.

UI requirements:
- Same agent summary as the published landing screen.
- Clear statement that the creator's API key and chat history are not shared.
- API key connection prompt if needed.
- Start-chat button after key connection.

Behavior:
- Recipient does not need an account.
- Recipient cannot edit or fork the agent.
- Recipient cannot see creator lesson sessions, uploaded images, or chat history.

### 6. Lesson Chat Screen

Purpose:
- Generate and discuss a language lesson from a photo.

Initial state:
- Agent summary compact header.
- Camera capture control.
- Image upload control.
- Empty lesson area.
- Chat input disabled until a lesson exists.

Camera capture requirements:
- Browser camera capture is required in the MVP.
- Use browser camera APIs to let the visitor take a still image.
- Show a clear permission error if camera access is blocked.
- Let the visitor retry camera permission where the browser allows it.
- Submit the captured still image to the same backend endpoint as file uploads.

Image upload requirements:
- Accept PNG, JPEG, WEBP, and non-animated GIF.
- Maximum image size is 10 MB.
- Preview image before submit.
- Allow replacing image before submit.
- Show loading state while lesson is generated.

Lesson result requirements:
- Render generated lesson text clearly.
- Make vocabulary, phrases, and practice questions easy to read.
- Preserve enough context to continue chat.

Chat requirements:
- Text input for follow-up questions.
- Follow-up question max length is 1,000 characters.
- Message list with user and assistant messages.
- Loading state for assistant response.
- Error state with retry.
- Start-over action that clears the current lesson view and lets the user submit
  a new image.

## Client State

### Local UI State

- Current form values
- Form validation errors
- Image preview URL
- Chat input draft
- Copy-share-link confirmation
- Loading and error states

### Server State

Fetch via API:

- API key session status
- Agent draft/create response
- Published agent by share slug
- Lesson session
- Chat messages for active lesson session

### Session Rules

- Do not persist raw OpenAI API keys in localStorage, sessionStorage, IndexedDB,
  or URL params.
- It is acceptable to store non-secret UI state locally if useful.
- If backend session expires, prompt the visitor to reconnect their key.

## API Contract Used by Frontend

The backend spec owns exact implementation details. The frontend should assume
these endpoints or close equivalents.

### API Key Session

`POST /api/runtime/openai-key/validate`

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

`GET /api/runtime/openai-key/status`

Response:

```json
{
  "hasApiKey": true
}
```

`DELETE /api/runtime/openai-key`

Response:

```json
{
  "hasApiKey": false
}
```

### Agents

`POST /api/agents`

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

`POST /api/agents/:agentId/publish`

Response:

```json
{
  "id": "uuid",
  "status": "published",
  "shareSlug": "abc123",
  "shareUrl": "https://example.com/agents/abc123"
}
```

`GET /api/shared-agents/:shareSlug`

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

### Lesson Sessions

`POST /api/shared-agents/:shareSlug/lesson-sessions`

Request:
- Multipart form data with `image`.

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

`GET /api/lesson-sessions/:lessonSessionId`

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

`POST /api/lesson-sessions/:lessonSessionId/messages`

Request:

```json
{
  "content": "Can you give me a simpler example?"
}
```

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

## Error Handling

Show friendly errors for:

- Missing API key
- Invalid API key
- Expired backend key session
- Camera permission denied or unavailable
- Agent not found
- Agent is not published
- Image file type not supported
- Image file too large
- OpenAI request failed
- Network failure

The frontend should avoid exposing raw backend traces or OpenAI error blobs.

## Accessibility

- All form controls need labels.
- Buttons need clear disabled states.
- Icon-only controls need accessible names and tooltips.
- Chat messages should be keyboard navigable.
- Image upload should work without drag-and-drop.
- Copy-share-link action should announce success.

## Visual Direction

The app should feel like a compact work tool, not a marketing landing page.

Design priorities:

- Clear builder form
- Obvious publish/share/start path
- Disabled future tools visible but quiet
- Lesson content easy to scan
- Chat interaction simple and familiar
- No oversized hero
- No marketplace styling

## Acceptance Criteria

- A visitor can connect an OpenAI API key.
- A visitor can create a Photo Language Agent with required fields.
- Dummy capability icons appear but cannot be configured.
- A visitor can publish the agent.
- A visitor can copy a direct share link.
- A recipient can open the share link without logging in.
- A recipient must connect their own OpenAI API key before generating a lesson.
- A visitor can take a camera photo and receive a lesson.
- A visitor can upload an image and receive a lesson.
- A visitor can ask follow-up questions about the lesson.
- The UI never claims to save flashcards, memory, progress, or vocabulary.
- The UI never exposes or shares the creator's API key.

## Frontend Subagent Handoff

The frontend subagent should implement only the React app and mock backend
responses if the backend is not ready. It should not implement FastAPI,
PostgreSQL, OpenAI calls, or database migrations.
