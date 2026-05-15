import { Link } from "react-router-dom";
import { ArrowRightIcon, CheckCircleIcon } from "@heroicons/react/24/outline";
import ApiKeyConnect from "../components/ApiKeyConnect";
import Layout from "../components/Layout";
import { useApiKeySession } from "../hooks/useApiKeySession";
import styles from "./HomePage.module.css";

export default function HomePage() {
  const { hasApiKey, isChecking } = useApiKeySession();

  return (
    <Layout>
      <div className={styles.grid}>
        <section className={styles.intro}>
          <p className={styles.eyebrow}>MVP agent builder</p>
          <h1>Build a photo language tutor and share it directly.</h1>
          <p>
            Connect your own OpenAI key, publish one constrained agent, then let recipients run lessons with their own key.
          </p>
          {hasApiKey ? (
            <div className={styles.actions}>
              <Link className={styles.primaryLink} to="/build">
                Create Photo Language Agent
                <ArrowRightIcon aria-hidden="true" />
              </Link>
              <Link className={styles.secondaryLink} to="/agents">
                View Published Agents
              </Link>
            </div>
          ) : null}
        </section>
        <aside>
          {isChecking ? (
            <div className={styles.statusCard}>Checking API key session...</div>
          ) : hasApiKey ? (
            <div className={styles.connectedCard}>
              <CheckCircleIcon aria-hidden="true" />
              <div>
                <h2>API key connected</h2>
                <p>You can build or run a shared lesson in this browser session.</p>
              </div>
            </div>
          ) : (
            <ApiKeyConnect />
          )}
        </aside>
      </div>
    </Layout>
  );
}
