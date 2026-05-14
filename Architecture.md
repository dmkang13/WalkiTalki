# WalkiTalki Agent Platform Architecture

## Table of Contents

- [Purpose](#purpose)
- [Product Thesis](#product-thesis)
- [Platform Boundary](#platform-boundary)
- [What an Agent Spec Is](#what-an-agent-spec-is)
- [Core Product Surfaces](#core-product-surfaces)
- [Capability Blocks](#capability-blocks)
- [User-Owned Compute](#user-owned-compute)
- [Agent Sessions](#agent-sessions)
- [Sharing Model](#sharing-model)
- [Data and Knowledge Model](#data-and-knowledge-model)
- [Trust and Safety](#trust-and-safety)
- [Platform Possibilities](#platform-possibilities)
- [What This Document Avoids](#what-this-document-avoids)
- [Follow-On Specs](#follow-on-specs)

## Purpose

WalkiTalki is a platform for creating, running, and sharing AI agent specs.

The platform should make it easy for a user to define an agent, connect their
own OpenAI API key, grant the agent access to selected WalkiTalki resources, and
share or fork that agent with other users.

This document describes the shape of the platform and the possibilities it could
support. It intentionally avoids table schemas, endpoint definitions, and
implementation-level detail. Those should live in follow-on technical specs.

## Product Thesis

The product is not "agent infrastructure." The product is a place where normal
users can create useful AI assistants without understanding agent
infrastructure.

For WalkiTalki specifically, the first valuable category is language-learning
agents:

- Photo vocabulary tutors
- Flashcard generators
- Writing coaches
- Reading companions
- Lesson planners
- Quiz creators
- Personal recall tutors

The long-term platform can support many agent categories, but the first product
experience should prove that a user can build a constrained photo-language
agent, publish it privately, share it by direct link, run it on a picture, and
chat about what the model sees before adding flashcards, memory, forking, or
marketplace mechanics.

## Platform Boundary

WalkiTalki and OpenAI should have a clean separation of responsibilities.

WalkiTalki is the platform layer. It owns:

- User accounts in the future platform, but not in the MVP
- Agent specs
- Agent names, descriptions, and share links
- Skill IDs and curated capability definitions
- WalkiTalki data such as flashcards, uploaded documents, lessons, memories, and
  progress
- Vector store ownership and metadata
- User-owned OpenAI API key references
- Session grants for WalkiTalki resources
- Sharing, forking, and visibility rules
- Usage visibility and platform audit history

OpenAI is the runtime and compute layer. It handles:

- LLM reasoning
- Chatbot interaction
- Image understanding
- Tool selection from the tools included in the selected agent session
- Structured outputs when needed
- Retrieval or file search if WalkiTalki chooses to use OpenAI-hosted vector
  stores

WalkiTalki should not try to become a full agent runtime. It should create clean
agent specs and expose clean resource interfaces. OpenAI should do the heavy
model work.

## What an Agent Spec Is

An agent spec is the shareable definition of an agent.

At a product level, an agent spec includes:

- Name
- Description
- Instructions
- Intended user goal
- Enabled capability blocks
- Required WalkiTalki resources
- Required user-owned OpenAI API key
- Sharing settings
- Version identity

An agent spec should be shareable without sharing private user data.

When a user forks a shared agent, they copy the reusable spec, not the creator's
API key, private memory, private flashcards, private documents, or private vector
stores.

## Core Product Surfaces

### Agent Library

The library is where users access agents.

It should support:

- Agents I created
- Agents shared with me
- Agents I forked
- Recently used agents
- A simple create-agent action

The library should not feel like a marketplace in the MVP. A marketplace invites
moderation, ranking, search, abuse, creator incentives, and support burden too
early.

### Agent Builder

The builder is where users create and edit an agent spec.

The builder should start as a boring, reliable form. Avoid a canvas until there
is proof that users need visual composition.

For the MVP, the builder can still show a set of disabled future capability
icons. These icons help users understand that agents are made of interchangeable
building blocks, but they should not add real runtime capability until the core
photo-language loop is proven.

The builder should help users answer:

- What is this agent for?
- What should it do?
- What should it not do?
- What WalkiTalki resources can it use?
- What should happen when it creates or changes user data?

### Agent Runner

The runner is the chat experience for using an agent.

It should support:

- Text chat
- Image input for photo-based lessons
- Clear indication of which agent is running
- Clear indication of which resources the session can access
- Approval moments for writes or high-impact actions

### Share and Fork

MVP sharing should be simple:

- Share by link
- Recipient can view the spec
- Recipient must use their own OpenAI API key
- Recipient can start a new session with the shared agent

Forking is a future platform behavior. It should not be required to prove that a
shared photo-language agent can travel by link and run for someone else.

## Capability Blocks

Capability blocks are the user-facing building blocks of an agent spec. They
should be understandable before they are powerful.

### Instructions

Defines the agent's goal, tone, behavior, and boundaries.

This is the most important block. Most early value will come from better
instructions and better templates, not more tools.

### Skills

Skills are reusable WalkiTalki-defined capability packages.

Early skills should be curated by WalkiTalki, not user-created. Skill IDs matter
because WalkiTalki is the platform where agents are shared and forked.

Examples:

- Photo vocabulary tutor
- Flashcard generator
- Writing feedback coach
- Reading comprehension helper

### Image Input

Allows an agent to work with photos or uploaded images.

This is central to the WalkiTalki concept because it lets users turn real-world
context into language practice.

### Flashcard Access

Allows an agent to read or create flashcards inside WalkiTalki.

This is a strong future database-backed action because it turns an agent
conversation into durable learning material. It is not required for the first
MVP.

### Uploaded Documents

Allows an agent to use user-provided or shared documents as learning material.

Documents should remain database-owned product records. If they are indexed for
retrieval, the vector store should be treated as a search layer, not the source
of truth.

### Vector Recall

Allows an agent to retrieve relevant prior context.

Use vector stores for fuzzy recall:

- Similar prior mistakes
- Related past lessons
- User notes
- Chunks from uploaded documents
- Memory-like snippets

Vector recall is useful, but it should not become a substitute for structured
product data.

### Memory

Allows an agent to remember lightweight personal preferences.

Memory should be private, user-specific, editable, and limited. It should not be
the primary place where WalkiTalki stores important product records.

### External API Actions

External API tools may eventually let users connect agents to third-party
services.

This is not an MVP capability. It creates security, support, validation,
credential, and product-complexity problems before the photo lesson loop is
proven.

### Scripts and Workflows

Scripts may eventually let agents trigger approved workflows.

This should be delayed. Arbitrary scripts create a much bigger trust and safety
surface than the platform needs at the beginning.

### Audio and Microphone

Audio may eventually support pronunciation, live listening, transcription, and
conversation practice.

This should stay deferred until the text, image, lesson, chat, and BYOK loops are
working.

## User-Owned Compute

User-owned OpenAI API keys are central to the product strategy.

WalkiTalki should not pay for general user experimentation. Users should bring
their own OpenAI API key to run agents.

The product implication is important:

- WalkiTalki stores and shares agent specs.
- Users pay for their own AI compute.
- Shared agents never include the creator's API key.
- A recipient must connect their own key before running a shared agent.
- WalkiTalki should show enough usage visibility that users understand that
  their key is being used.

In the MVP, "bring your own key" should mean OpenAI API keys only. Do not support
generic provider keys, arbitrary external API credentials, OAuth integrations, or
third-party API marketplaces yet.

The MVP should not include user-account infrastructure. In MVP discussions,
"user" means the person operating the prototype, not a persisted platform object.

## Agent Sessions

An agent session is a temporary run of an agent spec for one user.

Session grants should be the main permission model. Instead of building a huge
permanent permission system, WalkiTalki should ask:

- Which agent is this user running?
- Which WalkiTalki resources does this session need?
- Which resources did the user grant for this session?
- What can the agent read?
- What can the agent write?

Examples:

- A photo-language session can use the user's OpenAI API key and image input.
- A future photo tutor session can read the user's flashcards and create new
  flashcards after that capability exists.
- A writing coach session can access a personal recall vector store.
- A shared tutor session can use the recipient's OpenAI API key, not the
  creator's key.

Session grants keep sharing understandable. The shared spec is reusable, but the
data access is personal to the current user's session.

## Sharing Model

Sharing is the platform's core unlock.

The user should be able to:

- Create an agent
- Publish the agent spec
- Copy a direct link to the agent spec
- Let the recipient run it with their own key and resources

Sharing should not include:

- Creator API keys
- Creator private memory
- Creator private documents
- Creator private flashcards
- Creator private vector stores

Future sharing modes may include:

- Friend sharing
- Classroom sharing
- Team sharing
- Public templates
- Forkable templates
- Curated marketplace
- Paid templates

Direct link sharing belongs in the MVP because it tests whether a created agent
is useful to someone besides its creator. Forking, public discovery, ratings,
profiles, and marketplace mechanics should wait.

## Data and Knowledge Model

WalkiTalki will likely use three kinds of data:

### Structured Product Data

This is canonical WalkiTalki data.

Examples:

- Agents
- Skill IDs
- Flashcards
- Uploaded documents
- Lesson results
- Stories
- Comments
- User progress

This data belongs in WalkiTalki's platform layer.

### Vector Search Data

This is retrieval-oriented data.

Examples:

- Chunks from uploaded documents
- Similar writing mistakes
- Prior lesson snippets
- Personal recall context

Vector data should support search and recall. It should not be treated as the
source of truth for important product objects.

### Lightweight Memory

This is user preference and personalization data.

Examples:

- "The user prefers short explanations."
- "The user is learning Korean."
- "The user struggles with formal speech."
- "The user likes examples before grammar explanations."

Memory should make agents feel personal without turning into an invisible
database.

## Trust and Safety

The platform has several trust problems that need to be designed early:

- Users need to know when their OpenAI API key is being used.
- Shared agents must not leak creator data.
- Forked agents must not inherit private credentials.
- Agents should ask before writing durable user data.
- Users should be able to inspect what an agent can access before running it.
- Users should be able to stop a session.
- Users should be able to revoke resource access.

Trust is more important than advanced capabilities. If users do not understand
what an agent can access, they will not share or run agents confidently.

## Platform Possibilities

The platform could eventually support many directions. These are possibilities,
not MVP commitments.

### Language Learning

- Photo vocabulary tutors
- Flashcard generators
- Writing coaches
- Reading companions
- Conversation simulators
- Grammar explainers
- Lesson planners
- Quiz creators

### Personal Productivity

- Personal knowledge assistants
- Document tutors
- Planning agents
- Research agents
- Study coaches

### Education and Classrooms

- Teacher-created agents
- Shared class document agents
- Student-specific practice agents
- Assignment feedback agents
- Classroom flashcard decks

### Community Templates

- Public agent gallery
- Forkable templates
- Ratings and reviews
- Creator profiles
- Verified agents
- Moderation workflows

### Advanced Integrations

- External API tools
- OAuth-connected services
- Approved workflow scripts
- Multi-agent handoffs
- Scheduled agents
- Voice agents
- Paid templates

These are later-stage platform expansions. They should not distract from the
first proof: users can build a constrained photo-language agent, publish it
privately, share it by link, run it on a picture, and chat about what the model
sees.

## What This Document Avoids

This document intentionally avoids:

- Database table definitions
- API endpoint specs
- JSON schemas
- Provider SDK details
- UI component specs
- Authentication implementation
- Vector store implementation
- OpenAPI ingestion details
- Deployment details

Those details should be written only after the MVP scope is locked.

## Follow-On Specs

The next specs should be narrow and technical:

1. Photo Lesson Product Spec
2. OpenAI BYOK Spec
3. Photo Language Agent Builder Spec
4. Direct Link Sharing Spec
5. Builder Capability Icon Spec
6. Photo Lesson Prompt Spec
7. Image Input Flow Spec
8. Lesson Chat Session Spec
9. Minimal Data Model Spec
10. MVP Screen Spec
11. MVP Test Plan

Each spec should be small enough to implement and test directly.
