import { FormEvent, useState } from "react";
import { KeyIcon } from "@heroicons/react/24/outline";
import { useApiKeySession } from "../hooks/useApiKeySession";
import styles from "./ApiKeyConnect.module.css";

type ApiKeyConnectProps = {
  compact?: boolean;
};

export default function ApiKeyConnect({ compact = false }: ApiKeyConnectProps) {
  const [apiKey, setApiKey] = useState("");
  const [success, setSuccess] = useState(false);
  const { connect, error, hasApiKey, isConnecting } = useApiKeySession();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSuccess(false);
    const connected = await connect(apiKey.trim());
    if (connected) {
      setApiKey("");
      setSuccess(true);
    }
  }

  return (
    <section className={`${styles.panel} ${compact ? styles.compact : ""}`} aria-labelledby="api-key-title">
      <div className={styles.header}>
        <KeyIcon aria-hidden="true" />
        <div>
          <h2 id="api-key-title">Connect your OpenAI key</h2>
          <p>No key, no lesson generation. Your browser session must be connected before AI compute runs.</p>
        </div>
      </div>
      <form onSubmit={handleSubmit} className={styles.form}>
        <label htmlFor="api-key">OpenAI API key</label>
        <div className={styles.row}>
          <input
            id="api-key"
            type="password"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder="sk-..."
            autoComplete="off"
            required
          />
          <button type="submit" disabled={isConnecting || !apiKey.trim()}>
            {isConnecting ? "Connecting..." : "Connect"}
          </button>
        </div>
      </form>
      <p className={styles.notice}>You pay OpenAI directly through your own key. The raw key is not stored in browser storage.</p>
      {hasApiKey && (success || compact) ? <p className={styles.success}>API key session connected.</p> : null}
      {error ? <p className={styles.error}>{error}</p> : null}
    </section>
  );
}
