import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowPathIcon, PaperAirplaneIcon } from "@heroicons/react/24/outline";
import { api } from "../api/client";
import AgentSummary from "../components/AgentSummary";
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
      <div className={styles.headerRow}>
        <div>
          <Link to={`/agents/${shareSlug}`} className={styles.backLink}>
            Back to agent
          </Link>
          <h1>Lesson chat</h1>
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

      <div className={styles.chatGrid}>
        <aside className={styles.side}>{agent ? <AgentSummary agent={agent} compact /> : <p className={styles.state}>Loading agent...</p>}</aside>
        <section className={styles.mainPanel}>
          {!lesson ? <ImageCapture disabled={!hasApiKey} onImageReady={handleImageReady} /> : null}
          {lessonError ? <p className={styles.error}>{lessonError}</p> : null}

          <section className={styles.lessonPanel} aria-labelledby="lesson-title">
            <div className={styles.lessonHeader}>
              <h2 id="lesson-title">Generated lesson</h2>
              {usage ? (
                <span>
                  {usage.model} · {usage.totalTokens} tokens
                </span>
              ) : null}
            </div>
            {lesson ? <MarkdownLesson markdown={lesson.lessonMarkdown} /> : <p className={styles.empty}>Submit a photo to generate the first lesson.</p>}
          </section>

          <section className={styles.messagesPanel} aria-labelledby="messages-title">
            <h2 id="messages-title">Chat</h2>
            <div className={styles.messages} tabIndex={0}>
              {messages.length ? (
                messages.map((message) => (
                  <article key={message.id} className={`${styles.message} ${styles[message.role]}`}>
                    <span>{message.role === "assistant" ? "Assistant" : "You"}</span>
                    <p>{message.content}</p>
                  </article>
                ))
              ) : (
                <p className={styles.empty}>Follow-up chat unlocks after a lesson exists.</p>
              )}
              {isSending ? <p className={styles.state}>Assistant is responding...</p> : null}
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
              <label htmlFor="chat-draft">Follow-up question</label>
              <div className={styles.composerRow}>
                <textarea
                  id="chat-draft"
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  disabled={!lesson || isSending}
                  rows={3}
                  maxLength={1100}
                  placeholder="Can you give me a simpler example?"
                />
                <button type="submit" disabled={!lesson || isSending || Boolean(chatValidation)}>
                  <PaperAirplaneIcon aria-hidden="true" />
                  Send
                </button>
              </div>
              {lesson && chatValidation && draft ? <p className={styles.error}>{chatValidation}</p> : null}
            </form>
          </section>
        </section>
      </div>
    </Layout>
  );
}
