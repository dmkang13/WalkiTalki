# OpenClaw MVP Validation

## Table of Contents

- [Purpose](#purpose)
- [Validation Thesis](#validation-thesis)
- [Success Criteria](#success-criteria)
- [Non-Goals](#non-goals)
- [Target Architecture](#target-architecture)
- [Prebuilt Example Agent](#prebuilt-example-agent)
- [Validation Flow](#validation-flow)
- [Required Runtime Capabilities](#required-runtime-capabilities)
- [Backend Responsibilities](#backend-responsibilities)
- [Frontend Responsibilities](#frontend-responsibilities)
- [OpenClaw Responsibilities](#openclaw-responsibilities)
- [Data to Capture](#data-to-capture)
- [Questions to Answer](#questions-to-answer)
- [Failure Criteria](#failure-criteria)
- [Implementation Notes](#implementation-notes)

## Purpose

This spec exists to validate whether OpenClaw can be the backend-controllable
runtime layer for WalkiTalki.

The OpenClaw MVP is not an agent builder. It should not require any front-end or
back-end agent editing capability.

The MVP should prove one focused runtime loop:

> Can WalkiTalki expose one already-published example agent, let a user log in
> with their ChatGPT account through OpenClaw, optionally add per-session custom
> instructions, upload a photo, and receive a language lesson from that agent?

If the answer is no, the product architecture must change before the broader MVP
grows.

## Validation Thesis

OpenClaw is useful to WalkiTalki only if it can do more than call a model. It
must let WalkiTalki keep the product surface simple while OpenClaw handles model
runtime concerns.

The validation should prove:

- WalkiTalki can expose a prebuilt agent spec from the backend.
- WalkiTalki can initiate an OpenClaw session for that prebuilt agent.
- OpenClaw can trigger or expose a ChatGPT login flow.
- ChatGPT/provider auth can be isolated between different people or browser
  sessions.
- WalkiTalki can pass optional per-session custom instructions into the run.
- WalkiTalki can send chat and image input to OpenClaw.
- OpenClaw can upload or forward an image to the target LLM for vision
  understanding.
- OpenClaw can load and use at least one externally sourced agent skill.
- OpenClaw can call the target LLM using the authenticated ChatGPT/provider
  context.
- WalkiTalki can receive assistant responses and basic runtime metadata.

## Success Criteria

The validation succeeds if all of these are true:

- The backend exposes one already-published example agent.
- The frontend can display and launch that agent without editing it.
- The backend can create an OpenClaw runtime session for the example agent.
- The backend can tell the frontend whether the runtime session needs ChatGPT
  login.
- The frontend can send the person into the ChatGPT/provider login flow.
- After login, the backend can resume or confirm the OpenClaw runtime session.
- Optional custom instructions can be attached to the current session without
  modifying the published agent.
- The backend can send a text message through OpenClaw and receive an assistant
  response.
- The backend can send image input through OpenClaw or through an OpenClaw-
  approved target-LLM path.
- The target LLM can actually inspect the uploaded image and produce a lesson
  grounded in visible objects.
- An OpenClaw runtime session can load an externally sourced skill and produce
  observable behavior that proves the skill was available to the agent.
- Two different browser sessions can run the same example agent without sharing
  auth, uploaded images, chat history, session instructions, or skill state.
- WalkiTalki never asks the user to paste an OpenAI API key.
- WalkiTalki can display at least basic model/provider status, and preferably
  usage metadata.

## Non-Goals

This validation does not include:

- Agent builder UI
- Agent editing API
- Agent creation API
- Agent publishing API
- Multiple agents
- Full production auth
- WalkiTalki user accounts
- Flashcards
- Memory
- Vector stores
- External APIs
- Scripts
- Audio
- Marketplace functionality
- Long-term token storage design
- Multi-provider picker UI
- Billing UI
- Admin tooling
- Production deployment hardening

The goal is to validate the runtime architecture, not to finish the product.

External APIs remain out of scope. The required validation skill should be an
instruction-only or otherwise low-risk skill used to prove OpenClaw skill
loading, not a third-party integration.

## Target Architecture

The target validation shape:

1. React calls the WalkiTalki backend.
2. WalkiTalki backend loads the prebuilt example agent.
3. WalkiTalki backend calls OpenClaw.
4. OpenClaw manages ChatGPT/provider authentication and runtime execution.
5. The target LLM performs model compute.
6. OpenClaw returns assistant output to the backend.
7. Backend returns chat output to React.

React should not call OpenClaw directly.

WalkiTalki should not store pasted provider API keys.

## Prebuilt Example Agent

The OpenClaw MVP should include one example agent capability living in the
backend.

The example agent is already published from the product's point of view. There
is no create, edit, publish, unpublish, or delete flow in this validation.

The example agent should include:

- Agent name
- Short description
- Target language
- Native language, if desired
- Fixed system instructions
- Required image input capability
- Required ChatGPT/provider login capability
- One allowed validation skill

The frontend may display the agent summary, but it cannot edit the saved agent
spec.

Optional custom instructions are allowed only as session-level overrides. They
should influence the current run without changing the backend's prebuilt agent
definition.

## Validation Flow

### 1. Load Example Agent

Frontend opens the OpenClaw MVP page.

Backend returns the already-published example agent summary.

Frontend displays:

- Agent name
- Description
- Target language
- Required photo input
- ChatGPT login requirement
- Optional custom instructions field

### 2. Start Runtime Session

User clicks Start Chat.

Frontend sends any optional custom instructions to the backend as session input.

Backend asks OpenClaw to create a runtime session for the prebuilt agent and the
session-level custom instructions.

Backend returns one of these states:

- Runtime ready
- ChatGPT/provider login required
- Runtime creation failed

### 3. Complete ChatGPT Login

If login is required, frontend sends the user through the OpenClaw/provider login
flow.

After the login returns, frontend asks backend to confirm the runtime session.

Backend confirms with OpenClaw that the session has an authenticated provider
context.

### 4. Send Text Message

Frontend sends a simple text prompt to the backend.

Backend forwards it to OpenClaw.

OpenClaw invokes the target LLM.

Backend returns the assistant response to the frontend.

### 5. Send Image Lesson Request

Frontend sends an image and lesson prompt to the backend.

Backend forwards the image, prebuilt agent context, optional session
instructions, and target LLM requirement to OpenClaw.

OpenClaw invokes a model-provider path that supports image understanding.

Backend returns the generated lesson to the frontend.

The response must demonstrate that the target LLM received the image, not just a
text placeholder. The simplest check is to ask the model to name visible objects
and produce vocabulary from those objects.

### 6. Invoke Validation Skill

Backend sends a message that should trigger the allowed validation skill.

OpenClaw loads the skill into the runtime context and lets the agent use it.

Backend returns the assistant response and any available skill-use metadata.

The validation skill can be any low-risk public skill found on the internet,
such as a simple greeting, formatting, translation-helper, or lesson-structure
skill. Prefer a skill that does not require credentials, shell execution,
network access, private data access, or writes to disk.

The point is not which skill is useful to WalkiTalki. The point is proving that
the backend can select a skill for the prebuilt agent, OpenClaw can load that
skill, and the target LLM can follow the skill's instructions during a session.

### 7. Verify Isolation

Repeat the flow in a second browser session.

The second session should require its own ChatGPT/provider authentication or use
only its own already-authenticated provider profile.

The second session must not inherit the first session's auth, uploaded image,
chat history, custom instructions, runtime state, or skill state.

## Required Runtime Capabilities

### ChatGPT Login

The OpenClaw MVP must prove that the user can authenticate with their ChatGPT or
OpenAI-provider account through OpenClaw before running the agent.

Validation requirements:

- Frontend can show a clear login-required state.
- Backend can start or receive the OpenClaw login flow.
- Backend can confirm when the runtime session is authenticated.
- Runtime calls use the authenticated provider context.
- WalkiTalki does not ask for a pasted OpenAI API key.

### Session Custom Instructions

The OpenClaw MVP may allow the user to add custom instructions before starting
the session.

Validation requirements:

- Custom instructions are optional.
- Custom instructions apply only to the current runtime session.
- Custom instructions do not mutate the backend's prebuilt example agent.
- The assistant response reflects the instructions when they are relevant.

### Image Upload to Target LLM

The OpenClaw MVP must prove that image input can reach the same target LLM that
is powering the agent chat.

Validation requirements:

- Frontend can provide an image through upload.
- Camera capture can be added later, but is not required for the OpenClaw
  validation.
- Backend can pass the image to OpenClaw without exposing provider credentials to
  the frontend.
- OpenClaw can route the image to a vision-capable target LLM.
- The target LLM can return a lesson grounded in visible objects.
- Follow-up chat can refer back to the same image context.

This is a hard requirement. If image upload only works outside OpenClaw, then the
OpenClaw architecture does not yet support the core WalkiTalki MVP.

### Agent Skill Use

The OpenClaw MVP must prove that the prebuilt agent can include at least one
allowed skill and that OpenClaw can make that skill available during runtime.

Validation requirements:

- Choose one low-risk public skill from an external source.
- Review the skill before enabling it.
- Add the skill to the OpenClaw runtime in a scoped location for this validation.
- Allowlist that skill for the prebuilt example agent.
- Trigger behavior that clearly depends on the skill being loaded.
- Record whether OpenClaw exposes skill-use metadata or only the final assistant
  response.

Use the smallest possible skill. A skill that teaches the agent how to format a
language lesson is better than a powerful automation skill.

Do not validate with a skill that needs credentials, shell execution, broad file
access, browser control, or external writes. Internet-sourced skills should be
treated as untrusted until reviewed.

## Backend Responsibilities

The backend validation should prove these operations:

- Serve the prebuilt example agent summary
- Create OpenClaw runtime session for the prebuilt agent
- Attach optional session custom instructions
- Report runtime status to frontend
- Start provider login or return login URL/state
- Confirm provider login completion
- Send text message to OpenClaw session
- Send image lesson request to OpenClaw session
- Send an image in a format OpenClaw can route to the target LLM
- Select one allowed skill for the prebuilt agent
- Trigger and observe skill-dependent behavior
- Return assistant response to frontend
- Return model/provider/usage metadata when available
- Keep OpenClaw session references separate per browser session

The backend should remain the only application layer that talks to OpenClaw.

## Frontend Responsibilities

The frontend validation should prove these screens or states:

- Example agent launch screen
- Optional custom instructions input
- Start Chat button
- ChatGPT/provider login required state
- Provider login in progress state
- Runtime ready state
- Image upload
- Chat display
- Skill validation result state
- Runtime error display
- Model/provider status display

The frontend should present OpenClaw as part of the runtime plumbing, not as the
main product brand.

The frontend should not include agent create, edit, publish, or builder flows for
this validation.

## OpenClaw Responsibilities

OpenClaw must prove it can provide:

- Backend-controlled session creation
- ChatGPT/provider OAuth or login initiation
- Authenticated provider profile attachment to a runtime session
- Runtime isolation between sessions
- Model invocation
- Image-capable model invocation or routing
- Image upload or forwarding into the target LLM
- Session-level custom instruction handling
- Skill loading from a reviewed external source
- Per-agent skill allowlisting
- Observable skill-dependent behavior
- Tool or skill orchestration path for future WalkiTalki capabilities
- Runtime metadata returned to WalkiTalki
- Clear errors when auth, provider, or model invocation fails

## Data to Capture

During validation, capture:

- OpenClaw session ID or reference
- Example agent ID
- Provider connection status
- Provider/model name, if available
- Runtime status
- Session custom instructions presence, not necessarily full content
- Target LLM name or identifier, if available
- Image upload status
- Validation skill name and source
- Skill availability status
- Skill invocation evidence or skill-dependent assistant output
- Assistant responses
- Usage metadata, if available
- Error category and message
- Browser session identifier used by WalkiTalki for the prototype

Do not capture:

- Provider API keys
- Provider refresh tokens, unless OpenClaw requires storage outside WalkiTalki
  and a separate security spec approves it
- Creator provider auth
- Shared user chat history across sessions

## Questions to Answer

The validation must answer:

- Does OpenClaw support the ChatGPT/provider login flow we need?
- Is this login with a user's ChatGPT/provider account, or only app-level
  authentication?
- Can the backend initiate and control the flow cleanly?
- Can WalkiTalki attach an OpenClaw runtime session to a browser session without
  creating full WalkiTalki user accounts?
- Can provider auth be isolated across people running the same prebuilt agent?
- Can optional custom instructions be attached to one session without editing
  the prebuilt agent?
- Can OpenClaw run an image-understanding lesson flow?
- Is the image actually sent to the target LLM used by the agent session?
- Which image formats and size limits does the OpenClaw path support?
- Can OpenClaw load a reviewed public skill from the internet?
- Can WalkiTalki allowlist a specific skill for the prebuilt agent?
- Can WalkiTalki tell whether the skill was actually available or invoked?
- Can OpenClaw return useful usage metadata?
- What happens when the user cancels provider login?
- What happens when provider auth expires?
- What happens when the provider account has no model access?
- What happens when OpenClaw is unavailable?

## Failure Criteria

The validation fails if any of these are true:

- OpenClaw cannot initiate provider login from a backend-controlled flow.
- OpenClaw requires one shared provider auth profile for all browser sessions.
- OpenClaw cannot isolate provider auth between sessions.
- OpenClaw cannot support image-capable model calls for the lesson flow.
- OpenClaw cannot upload or route images to the target LLM.
- OpenClaw cannot attach session-level custom instructions.
- OpenClaw cannot load a scoped externally sourced skill.
- OpenClaw cannot restrict the validation agent to a specific skill allowlist.
- WalkiTalki must handle pasted provider API keys anyway.
- Usage cannot be attributed to the authenticated provider context.
- The runtime flow is too confusing to explain in the product.
- Errors from OpenClaw are too opaque to make the UX understandable.

## Implementation Notes

Keep the validation intentionally small:

- One backend-owned prebuilt example agent
- No agent editing
- No agent builder
- No publish flow
- One backend integration path
- One ChatGPT/provider login flow
- One optional custom instructions field
- One text message call
- One image upload lesson call
- One image-to-target-LLM verification
- One reviewed external skill
- One skill invocation check
- One second-session isolation check

This should be built before rewriting the full MVP implementation around
OpenClaw. The point is to discover whether the architecture is real while the
blast radius is still small.
