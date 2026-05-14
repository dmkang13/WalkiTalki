# WalkiTalki Ideation

WalkiTalki is a language-learning app built around the user's real life: what
they see, hear, write, and talk about. The app should feel active, contextual,
and social, turning everyday moments into practice instead of relying only on
isolated drills.

## Table of Contents

- [Core Idea](#core-idea)
- [Feature Ideas](#feature-ideas)
  - [1. Photo-Based Language Lessons](#1-photo-based-language-lessons)
  - [2. Listening Companion Mode](#2-listening-companion-mode)
  - [3. Adaptive Difficulty and ELO System](#3-adaptive-difficulty-and-elo-system)
  - [4. Writing Practice and Story Sharing](#4-writing-practice-and-story-sharing)
  - [5. Conversation Practice Mode](#5-conversation-practice-mode)
  - [6. Narrative Thread Conversation Partner](#6-narrative-thread-conversation-partner)
  - [7. Ghost of Errors Past Grammar Shadowing](#7-ghost-of-errors-past-grammar-shadowing)
  - [8. Flashcards and Community Verification](#8-flashcards-and-community-verification)
  - [9. Social Layer](#9-social-layer)
- [Research Tasks](#research-tasks)
- [Open Questions](#open-questions)
- [Possible MVP](#possible-mvp)

## Core Idea

Users can start from a photo, a listening moment, a writing prompt, or a
simulated conversation. WalkiTalki turns that context into a lesson matched to
the user's current level.

Primary goal:
- Help users learn vocabulary and expression through real-world context.

Secondary goals:
- Make practice feel conversational and creative.
- Let users share, critique, and verify learning materials with friends.
- Adapt difficulty using learner-level signals.

## Feature Ideas

### 1. Photo-Based Language Lessons

Idea:
- The user takes a photo of what is in front of them, and the app turns the
  scene into a language lesson.

Flow:
- User opens the camera and takes a photo.
- App identifies visible objects, actions, and scene context.
- App generates vocabulary, phrases, and example sentences.

Related ideas:
- Practice speaking, writing, listening, or flashcards from the same scene.
- Start with manual photos, then later let the app suggest useful lesson
  moments.
- Tune explanations based on how much native-language support the user wants.

### 2. Listening Companion Mode

Idea:
- The app listens to a sermon, lecture, podcast, conversation, or video and
  helps the user understand words just above their level.

Flow:
- User starts listening mode.
- App transcribes or follows along with audio.
- App shows definitions, translations, examples, and optional flashcard saves.

Related ideas:
- Support real-time listening, recorded audio, or both.
- Show definitions during the session or as a recap afterward.
- Build clear privacy and microphone controls.

### 3. Adaptive Difficulty and ELO System

Idea:
- Use ELO-style scoring to match lessons, words, prompts, and conversations to
  the user's level.

Flow:
- Each user has a language-level score.
- Words, phrases, listening clips, and writing prompts have difficulty scores.
- Successful recall, correct usage, and comprehension raise the user's score.

Related ideas:
- Pick photo vocabulary that is challenging but not overwhelming.
- Adjust listening vocabulary, writing prompts, and conversation options.
- Track separate confidence by vocabulary, listening, speaking, writing, and
  grammar.

### 4. Writing Practice and Story Sharing

Idea:
- Users write stories, essays, or short responses using words they recently
  learned, then share them for feedback.

Flow:
- App selects recently learned words.
- User writes a story, essay, or short response.
- App gives feedback, then the user can share with friends for comments or
  critique.

Related ideas:
- Chat mode for essays and thought-provoking questions.
- Prompt-based and open-ended writing modes.
- Rubric-guided critique from AI, friends, or both.

### 5. Conversation Practice Mode

Idea:
- Users practice conversation by hearing or reading dialogue and choosing or
  speaking natural responses.

Flow:
- App plays or displays a conversation in the target language.
- User chooses from possible responses or gives an open-ended answer.
- App explains tone, meaning, cultural context, and more natural alternatives.

Related ideas:
- Multiple-choice reactions.
- Open-ended speaking responses.
- Roleplay conversations and listening comprehension quizzes.

### 6. Narrative Thread Conversation Partner

Idea:
- Maintain a persistent "Life Story" so conversation practice can refer back to
  real people, places, goals, and prior roleplays.

Flow:
- App remembers useful details from past sessions.
- New lessons reuse those details when relevant, such as mentioning Maria in
  Berlin during a travel lesson.
- Roleplays can continue over time, such as starting today at the airport after
  the user bought a ticket yesterday.

Related ideas:
- Use the Conversations API to pull context from previous thread_ids.
- Use a Knowledge Skill to update a USER_BIO.json file in a Vector Store after
  each session.
- Separate real-life memories from fictional roleplay state.

### 7. Ghost of Errors Past Grammar Shadowing

Idea:
- Preserve conversation flow by saving many corrections for later instead of
  interrupting every mistake live.

Flow:
- App tracks recurring error patterns over time.
- App notices context-specific struggles, such as a tense error that appears
  mostly when the user talks about work.
- App generates custom drills from the student's real mistakes.

Related ideas:
- Run a background Reflective Agent after each conversation to analyze logs.
- Update learning_profile.json in the student's small database.
- Track Fluency Peaks so the app can show the student how much they have
  improved.

### 8. Flashcards and Community Verification

Idea:
- Users generate flashcards from lessons and share decks so others can verify or
  improve them.

Flow:
- User saves words or phrases from lessons.
- App generates flashcards with definitions, translations, example sentences,
  and audio.
- Other users verify, correct, or suggest improvements.

Related ideas:
- Verification by friends, advanced learners, moderators, or AI.
- Flag incorrect cards and improve them collaboratively.
- Create decks from lessons, writing prompts, or listening mode.

### 9. Social Layer

Idea:
- Add a social layer for sharing writing, commenting on stories, critiquing
  submissions, and verifying flashcards.

Flow:
- User shares a story, essay, flashcard deck, lesson snapshot, or vocabulary
  list.
- Friends comment, suggest edits, critique, or verify learning materials.
- User applies feedback and keeps practicing from the improved material.

Related ideas:
- Stories, essays, flashcard decks, lesson snapshots, and vocabulary lists.
- Tier lists or sorting games.
- Friend-based, classroom-based, or public-community modes.

## Research Tasks

- Preply
- Babbel
- Speak.com
- Walking Charlie's app
- Qul AI - Arabic tutor app

## Open Questions

- What should the first version be: photo lessons, listening companion, writing
  practice, or conversation mode?
- Who is the initial user: casual learner, student, immigrant, traveler, sermon
  listener, or language hobbyist?
- What target language should be supported first?
- Is the core experience mobile-first?
- How social should the first version be?
- What user data is needed to personalize lessons safely?

## Possible MVP

The strongest first demo may be:

1. User takes a photo.
2. App identifies useful vocabulary and phrases.
3. App generates a short lesson matched to the user's level.
4. User saves selected words as flashcards.
5. User completes a short writing or speaking exercise using those words.

Why this MVP:
- It captures the unique WalkiTalki idea.
- It is concrete and demoable.
- It can later connect naturally to listening, writing, flashcards, ELO, and
  social sharing.
