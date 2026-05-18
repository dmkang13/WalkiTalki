import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  confirmLogin,
  getAgent,
  resetSession,
  sendChat,
  sendImageLesson,
  startSession,
  validateSkill,
} from './api';
import { Markdown } from './Markdown';
import type { AgentSummary, ChatMessage, SessionRead } from './types';

type RuntimeState =
  | 'idle'
  | 'loading'
  | 'starting'
  | 'login_required'
  | 'ready'
  | 'sending'
  | 'error';

export default function App() {
  const [agent, setAgent] = useState<AgentSummary | null>(null);
  const [session, setSession] = useState<SessionRead | null>(null);
  const [runtimeState, setRuntimeState] = useState<RuntimeState>('loading');
  const [customInstructions, setCustomInstructions] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [skillEvidence, setSkillEvidence] = useState<string | null>(null);

  useEffect(() => {
    getAgent()
      .then((agentSummary) => {
        setAgent(agentSummary);
        setRuntimeState('idle');
      })
      .catch((err: Error) => {
        setError(err.message);
        setRuntimeState('error');
      });
  }, []);

  const canUseRuntime = session?.runtime_status === 'ready' && session.provider_status === 'connected';
  const customInstructionsLocked = Boolean(session);

  const statusLabel = useMemo(() => {
    if (!session) return 'No runtime session';
    return `${session.runtime_status} / ${session.provider_status}`;
  }, [session]);

  async function handleStartSession() {
    setError(null);
    setRuntimeState('starting');
    try {
      const next = await startSession(customInstructions);
      setSession(next);
      setRuntimeState(next.provider_status === 'login_required' ? 'login_required' : 'ready');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start session.');
      setRuntimeState('error');
    }
  }

  async function handleConfirmLogin() {
    setError(null);
    setRuntimeState('starting');
    try {
      const next = await confirmLogin();
      setSession(next);
      setRuntimeState('ready');
      setMessages((current) => [
        ...current,
        {
          role: 'system',
          content: 'ChatGPT/provider login confirmed. The OpenClaw runtime session is ready.',
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not confirm login.');
      setRuntimeState('error');
    }
  }

  async function handleImageLesson() {
    if (!image) return;
    setError(null);
    setRuntimeState('sending');
    setMessages((current) => [...current, { role: 'user', content: `Uploaded ${image.name}` }]);
    try {
      const result = await sendImageLesson(image);
      setMessages((current) => [...current, { role: 'assistant', content: result.message }]);
      setRuntimeState('ready');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not send image.');
      setRuntimeState('error');
    }
  }

  async function handleChatSubmit(event: FormEvent) {
    event.preventDefault();
    const message = chatInput.trim();
    if (!message) return;
    setChatInput('');
    setError(null);
    setRuntimeState('sending');
    setMessages((current) => [...current, { role: 'user', content: message }]);
    try {
      const result = await sendChat(message);
      setMessages((current) => [...current, { role: 'assistant', content: result.message }]);
      setRuntimeState('ready');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not send chat message.');
      setRuntimeState('error');
    }
  }

  async function handleSkillValidation() {
    setError(null);
    setRuntimeState('sending');
    try {
      const result = await validateSkill();
      setSkillEvidence(result.evidence);
      setMessages((current) => [...current, { role: 'assistant', content: result.message }]);
      setSession((current) => current && { ...current, skill_status: result.skill_status });
      setRuntimeState('ready');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not validate skill.');
      setRuntimeState('error');
    }
  }

  async function handleReset() {
    await resetSession();
    setSession(null);
    setMessages([]);
    setImage(null);
    setSkillEvidence(null);
    setRuntimeState('idle');
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">OpenClaw Runtime Validation</p>
          <h1>{agent?.name ?? 'Loading Photo Language Tutor'}</h1>
          <p>{agent?.description ?? 'Loading the prebuilt backend agent.'}</p>
        </div>
        <div className="status-card">
          <span>Runtime</span>
          <strong>{statusLabel}</strong>
          <small>{session?.model ? `${session.provider} · ${session.model}` : 'Awaiting provider login'}</small>
        </div>
      </section>

      {error && <div className="error-banner">{error}</div>}

      <section className="layout">
        <aside className="panel agent-panel">
          <h2>Prebuilt Agent</h2>
          <dl>
            <dt>Target</dt>
            <dd>{agent?.target_language ?? '...'}</dd>
            <dt>Native</dt>
            <dd>{agent?.native_language ?? 'None'}</dd>
            <dt>Skill</dt>
            <dd>{agent?.validation_skill_name ?? '...'}</dd>
          </dl>

          <div className="capabilities">
            {agent?.required_capabilities.map((capability) => (
              <span key={capability}>{capability.split('_').join(' ')}</span>
            ))}
          </div>

          <label className="field">
            <span>Session-only custom instructions</span>
            <textarea
              value={customInstructions}
              onChange={(event) => setCustomInstructions(event.target.value)}
              disabled={customInstructionsLocked}
              placeholder="Example: Make the lesson suitable for a beginner."
            />
          </label>

          <button className="primary" onClick={handleStartSession} disabled={runtimeState === 'starting'}>
            Start Chat
          </button>
          {session?.login_url && (
            <a className="secondary link-button" href={session.login_url} target="_blank" rel="noreferrer">
              Open ChatGPT Login
            </a>
          )}
          {runtimeState === 'login_required' && (
            <button className="secondary" onClick={handleConfirmLogin}>
              I completed login
            </button>
          )}
          <button className="ghost" onClick={handleReset}>
            Reset Session
          </button>
        </aside>

        <section className="panel chat-panel">
          <div className="chat-header">
            <div>
              <h2>Chat</h2>
              <p>Upload a photo, then ask follow-up questions in the same runtime session.</p>
            </div>
            <button onClick={handleSkillValidation} disabled={!canUseRuntime || runtimeState === 'sending'}>
              Validate Skill
            </button>
          </div>

          {skillEvidence && <div className="skill-evidence">{skillEvidence}</div>}

          <div className="upload-row">
            <input
              type="file"
              accept="image/*"
              onChange={(event) => setImage(event.target.files?.[0] ?? null)}
              disabled={!canUseRuntime}
            />
            <button onClick={handleImageLesson} disabled={!canUseRuntime || !image || runtimeState === 'sending'}>
              Send Image
            </button>
          </div>

          <div className="messages">
            {messages.length === 0 && (
              <div className="empty-state">
                Start a session, confirm provider login, and upload a photo to generate the first lesson.
              </div>
            )}
            {messages.map((message, index) => (
              <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
                <span>{message.role}</span>
                <Markdown text={message.content} />
              </article>
            ))}
          </div>

          <form className="composer" onSubmit={handleChatSubmit}>
            <input
              value={chatInput}
              onChange={(event) => setChatInput(event.target.value)}
              disabled={!canUseRuntime || runtimeState === 'sending'}
              placeholder="Ask a follow-up question..."
            />
            <button type="submit" disabled={!canUseRuntime || !chatInput.trim()}>
              Send
            </button>
          </form>
        </section>
      </section>
    </main>
  );
}
