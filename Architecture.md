# WalkiTalki Agent Infrastructure Architecture

## Goal

Create a React app where users can assemble, edit, access, and share agents.
An agent is a connector to an LLM plus a configurable set of tools, skills,
permissions, memory, data access, API actions, and scripts.

The first design target is not maximum agent power. It is a clear building
experience where users understand what an agent can do, why it can do it, and
how to safely share or remix it.


## Core Concepts

### Agent

An agent is a saved configuration that includes:

- LLM provider and model settings
- System instructions and behavior style
- Skills
- Tool permissions
- OpenAPI-backed API tools
- Memory configuration
- Database access configuration
- Script or workflow access
- Runtime permissions such as camera or microphone
- Sharing permissions
- Version history

### Agent Tool

An agent tool is a building block the user can add, remove, configure, test,
and share. Tools should be interchangeable, but each tool needs its own edit
panel because camera access, memory, database access, and API access all have
different risks and configuration needs.

### Skill

A skill is a reusable capability package. It may contain instructions,
examples, schemas, UI hints, tool requirements, evaluation rules, or scripts.
The WalkiTalki database should store skill ids so agents can reference skills
without duplicating the full skill definition each time.

### OpenAPI Tool

An OpenAPI tool is created by importing or linking an OpenAPI spec. The backend
validates the spec, extracts supported operations, stores operation metadata,
and exposes selected operations to the agent as callable tools. API credentials
must stay server-side.


## React App UX

### Primary Views

- Agent Library: list of the user's agents, shared agents, drafts, favorites,
  and recently used agents.
- Agent Builder: main workspace for assembling an agent from blocks.
- Agent Detail: public or private profile page for one agent.
- Agent Runner: chat, voice, camera, or task interface for using an agent.
- Shared Agent Gallery: browsable list of community or team agents.
- Version History: compare, restore, fork, or publish prior agent versions.

### Agent Builder Layout

The builder should have four major areas:

- Block Tray: available tools, skills, models, memories, APIs, and data sources.
- Agent Canvas: current agent assembled as editable blocks.
- Inspector Panel: settings for the selected block.
- Test Console: quick place to run the agent and see what tools it tries to use.

The canvas should feel more like putting together a kit than writing code.
Each block needs a plain-language summary of what it allows the agent to do.

### Builder Flow

1. User creates a new agent from blank state or template.
2. User chooses a model and gives the agent a name.
3. User adds skills and tools from the block tray.
4. User configures each block in the inspector panel.
5. User tests the agent in the test console.
6. User saves a draft, publishes privately, or shares.

### Access and Sharing UI

Agents should be accessible from cards in the library. Each card should show:

- Agent name
- Short description
- Tool icons
- Visibility state
- Last edited date
- Run button
- Share button
- More menu for duplicate, fork, archive, or version history

Sharing should support:

- Private
- Shared by link
- Shared with specific users
- Shared with a group or classroom
- Published to gallery
- Forkable template

When sharing an agent, the UI must clearly separate:

- Agent definition: safe to share
- User credentials: never shared
- Private memory: not shared by default
- User data sources: not shared unless explicitly allowed
- Scripts and API actions: shared only as references plus required permissions


## Agent Tool Blocks and UX Ideas

### 1. LLM Connector

What it does:
- Chooses the model provider, model, temperature, response style, and token
  limits.

Builder UX:
- Model picker with recommended defaults.
- Simple mode for basic users.
- Advanced mode for temperature, max output, and reasoning controls.

Runner UI:
- Shows which model powers the agent.
- Optionally lets the user switch between fast, balanced, and careful modes.

### 2. Instructions

What it does:
- Defines the agent's role, tone, goals, boundaries, and default behavior.

Builder UX:
- Guided form with fields for purpose, audience, tone, and constraints.
- Prompt preview for advanced users.
- Template starters such as tutor, coach, researcher, planner, and reviewer.

Runner UI:
- Agent profile summary explains what the agent is meant to do.

### 3. Skills

What it does:
- Adds reusable capability packages by skill id.

Builder UX:
- Skill marketplace or library.
- Skill cards with category, required tools, author, rating, and compatibility.
- Drag skills into the agent canvas.
- Inspector lets users enable, disable, reorder, or configure skill preferences.

Runner UI:
- Skill badges show what capabilities are active.
- Agent can cite which skill it used when useful.

Backend note:
- Store skill ids on the agent version.
- Resolve skill details at runtime from the skill registry.

### 4. Camera Access

What it does:
- Allows an agent to request or process images from the user's camera.

Builder UX:
- Camera permission block with allowed modes:
  - Manual photo only
  - Upload image
  - Live camera preview
  - Periodic capture, if later supported
- Inspector explains when the agent may use the camera.

Runner UI:
- Clear camera button.
- Preview before sending image to the agent.
- Per-use permission confirmation.

WalkiTalki use:
- Photo-based language lessons from real-world objects and scenes.

### 5. Microphone and Audio Access

What it does:
- Allows recording, transcription, pronunciation checks, or live listening.

Builder UX:
- Audio block with mode choices:
  - Record and submit
  - Live transcription
  - Pronunciation practice
  - Listening companion

Runner UI:
- Push-to-talk or start listening button.
- Visible recording state.
- Transcript review before saving or sharing.

WalkiTalki use:
- Sermon, podcast, lecture, or conversation vocabulary help.

### 6. Memory

What it does:
- Lets an agent remember user preferences, past sessions, learned words, goals,
  mistakes, and progress.

Builder UX:
- Memory block with toggles:
  - Remember preferences
  - Remember vocabulary
  - Remember writing feedback
  - Remember conversation history
  - Remember learning level
- Inspector shows memory scope and retention rules.

Runner UI:
- "What this agent remembers" panel.
- Delete or edit memory entries.
- Temporary session mode.

Backend note:
- Separate private user memory from shared agent definition.
- Agent sharing should not copy personal memory unless the user exports it.

### 7. Database Access

What it does:
- Allows an agent to read or write approved WalkiTalki data.

Builder UX:
- Database block with selectable tables or resource types.
- Plain-language permissions:
  - Read vocabulary
  - Create flashcards
  - Read lesson progress
  - Write lesson results
  - Read shared stories
  - Comment on shared work

Runner UI:
- Agent activity log shows when data is read or written.
- Confirmation for destructive or public writes.

Backend note:
- Do not expose direct database credentials to agents or browsers.
- Use scoped server endpoints and policy checks.

### 8. OpenAPI API Tools

What it does:
- Turns external API operations into agent-callable tools.

Builder UX:
- Import OpenAPI spec by URL or file upload.
- Validate the spec and show detected operations.
- User selects which operations the agent can use.
- Inspector allows operation naming, descriptions, parameter defaults, and auth
  connection selection.
- Test call panel for each selected operation.

Runner UI:
- Tool-use timeline shows API calls before and after execution.
- Sensitive calls require confirmation.
- Failed API calls should show a readable reason and retry option.

Backend note:
- Store the original OpenAPI spec plus a normalized operation registry.
- Resolve auth and execute API calls on the backend.
- Use operation ids, HTTP methods, paths, parameters, request schemas, response
  schemas, and security schemes from the spec.
- Validate inputs against the OpenAPI schema before execution.
- Return structured results to the LLM rather than raw unbounded responses.

### 9. User API Key and Token Connections

What it does:
- Lets users connect their own API keys, bearer tokens, or provider credentials
  so agents can use the user's quota, account, and permissions.

Builder UX:
- Credential block or connection step attached to OpenAPI tools and LLM
  providers.
- User can paste an API key, upload a token file if the provider requires it,
  or complete an OAuth-style connection flow.
- UI shows the credential label, provider, allowed scopes, last used date, and
  whether the key is active.
- After saving, the secret is never shown again. The user can only rename,
  rotate, test, disable, or delete it.
- Builder should clearly mark tools that require the user to bring their own
  key before the agent can run.

Runner UI:
- If a shared agent requires a key, prompt the current user to connect their own
  credential before running that tool.
- Show which connected account or token will be charged before high-cost calls.
- Let users set per-agent usage limits where possible, such as daily call caps
  or maximum spend warnings.

Sharing behavior:
- A creator's API keys are never shared with other users.
- Shared agents should include a list of required credential types, not the
  actual credentials.
- Forked agents inherit credential requirements but not credential values.
- Each user decides which of their own saved keys can be used by the agent.

Backend note:
- Store encrypted credentials in a secrets store or encrypted credential table.
- Store only a reference to the secret on agent connections.
- Track key owner, provider, scopes, status, and last-used metadata.
- Do not pass raw keys to the LLM or React client.
- All API calls using user keys must execute server-side through the tool
  runtime.

### 10. Scripts

What it does:
- Allows agents to run approved scripts or workflows.

Builder UX:
- Script block with approved script library.
- Show inputs, outputs, required permissions, and last updated date.
- No arbitrary user code in the MVP.

Runner UI:
- Confirmation before running scripts with side effects.
- Display script output in a readable panel.

Backend note:
- Scripts should run in a sandboxed job environment.
- Store script ids and version ids on agent versions.

### 11. Knowledge Sources

What it does:
- Gives the agent access to documents, vocabulary lists, lesson content,
  imported notes, or other retrieval sources.

Builder UX:
- Knowledge block for uploading files or selecting existing collections.
- Indexing status and source preview.
- Scope selector for private, shared, or public sources.

Runner UI:
- Source citations when the agent answers from knowledge.
- Source viewer for inspecting retrieved material.

### 12. Database Schemas

What it does:
- Defines structured data the agent can create, update, or query.

Builder UX:
- Schema block with visual schema editor.
- Templates for flashcards, lessons, stories, comments, vocabulary items, and
  user progress.
- Field-level permission controls.

Runner UI:
- Generated records appear as structured cards, not just chat text.
- User can approve records before saving.

Backend note:
- Store schema ids and version ids.
- Validate generated records against schemas before writes.

### 13. Sharing and Permission Policy

What it does:
- Controls who can view, use, fork, edit, or publish an agent.

Builder UX:
- Share block or publish panel.
- Permission presets:
  - Private draft
  - Personal agent
  - Friend shared
  - Classroom shared
  - Public template

Runner UI:
- Clear indicator when using someone else's agent.
- Fork button creates a personal copy without copying private credentials.

### 14. Evaluation and Safety Rules

What it does:
- Adds tests, guardrails, and expected behavior checks.

Builder UX:
- Evaluation block with sample tasks and expected outcomes.
- Tool permission checks.
- "Run test suite" button before publishing.

Runner UI:
- Lightweight warning when the agent cannot perform a requested action because
  a permission or tool is missing.


## Backend Architecture

### Main Backend Responsibilities

- Store users, agents, skills, tool definitions, and sharing permissions.
- Validate and store OpenAPI specs.
- Convert selected OpenAPI operations into callable agent tools.
- Store agent versions so shared agents are stable.
- Execute tools through server-side permission checks.
- Store encrypted references to user API keys and provider tokens.
- Keep credentials, private memory, and database access off the client.
- Log agent runs, tool calls, approvals, and errors.

### Suggested Services

- React client: builder, gallery, runner, and sharing UI.
- App API: authentication, agent CRUD, sharing, comments, gallery, credential
  connections, and runs.
- Agent runtime service: prepares model calls and executes approved tools.
- Tool registry service: skills, scripts, OpenAPI operations, and database tools.
- OpenAPI ingestion service: validates specs and creates normalized tool records.
- Credential service: encrypts, stores, rotates, disables, and audits user API
  keys and provider tokens.
- Memory service: private user memory and agent-scoped memory.
- Job service: sandboxed scripts, long-running imports, and evaluations.


## Database Design

### Core Tables

`users`
- id
- display_name
- email
- created_at

`agents`
- id
- owner_user_id
- current_version_id
- name
- slug
- summary
- visibility
- created_at
- updated_at

`agent_versions`
- id
- agent_id
- version_number
- model_config_json
- instructions
- tool_config_json
- created_by_user_id
- created_at
- publish_state

`skills`
- id
- name
- description
- category
- definition_json
- required_tool_types_json
- author_user_id
- visibility
- created_at

`agent_skills`
- id
- agent_version_id
- skill_id
- config_json
- position
- enabled

`tool_definitions`
- id
- tool_type
- name
- description
- definition_json
- created_by_user_id
- visibility

`agent_tools`
- id
- agent_version_id
- tool_definition_id
- config_json
- permissions_json
- enabled

### OpenAPI Tables

`openapi_specs`
- id
- owner_user_id
- name
- source_type
- source_url
- raw_spec_json
- parsed_spec_json
- validation_status
- validation_errors_json
- created_at
- updated_at

`openapi_operations`
- id
- openapi_spec_id
- operation_id
- method
- path
- summary
- description
- parameters_schema_json
- request_body_schema_json
- response_schema_json
- security_requirements_json
- normalized_tool_name

`api_connections`
- id
- owner_user_id
- openapi_spec_id
- auth_type
- provider_name
- credential_kind
- key_label
- secret_last_four
- encrypted_credentials_ref
- scopes_json
- status
- display_name
- last_used_at
- created_at
- updated_at

`credential_grants`
- id
- owner_user_id
- agent_id
- api_connection_id
- allowed_tool_types_json
- allowed_operation_ids_json
- usage_limits_json
- status
- created_at
- updated_at

`agent_api_operations`
- id
- agent_version_id
- openapi_operation_id
- api_connection_id
- alias
- enabled
- requires_confirmation
- parameter_defaults_json

### Memory and Data Access Tables

`memories`
- id
- user_id
- agent_id
- memory_type
- content_json
- visibility
- created_at
- updated_at

`db_schemas`
- id
- owner_user_id
- name
- schema_json
- version
- visibility

`agent_db_permissions`
- id
- agent_version_id
- resource_type
- action
- scope
- policy_json

### Sharing Tables

`agent_shares`
- id
- agent_id
- shared_with_user_id
- shared_with_group_id
- permission
- created_by_user_id
- created_at

`agent_forks`
- id
- source_agent_id
- source_version_id
- forked_agent_id
- forked_by_user_id
- created_at

### Runtime Tables

`agent_runs`
- id
- agent_id
- agent_version_id
- user_id
- status
- started_at
- completed_at

`tool_calls`
- id
- agent_run_id
- tool_type
- tool_name
- request_json
- response_json
- status
- requires_confirmation
- confirmed_by_user_id
- created_at

`audit_logs`
- id
- actor_user_id
- action
- resource_type
- resource_id
- metadata_json
- created_at


## OpenAPI Handling

The OpenAPI flow should be explicit and permissioned:

1. User imports a spec by URL or upload.
2. Backend validates that it is a supported OpenAPI version.
3. Backend parses paths, operations, schemas, parameters, request bodies,
   response bodies, and security schemes.
4. Backend creates an operation list for the builder UI.
5. User selects allowed operations.
6. User connects auth credentials through a server-side connection flow or
   chooses one of their saved API key connections.
7. Agent version stores references to selected operation ids.
8. At runtime, the agent proposes an operation call.
9. Backend validates arguments against the operation schema.
10. Backend checks agent permissions, user permissions, and confirmation rules.
11. Backend executes the HTTP request server-side.
12. Backend normalizes the response and sends structured results back to the
    agent.

Important constraints:

- Never send API keys to the React client.
- Never let the LLM call arbitrary URLs from a spec.
- Only selected operations become tools.
- Require confirmation for writes, purchases, messages, deletes, or public posts.
- Keep raw API responses size-limited and schema-shaped before returning them to
  the LLM.
- Shared agents must ask each user to connect their own key when an operation
  requires user-owned credentials.


## User API Key Handling

Users should be able to bring their own API keys and tokens, but the system
should treat those credentials as private user-owned resources.

Credential setup flow:

1. User opens a credential connection screen from the agent builder, account
   settings, or an API tool block.
2. User chooses a provider or imported OpenAPI spec.
3. User selects the auth type: API key, bearer token, basic auth, OAuth, or
   custom header if supported by the spec.
4. User pastes the key, uploads the provider token file, or completes the
   provider auth flow.
5. Backend validates the credential with a safe test request when possible.
6. Backend stores the secret encrypted and returns only non-secret metadata to
   the client.
7. User grants a specific agent permission to use that credential.
8. Runtime uses the credential only for approved tools and approved operations.

Credential metadata shown in UI:

- Provider name
- Credential label
- Credential type
- Last four characters, when safe
- Connected user or account, when available
- Scopes or permissions
- Last used date
- Status: active, disabled, expired, revoked, or needs attention

Credential controls:

- Test connection
- Rename
- Rotate key
- Disable
- Delete
- View usage history
- Set per-agent usage limits
- Revoke an agent's access

Runtime rules:

- Never put raw keys in prompts, tool descriptions, logs, or client responses.
- Never copy keys when sharing or forking an agent.
- Use the running user's key, not the agent creator's key, unless the creator is
  the current user and has granted that agent access.
- Confirm before using a key for high-cost, write, publish, purchase, message,
  or delete operations.
- Log which credential reference was used, but not the credential value.
- Allow users to revoke a credential globally or revoke one agent's grant.


## Agent Runtime Flow

1. User opens an agent.
2. Backend loads the current agent version.
3. Backend resolves skills, tool definitions, memory scope, database
   permissions, and API operations.
4. Runtime constructs the LLM request with the agent instructions and available
   tools.
5. User sends text, image, audio, or another input.
6. LLM responds directly or requests a tool call.
7. Backend validates and executes the tool call.
8. Backend logs the tool call.
9. LLM receives tool result and produces the final response.
10. Runtime optionally writes memory or database records after policy checks.


## MVP Scope

The first version should support:

- Agent library
- Agent builder with block tray, canvas, inspector, and test console
- LLM connector block
- Instructions block
- Skills block using stored skill ids
- Camera block for photo-based lessons
- Memory block for vocabulary and preferences
- Basic database permission block for flashcards and lesson progress
- OpenAPI import with operation selection
- User API key connection and encrypted credential storage
- Private agents and link sharing
- Forking shared agents
- Agent runner with chat and image input

Defer until later:

- Public marketplace ranking
- Arbitrary user scripts
- Live microphone streaming
- Complex group administration
- Paid agent publishing
- Fully visual schema designer


## Design Principles

- Blocks should be understandable before they are powerful.
- Every permission should have a visible reason.
- Sharing should copy agent structure, not private data.
- OpenAPI tools should be selected operation-by-operation.
- Credentials should stay server-side.
- User-owned API keys should power shared agents without exposing or copying the
  keys.
- Users should be able to test an agent while building it.
- Agent versions should make sharing and forking stable.
- The UI should show what an agent can do at a glance.


## Open Questions

- Should WalkiTalki agents be mostly personal tools, shared classroom tools, or
  public community templates?
- Should skills be created only by WalkiTalki at first, or can users create
  skills in the MVP?
- Should agent blocks be arranged as a canvas, a vertical checklist, or both?
- How much of the agent's prompt should be visible to non-technical users?
- Should shared agents show their full configuration before a user runs them?
- Should API-connected agents require publisher review before public sharing?
