import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ClipboardDocumentIcon, PlayIcon } from "@heroicons/react/24/outline";
import { api } from "../api/client";
import AgentSummary from "../components/AgentSummary";
import ApiKeyConnect from "../components/ApiKeyConnect";
import Layout from "../components/Layout";
import { useApiKeySession } from "../hooks/useApiKeySession";
import type { PublishedAgent } from "../types";
import styles from "./AgentLandingPage.module.css";

export default function AgentLandingPage() {
  const { shareSlug = "" } = useParams();
  const { hasApiKey, isChecking } = useApiKeySession();
  const [agent, setAgent] = useState<PublishedAgent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let alive = true;
    setIsLoading(true);
    api
      .getSharedAgent(shareSlug)
      .then((nextAgent) => {
        if (alive) setAgent(nextAgent);
      })
      .catch((caught) => {
        if (alive) setError(caught instanceof Error ? caught.message : "Could not load shared agent.");
      })
      .finally(() => {
        if (alive) setIsLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [shareSlug]);

  async function copyShareLink() {
    const link = `${window.location.origin}/agents/${shareSlug}`;
    await navigator.clipboard.writeText(link);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2200);
  }

  return (
    <Layout>
      {isLoading ? <p className={styles.state}>Loading shared agent...</p> : null}
      {error ? <p className={styles.error}>{error}</p> : null}
      {agent ? (
        <div className={styles.grid}>
          <section className={styles.primary}>
            <AgentSummary agent={agent} />
            <div className={styles.notice}>
              <p>The current visitor's OpenAI API key is used for lessons.</p>
              <p>The creator's API key, uploaded images, chat history, and lesson sessions are not shared.</p>
            </div>
            <div className={styles.actions}>
              <Link className={`${styles.startLink} ${!hasApiKey ? styles.disabled : ""}`} to={hasApiKey ? `/agents/${shareSlug}/chat` : "#"}>
                <PlayIcon aria-hidden="true" />
                Start chat
              </Link>
              <button type="button" onClick={() => void copyShareLink()}>
                <ClipboardDocumentIcon aria-hidden="true" />
                Copy share link
              </button>
              <span role="status" aria-live="polite" className={styles.copied}>
                {copied ? "Copied" : ""}
              </span>
            </div>
          </section>
          <aside>{!isChecking && !hasApiKey ? <ApiKeyConnect compact /> : null}</aside>
        </div>
      ) : null}
    </Layout>
  );
}
