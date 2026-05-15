import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRightIcon } from "@heroicons/react/24/outline";
import { api } from "../api/client";
import Layout from "../components/Layout";
import type { PublishedAgent } from "../types";
import styles from "./AgentsPage.module.css";

export default function AgentsPage() {
  const [agents, setAgents] = useState<PublishedAgent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    api
      .listSharedAgents()
      .then((response) => {
        if (alive) setAgents(response.agents);
      })
      .catch((caught) => {
        if (alive) setError(caught instanceof Error ? caught.message : "Published agents could not be loaded.");
      })
      .finally(() => {
        if (alive) setIsLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  return (
    <Layout>
      <div className={styles.header}>
        <div>
          <p className={styles.eyebrow}>Published MVP agents</p>
          <h1>Agents</h1>
          <p>Every photo-language agent published in this prototype is available here.</p>
        </div>
        <Link to="/build" className={styles.buildLink}>
          Build Agent
        </Link>
      </div>

      {isLoading ? <p className={styles.state}>Loading published agents...</p> : null}
      {error ? <p className={styles.error}>{error}</p> : null}
      {!isLoading && !error && agents.length === 0 ? (
        <section className={styles.empty}>
          <h2>No published agents yet</h2>
          <p>Publish a Photo Language Agent and it will appear here.</p>
          <Link to="/build">Create the first agent</Link>
        </section>
      ) : null}

      <div className={styles.grid}>
        {agents.map((agent) => (
          <article className={styles.card} key={agent.id}>
            <div>
              <h2>{agent.name}</h2>
              <p>
                {agent.targetLanguage}
                {agent.nativeLanguage ? ` from ${agent.nativeLanguage}` : ""}
              </p>
            </div>
            {agent.customInstructions ? <p className={styles.instructions}>{agent.customInstructions}</p> : null}
            <Link to={`/agents/${agent.shareSlug}`} className={styles.openLink}>
              Open Agent
              <ArrowRightIcon aria-hidden="true" />
            </Link>
          </article>
        ))}
      </div>
    </Layout>
  );
}
