import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  createAgent,
  getAgent,
  getAuthStatus,
  getSharedAgent,
  listAgents,
  publishAgent,
  resetSession,
  sendChatStream,
  startAuthLogin,
  startAgentSession,
  startSession,
  validateSkill,
} from './api';
import { Markdown } from './Markdown';
import type { AgentFormValues, AgentSummary, AuthStatus, ChatMessage, ProductAgent, SessionRead } from './types';

type RuntimeState = 'idle' | 'loading' | 'starting' | 'login_required' | 'ready' | 'sending' | 'error';
type Route =
  | { name: 'home' }
  | { name: 'build' }
  | { name: 'agents' }
  | { name: 'agent'; shareSlug: string }
  | { name: 'chat'; shareSlug: string }
  | { name: 'validation' };

function currentRoute(): Route {
  const path = window.location.pathname.replace(/\/+$/, '') || '/';
  const parts = path.split('/').filter(Boolean);
  if (path === '/') return { name: 'home' };
  if (path === '/build') return { name: 'build' };
  if (path === '/agents') return { name: 'agents' };
  if (path === '/validation') return { name: 'validation' };
  if (parts[0] === 'agents' && parts[1] && parts[2] === 'chat') return { name: 'chat', shareSlug: parts[1] };
  if (parts[0] === 'agents' && parts[1]) return { name: 'agent', shareSlug: parts[1] };
  return { name: 'home' };
}

export default function App() {
  const [route, setRoute] = useState<Route>(() => currentRoute());

  useEffect(() => {
    const onPop = () => setRoute(currentRoute());
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  function navigate(path: string) {
    window.history.pushState({}, '', path);
    setRoute(currentRoute());
  }

  return (
    <main className="app-shell">
      <nav className="top-nav">
        <button onClick={() => navigate('/')}>Home</button>
        <button onClick={() => navigate('/build')}>Build</button>
        <button onClick={() => navigate('/agents')}>Agents</button>
        <button onClick={() => navigate('/validation')}>Validation</button>
      </nav>

      {route.name === 'home' && <HomePage navigate={navigate} />}
      {route.name === 'build' && <BuildPage navigate={navigate} />}
      {route.name === 'agents' && <AgentsPage navigate={navigate} />}
      {route.name === 'agent' && <AgentLandingPage navigate={navigate} shareSlug={route.shareSlug} />}
      {route.name === 'chat' && <AgentChatPage shareSlug={route.shareSlug} />}
      {route.name === 'validation' && <ValidationPage />}
    </main>
  );
}

function HomePage({ navigate }: { navigate: (path: string) => void }) {
  return (
    <section className="hero compact-hero">
      <div>
        <p className="eyebrow">OpenClaw MVP</p>
        <h1>Build, publish, share, and chat with a text language agent.</h1>
        <p>
          This prototype uses OpenClaw provider login instead of pasted API keys. Published agents are in-memory for
          this pass, and chat is text-only.
        </p>
      </div>
      <div className="hero-actions">
        <button className="primary" onClick={() => navigate('/build')}>
          Create Agent
        </button>
        <button className="secondary" onClick={() => navigate('/agents')}>
          View Published Agents
        </button>
      </div>
    </section>
  );
}

function BuildPage({ navigate }: { navigate: (path: string) => void }) {
  const [values, setValues] = useState<AgentFormValues>({
    name: 'Photo Language Tutor',
    target_language: '',
    native_language: '',
    custom_instructions: '',
  });
  const [draft, setDraft] = useState<ProductAgent | null>(null);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const valid = values.name.trim() && values.target_language.trim();

  function update(field: keyof AgentFormValues, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
  }

  async function handlePublish(event: FormEvent) {
    event.preventDefault();
    if (!valid) return;
    setBusy(true);
    setError(null);
    try {
      const agent = draft ?? (await createAgent(values));
      setDraft(agent);
      const published = await publishAgent(agent.id);
      setShareUrl(published.share_url);
      navigate(`/agents/${published.share_slug}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not publish this agent.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="layout">
      <form className="panel form-panel" onSubmit={handlePublish}>
        <p className="eyebrow">Builder</p>
        <h1>Create a Text Language Agent</h1>
        {error && <div className="error-banner">{error}</div>}

        <label className="field">
          <span>Agent name</span>
          <input value={values.name} maxLength={80} onChange={(event) => update('name', event.target.value)} />
        </label>
        <label className="field">
          <span>Target language</span>
          <input
            value={values.target_language}
            maxLength={80}
            placeholder="Example: Spanish"
            onChange={(event) => update('target_language', event.target.value)}
          />
        </label>
        <label className="field">
          <span>Native language</span>
          <input
            value={values.native_language}
            maxLength={80}
            placeholder="Optional"
            onChange={(event) => update('native_language', event.target.value)}
          />
        </label>
        <label className="field">
          <span>Published custom instructions</span>
          <textarea
            value={values.custom_instructions}
            maxLength={1000}
            placeholder="Optional behavior for anyone who runs this agent."
            onChange={(event) => update('custom_instructions', event.target.value)}
          />
        </label>
        <button className="primary" type="submit" disabled={!valid || busy}>
          Publish Agent
        </button>
      </form>

      <aside className="panel preview-panel">
        <p className="eyebrow">Preview</p>
        <h2>{values.name || 'Untitled Agent'}</h2>
        <dl>
          <dt>Target</dt>
          <dd>{values.target_language || 'Required'}</dd>
          <dt>Native</dt>
          <dd>{values.native_language || 'Not specified'}</dd>
          <dt>Instructions</dt>
          <dd>{values.custom_instructions || 'No custom instructions.'}</dd>
        </dl>
        {shareUrl && <div className="skill-evidence">Published at {shareUrl}</div>}
      </aside>
    </section>
  );
}

function AgentsPage({ navigate }: { navigate: (path: string) => void }) {
  const [agents, setAgents] = useState<ProductAgent[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAgents()
      .then((result) => setAgents(result.agents))
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <section className="panel full-panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">Published Agents</p>
          <h1>In-memory published agents</h1>
        </div>
        <button className="primary" onClick={() => navigate('/build')}>
          Create Agent
        </button>
      </div>
      {error && <div className="error-banner">{error}</div>}
      {agents.length === 0 ? (
        <div className="empty-state">No agents have been published in this backend process.</div>
      ) : (
        <div className="agent-list">
          {agents.map((agent) => (
            <article className="agent-card" key={agent.id}>
              <h2>{agent.name}</h2>
              <p>{agent.description}</p>
              <button className="secondary" onClick={() => navigate(`/agents/${agent.share_slug}`)}>
                Open
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function AgentLandingPage({ navigate, shareSlug }: { navigate: (path: string) => void; shareSlug: string }) {
  const [agent, setAgent] = useState<ProductAgent | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSharedAgent(shareSlug)
      .then(setAgent)
      .catch((err: Error) => setError(err.message));
  }, [shareSlug]);

  function copyLink() {
    void navigator.clipboard.writeText(window.location.href).then(() => setCopied(true));
  }

  if (error) return <div className="error-banner">{error}</div>;
  if (!agent) return <div className="panel full-panel">Loading agent...</div>;

  return (
    <section className="panel full-panel">
      <p className="eyebrow">Shared Agent</p>
      <h1>{agent.name}</h1>
      <p className="lede">{agent.description}</p>
      <dl>
        <dt>Target</dt>
        <dd>{agent.target_language}</dd>
        <dt>Native</dt>
        <dd>{agent.native_language || 'Not specified'}</dd>
        <dt>Instructions</dt>
        <dd>{agent.custom_instructions || 'No custom instructions.'}</dd>
      </dl>
      <div className="notice">
        The share link includes the agent spec only. It does not include creator auth, chat history, or private runtime
        state.
      </div>
      <div className="button-row">
        <button className="primary" onClick={() => navigate(`/agents/${shareSlug}/chat`)}>
          Start Chat
        </button>
        <button className="secondary" onClick={copyLink}>
          {copied ? 'Copied' : 'Copy Share Link'}
        </button>
      </div>
    </section>
  );
}

function AgentChatPage({ shareSlug }: { shareSlug: string }) {
  const [agent, setAgent] = useState<ProductAgent | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [sessionInstructions, setSessionInstructions] = useState('');
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [session, setSession] = useState<SessionRead | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [runtimeState, setRuntimeState] = useState<RuntimeState>('idle');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSharedAgent(shareSlug)
      .then(setAgent)
      .catch((err: Error) => setError(err.message));
  }, [shareSlug]);

  useEffect(() => {
    getAuthStatus()
      .then(setAuthStatus)
      .catch((err: Error) => setError(err.message));
  }, []);

  const isAuthenticated = authStatus?.provider_status === 'connected';
  const canChat = session?.runtime_status === 'ready' && session.provider_status === 'connected';
  const statusLabel = session
    ? `${session.runtime_status} / ${session.provider_status}`
    : isAuthenticated
      ? 'OpenClaw authenticated'
      : 'ChatGPT login required';

  async function handleStartSession() {
    setRuntimeState('starting');
    setError(null);
    try {
      const next = await startAgentSession(shareSlug, sessionInstructions);
      setSession(next);
      setRuntimeState(next.provider_status === 'login_required' ? 'login_required' : 'ready');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start runtime session.');
      setRuntimeState('error');
    }
  }

  async function handleConfirmLogin() {
    setRuntimeState('starting');
    setError(null);
    try {
      const next = await getAuthStatus();
      setAuthStatus(next);
      setRuntimeState(next.provider_status === 'connected' ? 'idle' : 'login_required');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not confirm login.');
      setRuntimeState('error');
    }
  }

  async function handleProviderLogin() {
    setRuntimeState('starting');
    setError(null);
    try {
      const next = await startAuthLogin();
      setAuthStatus(next);
      setRuntimeState('login_required');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start provider login.');
      setRuntimeState('error');
    }
  }

  async function handleChatSubmit(event: FormEvent) {
    event.preventDefault();
    const message = chatInput.trim();
    if (!message || !canChat) return;
    setChatInput('');
    setError(null);
    setRuntimeState('sending');
    setMessages((current) => [...current, { role: 'user', content: message }, { role: 'assistant', content: '' }]);
    try {
      await sendChatStream(
        message,
        (text) => {
          setMessages((current) => {
            const next = [...current];
            const last = next[next.length - 1];
            if (last?.role !== 'assistant') return current;
            next[next.length - 1] = { ...last, content: last.content + text };
            return next;
          });
        },
        shareSlug,
      );
      setRuntimeState('ready');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not send chat message.');
      setRuntimeState('error');
    }
  }

  async function handleReset() {
    await resetSession();
    setSession(null);
    setMessages([]);
    setRuntimeState('idle');
  }

  return (
    <section className="chat-workspace">
      <div className="chat-title-row">
        <div>
          <p className="eyebrow">Text Chat</p>
          <h1>{agent?.name ?? 'Loading agent'}</h1>
        </div>
        <div className="runtime-pill">{statusLabel}</div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <details className="panel details-panel" open={detailsOpen} onToggle={(event) => setDetailsOpen(event.currentTarget.open)}>
        <summary>Agent details</summary>
        <dl>
          <dt>Target</dt>
          <dd>{agent?.target_language ?? '...'}</dd>
          <dt>Native</dt>
          <dd>{agent?.native_language || 'Not specified'}</dd>
          <dt>Published instructions</dt>
          <dd>{agent?.custom_instructions || 'No custom instructions.'}</dd>
        </dl>
      </details>

      {!isAuthenticated && (
        <section className="panel runtime-start">
          <div className="notice">Sign in to ChatGPT through OpenClaw before starting this agent chat.</div>
          <div className="button-row">
            <button className="primary" onClick={handleProviderLogin} disabled={runtimeState === 'starting'}>
              Open ChatGPT Login
            </button>
            <button className="secondary" onClick={handleConfirmLogin} disabled={runtimeState === 'starting'}>
              I Completed Login
            </button>
          </div>
          {authStatus?.login_url && (
            <a className="secondary link-button" href={authStatus.login_url} target="_blank" rel="noreferrer">
              Continue OAuth
            </a>
          )}
        </section>
      )}

      {isAuthenticated && !session && (
        <section className="panel runtime-start">
          <label className="field">
            <span>Session-only custom instructions</span>
            <textarea
              value={sessionInstructions}
              maxLength={2000}
              placeholder="Optional instructions for only this runtime session."
              onChange={(event) => setSessionInstructions(event.target.value)}
            />
          </label>
          <button className="primary" onClick={handleStartSession} disabled={runtimeState === 'starting'}>
            Start OpenClaw Session
          </button>
        </section>
      )}

      <section className="panel chat-panel product-chat-panel">
        <div className="messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              {isAuthenticated ? 'Start the OpenClaw session, then ask the agent a text question.' : 'Log in first to unlock agent chat.'}
            </div>
          ) : (
            messages.map((message, index) => (
              <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
                <span>{message.role}</span>
                <Markdown text={message.content || '...'} />
              </article>
            ))
          )}
        </div>

        <form className="composer" onSubmit={handleChatSubmit}>
          <input
            value={chatInput}
            maxLength={1000}
            onChange={(event) => setChatInput(event.target.value)}
            disabled={!canChat || runtimeState === 'sending'}
            placeholder="Ask a follow-up question..."
          />
          <button type="submit" disabled={!canChat || !chatInput.trim() || runtimeState === 'sending'}>
            Send
          </button>
          <button type="button" className="ghost" onClick={handleReset}>
            Start Over
          </button>
        </form>
      </section>
    </section>
  );
}

function ValidationPage() {
  const [agent, setAgent] = useState<AgentSummary | null>(null);
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [session, setSession] = useState<SessionRead | null>(null);
  const [runtimeState, setRuntimeState] = useState<RuntimeState>('loading');
  const [customInstructions, setCustomInstructions] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
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

  useEffect(() => {
    getAuthStatus()
      .then(setAuthStatus)
      .catch((err: Error) => setError(err.message));
  }, []);

  const isAuthenticated = authStatus?.provider_status === 'connected';
  const canUseRuntime = session?.runtime_status === 'ready' && session.provider_status === 'connected';
  const customInstructionsLocked = Boolean(session);

  const statusLabel = useMemo(() => {
    if (!session) return isAuthenticated ? 'OpenClaw authenticated' : 'ChatGPT login required';
    return `${session.runtime_status} / ${session.provider_status}`;
  }, [isAuthenticated, session]);

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
      const next = await getAuthStatus();
      setAuthStatus(next);
      setRuntimeState(next.provider_status === 'connected' ? 'idle' : 'login_required');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not confirm login.');
      setRuntimeState('error');
    }
  }

  async function handleProviderLogin() {
    setError(null);
    setRuntimeState('starting');
    try {
      const next = await startAuthLogin();
      setAuthStatus(next);
      setRuntimeState('login_required');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start provider login.');
      setRuntimeState('error');
    }
  }

  async function handleChatSubmit(event: FormEvent) {
    event.preventDefault();
    const message = chatInput.trim();
    if (!message || !canUseRuntime) return;
    setChatInput('');
    setError(null);
    setRuntimeState('sending');
    setMessages((current) => [...current, { role: 'user', content: message }, { role: 'assistant', content: '' }]);
    try {
      await sendChatStream(message, (text) => {
        setMessages((current) => {
          const next = [...current];
          const last = next[next.length - 1];
          if (last?.role !== 'assistant') return current;
          next[next.length - 1] = { ...last, content: last.content + text };
          return next;
        });
      });
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
    setSkillEvidence(null);
    setRuntimeState('idle');
  }

  return (
    <>
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
          <label className="field">
            <span>Session-only custom instructions</span>
            <textarea
              value={customInstructions}
              onChange={(event) => setCustomInstructions(event.target.value)}
              disabled={customInstructionsLocked}
              placeholder="Example: Make the lesson suitable for a beginner."
            />
          </label>
          {!isAuthenticated && (
            <>
              <div className="notice">Sign in to ChatGPT through OpenClaw before starting chat.</div>
              <button className="primary" onClick={handleProviderLogin} disabled={runtimeState === 'starting'}>
                Open ChatGPT Login
              </button>
              {authStatus?.login_url && (
                <a className="secondary link-button" href={authStatus.login_url} target="_blank" rel="noreferrer">
                  Continue OAuth
                </a>
              )}
              <button className="secondary" onClick={handleConfirmLogin} disabled={runtimeState === 'starting'}>
                I completed login
              </button>
            </>
          )}
          {isAuthenticated && !session && (
            <button className="primary" onClick={handleStartSession} disabled={runtimeState === 'starting'}>
              Start Chat
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
              <p>Text-only OpenClaw runtime validation.</p>
            </div>
            <button onClick={handleSkillValidation} disabled={!canUseRuntime || runtimeState === 'sending'}>
              Validate Skill
            </button>
          </div>
          {skillEvidence && <div className="skill-evidence">{skillEvidence}</div>}
          <div className="messages">
            {messages.length === 0 && (
              <div className="empty-state">
                {isAuthenticated ? 'Start a session, then send text.' : 'Log in first to unlock chat.'}
              </div>
            )}
            {messages.map((message, index) => (
              <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
                <span>{message.role}</span>
                <Markdown text={message.content || '...'} />
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
    </>
  );
}
