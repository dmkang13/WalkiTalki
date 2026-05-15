import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowPathIcon, ChevronDownIcon, PaperAirplaneIcon } from "@heroicons/react/24/outline";
import { api } from "../api/client";
import ApiKeyConnect from "../components/ApiKeyConnect";
import ImageCapture from "../components/ImageCapture";
import Layout from "../components/Layout";
import MarkdownLesson from "../components/MarkdownLesson";
import { useApiKeySession } from "../hooks/useApiKeySession";
import type { ChatMessage, LessonSession, PublishedAgent, Usage } from "../types";
import { validateChatDraft } from "../validation";
import styles from "./ChatPage.module.css";

export default function ChatPage() {
  const { shareSlug = "" } = useParams();
  const { hasApiKey, isChecking } = useApiKeySession();
  const [agent, setAgent] = useState<PublishedAgent | null>(null);
  const [agentError, setAgentError] = useState("");
  const [lesson, setLesson] = useState<LessonSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [usage, setUsage] = useState<Usage | undefined>();
  const [lessonError, setLessonError] = useState("");
  const [draft, setDraft] = useState("");
  const [chatError, setChatError] = useState("");
  const [failedPrompt, setFailedPrompt] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isMetadataOpen, setIsMetadataOpen] = useState(false);
  const chatValidation = useMemo(() => validateChatDraft(draft), [draft]);

  useEffect(() => {
    let alive = true;
    api
      .getSharedAgent(shareSlug)
      .then((nextAgent) => {
        if (alive) setAgent(nextAgent);
      })
      .catch((caught) => {
        if (alive) setAgentError(caught instanceof Error ? caught.message : "Could not load shared agent.");
      });
    return () => {
      alive = false;
    };
  }, [shareSlug]);

  async function handleImageReady(image: File | Blob) {
    setLessonError("");
    try {
      const nextLesson = await api.createLessonSession(shareSlug, image);
      setLesson(nextLesson);
      setMessages(nextLesson.messages);
      setUsage(nextLesson.usage);
    } catch (caught) {
      setLessonError(caught instanceof Error ? caught.message : "Could not generate the lesson.");
    }
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    if (!lesson || chatValidation) return;
    const content = draft.trim();
    const userMessage: ChatMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content,
      createdAt: new Date().toISOString()
    };
    setMessages((current) => [...current, userMessage]);
    setDraft("");
    await sendPrompt(content);
  }

  async function sendPrompt(content: string) {
    if (!lesson) return;
    setChatError("");
    setFailedPrompt("");
    setIsSending(true);
    try {
      const response = await api.sendMessage(lesson.id, content);
      setMessages((current) => [...current, response.message]);
      setUsage(response.usage);
    } catch (caught) {
      setChatError(caught instanceof Error ? caught.message : "Could not send that follow-up.");
      setFailedPrompt(content);
    } finally {
      setIsSending(false);
    }
  }

  function startOver() {
    setLesson(null);
    setMessages([]);
    setUsage(undefined);
    setLessonError("");
    setChatError("");
    setFailedPrompt("");
    setDraft("");
  }

  return (
    <Layout>
      <div className={styles.pageHeader}>
        <div>
          <Link to={`/agents/${shareSlug}`} className={styles.backLink}>
            Back to agent
          </Link>
          <h1>{agent?.name ?? "Lesson chat"}</h1>
        </div>
        {lesson ? (
          <button type="button" onClick={startOver}>
            <ArrowPathIcon aria-hidden="true" />
            Start over
          </button>
        ) : null}
      </div>

      {agentError ? <p className={styles.error}>{agentError}</p> : null}
      {!isChecking && !hasApiKey ? <ApiKeyConnect compact /> : null}

      <section className={styles.metadata}>
        <button type="button" className={styles.metadataToggle} onClick={() => setIsMetadataOpen((current) => !current)}>
          Agent details
          <ChevronDownIcon className={isMetadataOpen ? styles.chevronOpen : ""} aria-hidden="true" />
        </button>
        {isMetadataOpen ? (
          <dl className={styles.metadataGrid}>
            <div>
              <dt>Target language</dt>
              <dd>{agent?.targetLanguage ?? "Loading..."}</dd>
            </div>
            <div>
              <dt>Native language</dt>
              <dd>{agent?.nativeLanguage || "Not set"}</dd>
            </div>
            <div>
              <dt>Model</dt>
              <dd>{usage?.model || "Not used yet"}</dd>
            </div>
            <div>
              <dt>Tokens used</dt>
              <dd>{usage?.totalTokens ?? "Not used yet"}</dd>
            </div>
            <div className={styles.instructions}>
              <dt>Instruction summary</dt>
              <dd>{agent?.customInstructions || "No custom instructions."}</dd>
            </div>
          </dl>
        ) : null}
      </section>

      <section className={styles.chatPanel} aria-labelledby="chat-title">
        <h2 id="chat-title">Chat</h2>
        {!lesson ? <ImageCapture disabled={!hasApiKey} onImageReady={handleImageReady} /> : null}
        {lessonError ? <p className={styles.error}>{lessonError}</p> : null}

        <div className={styles.messages} tabIndex={0}>
          {messages.length ? (
            messages.map((message) => (
              <article key={message.id} className={`${styles.message} ${styles[message.role]}`}>
                <span>{message.role === "assistant" ? "WalkiTalki" : "You"}</span>
                {message.role === "assistant" ? <MarkdownLesson markdown={message.content} /> : <p>{message.content}</p>}
              </article>
            ))
          ) : (
            <p className={styles.empty}>Take a photo or upload an image to start the chat.</p>
          )}
          {isSending ? <p className={styles.state}>WalkiTalki is responding...</p> : null}
        </div>

        {chatError ? (
          <div className={styles.retryRow}>
            <p className={styles.error}>{chatError}</p>
            <button type="button" onClick={() => void sendPrompt(failedPrompt)} disabled={!failedPrompt || isSending}>
              <ArrowPathIcon aria-hidden="true" />
              Retry
            </button>
          </div>
        ) : null}

        <form className={styles.composer} onSubmit={sendMessage}>
          <label htmlFor="chat-draft">Message WalkiTalki</label>
          <div className={styles.composerShell}>
            <textarea
              id="chat-draft"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              disabled={!lesson || isSending}
              rows={1}
              maxLength={1100}
              placeholder={lesson ? "Ask a follow-up..." : "Start with a photo first"}
            />
            <button type="submit" aria-label="Send message" disabled={!lesson || isSending || Boolean(chatValidation)}>
              <PaperAirplaneIcon aria-hidden="true" />
            </button>
          </div>
          {lesson && chatValidation && draft ? <p className={styles.error}>{chatValidation}</p> : null}
        </form>
      </section>
    </Layout>
  );
}
