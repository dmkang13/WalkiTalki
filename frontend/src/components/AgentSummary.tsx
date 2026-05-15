import type { AgentFormValues, PublishedAgent } from "../types";
import styles from "./AgentSummary.module.css";

type AgentSummaryProps = {
  agent: AgentFormValues | PublishedAgent;
  compact?: boolean;
};

export default function AgentSummary({ agent, compact = false }: AgentSummaryProps) {
  return (
    <section className={`${styles.panel} ${compact ? styles.compact : ""}`} aria-label="Agent summary">
      <p className={styles.eyebrow}>Photo Language Agent</p>
      <h2>{agent.name || "Untitled agent"}</h2>
      <dl>
        <div>
          <dt>Target language</dt>
          <dd>{agent.targetLanguage || "Not selected"}</dd>
        </div>
        {"nativeLanguage" in agent && agent.nativeLanguage ? (
          <div>
            <dt>Native language</dt>
            <dd>{agent.nativeLanguage}</dd>
          </div>
        ) : null}
        {"customInstructions" in agent && agent.customInstructions ? (
          <div>
            <dt>Instruction summary</dt>
            <dd>{agent.customInstructions}</dd>
          </div>
        ) : null}
      </dl>
    </section>
  );
}
