# WalkiTalki MVP

## Table of Contents

- [WalkiTalki MVP](#walkitalki-mvp)
  - [Table of Contents](#table-of-contents)
  - [MVP Thesis](#mvp-thesis)
  - [The One User Promise](#the-one-user-promise)
  - [Yes](#yes)
  - [No](#no)
  - [The First Experience](#the-first-experience)
    - [Photo Language Agent](#photo-language-agent)
  - [MVP User Flows](#mvp-user-flows)
    - [1. Connect OpenAI API Key](#1-connect-openai-api-key)
    - [2. Build Photo Language Agent](#2-build-photo-language-agent)
    - [3. Share Published Agent Link](#3-share-published-agent-link)
    - [4. Start Photo Lesson Chat](#4-start-photo-lesson-chat)
    - [5. Chat About the Lesson](#5-chat-about-the-lesson)
  - [MVP Screens](#mvp-screens)
    - [Required Screens](#required-screens)
    - [Not Required](#not-required)
  - [MVP Platform Capabilities](#mvp-platform-capabilities)
    - [BYOK Compute](#byok-compute)
    - [Constrained Agent Builder](#constrained-agent-builder)
    - [Publish](#publish)
    - [Direct Link Sharing](#direct-link-sharing)
    - [Image and Camera Input](#image-and-camera-input)
    - [Lesson Chat Session](#lesson-chat-session)
  - [MVP Data Concepts](#mvp-data-concepts)
  - [What This MVP Must Prove](#what-this-mvp-must-prove)
  - [Failure Modes We Want to Discover](#failure-modes-we-want-to-discover)
  - [Build Order](#build-order)
  - [Technical Specs to Write Next](#technical-specs-to-write-next)

## MVP Thesis

The MVP is not an agent marketplace. It is not a flashcard app. It is not a
general-purpose no-code agent builder. It is not a social learning network.

The MVP is a focused test of one idea:

> Can a user build a constrained photo-language agent, publish it into a runnable
> state, share it by link, take or upload a picture, get a useful language
> lesson about what the model sees, and chat naturally about those things?

Everything else is distraction until this loop works.

In this MVP, "user" means the person operating the prototype. It does not imply
a stored user account, user table, sign-up system, team system, or identity
platform.

## The One User Promise

A user can connect their own OpenAI API key, build a simple photo-language
agent, publish it privately, share it by link, start a chat with it, take or
upload a picture, receive a short language lesson defining what is visible in
the picture, and chat with the agent about those objects, words, and phrases.

Someone else can open the shared link, bring their own OpenAI API key, and run
the same published agent spec for their own photo lesson.

## Yes

The MVP includes:

- User-owned OpenAI API key connection
- No account creation or user management
- One constrained photo-language agent builder
- Private publish step that makes the agent runnable
- Direct share link for the published photo-language agent
- Shared-agent landing screen for recipients
- Start-chat action from the published agent
- Target language selection in the builder
- Basic teaching style and instruction fields
- Disabled dummy capability icons in the builder
- Image upload
- Camera photo input if easy on web
- Generated language lesson from the image
- Vocabulary and phrase explanations based on visible objects
- Follow-up chat about the image and lesson
- Basic session history for the current lesson
- Basic usage visibility for the user's own key

## No

The MVP does not include:

- Flashcards
- Saved vocabulary lists
- Lesson progress tracking
- Full agent library
- General-purpose agent builder
- Agent marketplace
- Forking
- Public publishing
- Public profiles
- Ratings
- Reviews
- Classroom mode
- Group sharing
- Social feed
- Comments
- Story sharing
- Writing critique community
- Multiple templates
- User-created skills
- Skill marketplace
- Functional versions of the dummy builder icons
- Visual canvas builder
- Drag-and-drop tool graph
- Arbitrary tools
- Arbitrary OpenAPI import
- Third-party API keys
- OAuth integrations
- External actions
- Scripts
- Workflow automation
- Scheduled agents
- Multi-agent handoffs
- Audio
- Microphone
- Pronunciation scoring
- Live listening
- Conversation voice mode
- ELO system
- Complex progress analytics
- Custom database schemas
- Vector stores
- Memory
- Uploaded documents
- Advanced model controls
- Multiple model providers
- Creator-funded agents
- Free unlimited compute
- Admin moderation tools
- User account database
- User management
- Authentication system beyond what is minimally needed to run the prototype
- Version history UI
- Mobile app

If it is not required for build-to-publish-to-share-to-picture-lesson-to-chat, it
is not in the MVP.

## The First Experience

The MVP should ship one constrained buildable agent type:

### Photo Language Agent

Purpose:
- Turn a real-world photo into a short language lesson.

Builder inputs:
- Agent name
- Target language
- Optional native language
- Teaching style
- Optional custom instructions
- Disabled future capability icons for visual context only

Run inputs:
- Image upload or camera photo
- Follow-up text questions

Agent behavior:
- Identify important visible objects.
- Name those objects in the target language.
- Define the words in plain language.
- Provide pronunciation help if text-only pronunciation guidance is useful.
- Give a few practical phrases using the visible objects.
- Ask one or two follow-up practice questions.
- Let the user chat about the objects, words, and phrases.

Not allowed:
- Save flashcards.
- Save vocabulary.
- Track progress.
- Access microphone.
- Use external APIs.
- Run scripts.
- Share the creator's OpenAI API key.
- Share lesson session history.
- Publish publicly.
- Add new tools.

## MVP User Flows

### 1. Connect OpenAI API Key

1. User opens WalkiTalki.
2. User is asked to connect an OpenAI API key.
3. User pastes the key.
4. WalkiTalki validates that the key can be used.
5. WalkiTalki keeps the key available only for the current prototype session
   unless a later technical spec explicitly adds secure key persistence.
6. User is notified that AI compute is paid through their own key.

Hard rule:
- No key, no lesson generation.

### 2. Build Photo Language Agent

1. User opens the agent builder.
2. User configures the fixed Photo Language Agent:
   - Agent name
   - Target language
   - Optional native language
   - Optional custom instructions
3. User sees dummy capability icons for possible future tools, such as
   flashcards, memory, documents, vector recall, audio, API tools, scripts, and
   classroom mode.
4. User previews the agent summary.
5. User publishes the agent privately.

Hard rule:
- Publishing means the agent is runnable by the creator and shareable by direct
  link. It does not mean marketplace listing, account-backed ownership, forking,
  or public discovery.

### 3. Share Published Agent Link

1. User opens the published agent.
2. User clicks a share-link action.
3. WalkiTalki creates a direct link to the published Photo Language Agent spec.
4. User sends that link to someone else outside WalkiTalki.
5. Recipient opens the link.
6. Recipient sees the agent summary and understands they need their own OpenAI
   API key to run it.
7. Recipient connects their own key for the current prototype session.
8. Recipient starts a new chat with the shared agent.

Hard rule:
- The link shares the agent spec only. It does not share the creator's API key,
  lesson session, uploaded image, chat history, or private data.

### 4. Start Photo Lesson Chat

1. User opens the published agent or a shared-agent link.
2. User starts a chat.
3. User uploads or takes a picture.
4. User submits the image.
5. OpenAI analyzes the image and generates the language lesson.
6. User sees the lesson.

### 5. Chat About the Lesson

1. User asks follow-up questions.
2. Agent answers using the image and generated lesson context.
3. User can ask for examples, corrections, pronunciation guidance, or simpler
   explanations.
4. User can start over with a new image.

## MVP Screens

### Required Screens

- Connect OpenAI API key
- Build Photo Language Agent
- Published agent launch screen
- Share link action
- Shared-agent landing screen
- Lesson result and chat screen
- Basic usage notice

### Not Required

- Sign-up
- Login
- Account settings
- User management
- Full agent library
- General-purpose create/edit agent flow
- Flashcards list
- Fork page
- Marketplace
- User profiles
- Public indexed agent pages
- Classroom dashboard
- Admin dashboard
- Skill marketplace
- Visual workflow editor
- Analytics dashboard

## MVP Platform Capabilities

### BYOK Compute

Users run the lesson with their own OpenAI API key.

WalkiTalki should make this obvious in the UX. Users should not be surprised
that their key is being used.

The MVP should avoid user-account infrastructure. BYOK is a prototype/session
input, not proof that WalkiTalki has a full user identity system.

### Constrained Agent Builder

The MVP should let the user build one kind of agent: a Photo Language Agent.

The builder should feel like configuring a template, not assembling a tool
system. The user can name the agent and set its language behavior, but cannot add
arbitrary tools.

The builder can show a small grid of future capability icons so the product feels
like an agent-building platform, not a one-off prompt form. These icons are
visual placeholders only. They should be disabled, clearly non-functional, and
excluded from the runtime agent schema.

### Publish

Publishing makes the configured agent runnable by the creator.

Publishing also enables a direct share link to the published agent spec. Once published anyone with the link should be able to see it.

Publishing does not mean marketplace listing, public discovery, account-backed
ownership, or forking.

### Direct Link Sharing

The MVP should allow the creator to copy a link to the published Photo Language
Agent.

Someone who opens the link should see the agent summary, connect their own
OpenAI API key, and start a new photo lesson chat using the same agent spec.

Direct link sharing does not include:

- Creator API key
- Creator image
- Creator lesson session
- Creator chat history
- Creator private data
- Forking
- Comments
- Profiles
- Ratings
- Search or marketplace placement

### Image and Camera Input

The app must accept an image and send it to the model with the lesson prompt.

Camera and image upload would be good for the first working
prototype if browser camera handling slows the build.

### Lesson Chat Session

Each image creates one lesson session.

The session should preserve enough context for follow-up chat about:

- The image
- The visible objects
- The generated vocabulary
- The generated phrases
- The user's follow-up questions

No persistent memory is needed.

## MVP Data Concepts

Keep data concepts minimal:

- OpenAI API key for the current prototype session
- Photo Language Agent spec
- Published agent state
- Share token or share URL for the published agent spec
- Lesson session
- Uploaded image reference, if the image must be stored temporarily
- Generated lesson text
- Chat messages for the active lesson
- Basic usage estimate

Do not create a user object for the MVP. Treat the operator as a hypothetical
actor using the local prototype.

Do not attach the API key, agent spec, published state, or lesson session to a
persisted user account in the MVP.

Do not design the full future database yet.

## What This MVP Must Prove

The MVP must answer:

- Does picture-to-language-lesson feel valuable?
- Can users build a useful constrained agent without getting lost?
- Does the private publish step make sense?
- Does the model identify useful objects accurately enough?
- Is the generated lesson clear and useful?
- Does follow-up chat make the lesson meaningfully better?
- Does BYOK block too many users?
- Do users understand that their key pays for compute?
- Does direct-link sharing make the agent feel reusable without requiring
  accounts?
- Do recipients understand that they must bring their own OpenAI API key?
- Do dummy builder icons help users imagine the platform, or do they feel broken?
- Is image upload enough, or is camera capture essential?
- Is this compelling enough to justify agents, sharing, flashcards, memory, and
  vector recall later?

## Failure Modes We Want to Discover

The MVP should expose the painful truths early:

- Users do not want to bring their own OpenAI API key.
- Users do not understand API keys.
- Users do not know how to configure even a simple agent.
- The publish step feels unnecessary or confusing.
- Recipients abandon the shared link when asked for their own OpenAI API key.
- Users assume the shared link includes the creator's API key or lesson history.
- Dummy capability icons look clickable and broken instead of intentionally
  disabled.
- Image lessons are not compelling.
- Object recognition is too unreliable.
- Lessons are too generic.
- Follow-up chat does not add much value.
- Users immediately want saving/review features.
- Users immediately want audio/pronunciation.
- Cost visibility is insufficient.
- The experience is fun once but not repeatable.

These failures are useful. The MVP should find them before the platform gets
bigger.

## Build Order

1. OpenAI API key entry
2. Constrained Photo Language Agent builder
3. Disabled future capability icons in the builder
4. Private publish step
5. Published agent launch screen
6. Direct share link
7. Shared-agent landing screen
8. Image upload
9. Photo lesson prompt
10. Lesson generation
11. Lesson display
12. Follow-up chat using the same image/lesson context
13. Start-over-with-new-image flow
14. Basic usage notice
15. Optional browser camera capture

Do not start flashcards, vector stores, memory, marketplace, OpenAPI import,
scripts, audio, arbitrary tools, custom skills, forking, accounts, or public
discovery until this flow works.

## Technical Specs to Write Next

Write these after this MVP scope is accepted:

1. Photo Lesson Product Spec
2. OpenAI BYOK Spec
3. Photo Language Agent Builder Spec
4. Private Publish Spec
5. Direct Link Sharing Spec
6. Builder Capability Icon Spec
7. Photo Lesson Prompt Spec
8. Image Input Flow Spec
9. Lesson Chat Session Spec
10. Minimal Data Model Spec
11. MVP Screen Spec
12. MVP Test Plan

Each technical spec should be small, implementable, and directly tied to the
build-to-publish-to-share-to-picture-lesson-to-chat flow.
