# OpenClaw MVP Validation

## Table of Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Success Criteria](#success-criteria)
- [Architecture](#architecture)
- [Example Agent](#example-agent)
- [Validation Flow](#validation-flow)
- [Responsibilities](#responsibilities)
- [Data to Capture](#data-to-capture)
- [Open Questions](#open-questions)
- [Failure Criteria](#failure-criteria)
- [Implementation Notes](#implementation-notes)

## Purpose

Validate whether OpenClaw can be WalkiTalki's backend-controlled runtime for one
prebuilt photo-language agent.

The OpenClaw MVP should answer:

> Can a user open one already-published agent, log in with ChatGPT through
> OpenClaw, optionally add session-only instructions, upload a photo, and receive
> a language lesson from the target LLM?

This is a runtime validation, not an agent-building product.

## Scope

In scope:

- One backend-owned, already-published example agent
- ChatGPT/provider login through OpenClaw
- Optional per-session custom instructions
- Image upload to the target LLM
- Follow-up chat in the same runtime session
- One reviewed, low-risk external skill attached to the agent
- Basic model/provider status and usage metadata, if available
- Session isolation across browser sessions

Out of scope:

- Agent builder UI
- Agent creation, editing, publishing, or deletion APIs
- Multiple agents
- WalkiTalki user accounts
- Pasted OpenAI API keys
- Flashcards, memory, vector stores, uploaded documents, audio, scripts, and
  external API integrations
- Marketplace, billing, admin tools, and production auth hardening

The validation skill should be instruction-only or similarly low risk. It should
prove OpenClaw skill loading, not third-party API integration.

## Success Criteria

The validation succeeds only if:

- Frontend can display and launch the prebuilt agent without editing it.
- Backend can create an OpenClaw runtime session for that agent.
- OpenClaw can initiate or expose ChatGPT/provider login.
- Backend can confirm the session is authenticated after login.
- Optional custom instructions affect only the current session.
- Backend can send text and image input to OpenClaw.
- The target LLM actually inspects the image and returns a lesson grounded in
  visible objects.
- The prebuilt agent can use one allowlisted external skill with observable
  skill-dependent behavior.
- Two browser sessions do not share auth, images, chat history, custom
  instructions, runtime state, or skill state.
- WalkiTalki never asks for or stores pasted provider API keys.

## Architecture

1. React calls the WalkiTalki backend.
2. Backend loads the prebuilt example agent.
3. Backend creates and manages an OpenClaw runtime session.
4. OpenClaw handles ChatGPT/provider login, model calls, image routing, and skill
   loading.
5. The target LLM performs the language lesson and chat.
6. Backend returns assistant output and metadata to React.

React should never call OpenClaw directly.

## Example Agent

The backend owns one already-published agent definition.

The definition includes:

- Agent ID
- Name
- Short description
- Target language
- Optional native language
- Fixed system instructions
- Required image input capability
- Required ChatGPT/provider login capability
- One allowed validation skill

The frontend may display this summary but cannot edit the saved definition.
Custom instructions are session-only overlays.

## Validation Flow

### 1. Load Agent

Frontend opens the OpenClaw MVP page and receives the example agent summary from
the backend.

### 2. Start Session

User clicks Start Chat. Frontend sends optional custom instructions. Backend
creates an OpenClaw runtime session for the example agent.

Backend returns:

- Runtime ready
- ChatGPT/provider login required
- Runtime creation failed

### 3. Complete Login

If login is required, frontend sends the user through the OpenClaw/provider login
flow. Backend then confirms the runtime session is authenticated.

### 4. Send Text

Frontend sends a text prompt. Backend forwards it to OpenClaw and returns the
assistant response.

### 5. Send Image

Frontend uploads a photo. Backend forwards the image, agent context, and
session-only instructions to OpenClaw.

The response must prove the target LLM saw the image by naming visible objects
and turning them into target-language vocabulary or phrases.

### 6. Invoke Skill

Backend sends a prompt that should trigger the allowlisted validation skill.

Use a reviewed public skill that needs no credentials, shell execution, browser
control, private data access, or external writes.

The result must show either explicit skill-use metadata or assistant behavior
that clearly depends on the skill being loaded.

### 7. Verify Isolation

Repeat the flow in a second browser session. The second session must not inherit
the first session's auth, image, chat, custom instructions, runtime state, or
skill state.

## Responsibilities

Backend:

- Serve the prebuilt agent summary.
- Create and track OpenClaw runtime sessions.
- Pass session-only custom instructions.
- Start and confirm ChatGPT/provider login.
- Send text, image, and skill-validation prompts to OpenClaw.
- Return assistant responses, errors, and available metadata.
- Keep browser sessions isolated.

Frontend:

- Display the example agent.
- Provide Start Chat, login state, optional custom instructions, image upload,
  chat, skill validation result, runtime errors, and model/provider status.
- Avoid all create, edit, publish, and builder flows.

OpenClaw:

- Provide backend-controlled session creation.
- Handle ChatGPT/provider login and authenticated runtime use.
- Route images to the target LLM.
- Apply session-only custom instructions.
- Load one reviewed external skill with per-agent allowlisting.
- Return usable responses, errors, and metadata.

## Data to Capture

- OpenClaw session ID or reference
- Example agent ID
- Provider connection status
- Provider/model name, if available
- Runtime status
- Whether custom instructions were provided
- Image upload status
- Validation skill name and source
- Skill availability or invocation evidence
- Assistant responses
- Usage metadata, if available
- Error category and message
- Browser session identifier

Do not capture provider API keys, provider refresh tokens, creator auth, or chat
history shared across sessions.

## Open Questions

- Does OpenClaw support the ChatGPT/provider login flow WalkiTalki needs?
- Is the login tied to the user's provider account, or only app-level auth?
- Can backend code initiate and confirm the flow cleanly?
- Can this work without WalkiTalki user accounts?
- Can provider auth stay isolated across browser sessions?
- Can session-only custom instructions be attached without editing the agent?
- Does the image reach the same target LLM used by the chat session?
- Which image formats and size limits are supported?
- Can OpenClaw load a reviewed public skill and restrict the agent to that skill?
- Can WalkiTalki tell whether the skill was available or invoked?
- Can OpenClaw return useful usage metadata?
- What happens when login is canceled, expires, lacks model access, or OpenClaw
  is unavailable?

## Failure Criteria

The validation fails if:

- OpenClaw cannot initiate provider login from a backend-controlled flow.
- OpenClaw requires one shared provider auth profile for all browser sessions.
- OpenClaw cannot isolate auth or runtime state between sessions.
- OpenClaw cannot route uploaded images to the target LLM.
- OpenClaw cannot attach session-only custom instructions.
- OpenClaw cannot load and restrict one scoped external skill.
- WalkiTalki must handle pasted provider API keys.
- Usage cannot be attributed to the authenticated provider context.
- Errors are too opaque to make the UX understandable.

## Implementation Notes

Keep the validation intentionally small:

- One prebuilt backend agent
- No agent builder or editing
- One OpenClaw integration path
- One ChatGPT/provider login flow
- One optional custom instructions field
- One text call
- One image lesson call
- One reviewed external skill
- One second-session isolation check

Build this before rewriting the full MVP around OpenClaw. The goal is to find
out whether the architecture is real while the blast radius is still small.
