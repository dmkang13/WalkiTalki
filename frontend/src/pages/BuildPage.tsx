import { FormEvent, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PaperAirplaneIcon } from "@heroicons/react/24/outline";
import { api } from "../api/client";
import AgentSummary from "../components/AgentSummary";
import ApiKeyConnect from "../components/ApiKeyConnect";
import CapabilityGrid from "../components/CapabilityGrid";
import Layout from "../components/Layout";
import { useApiKeySession } from "../hooks/useApiKeySession";
import type { AgentFormValues } from "../types";
import { validateAgent } from "../validation";
import styles from "./BuildPage.module.css";

const initialValues: AgentFormValues = {
  name: "Photo Language Tutor",
  targetLanguage: "",
  nativeLanguage: "",
  customInstructions: ""
};

export default function BuildPage() {
  const navigate = useNavigate();
  const { hasApiKey, isChecking } = useApiKeySession();
  const [values, setValues] = useState(initialValues);
  const [submitError, setSubmitError] = useState("");
  const [isPublishing, setIsPublishing] = useState(false);
  const errors = useMemo(() => validateAgent(values), [values]);
  const isValid = Object.keys(errors).length === 0;

  function updateField(field: keyof AgentFormValues, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!isValid || !hasApiKey) return;
    setIsPublishing(true);
    setSubmitError("");
    try {
      const agent = await api.createAgent(values);
      const published = await api.publishAgent(agent.id);
      navigate(`/agents/${published.shareSlug}`);
    } catch (caught) {
      setSubmitError(caught instanceof Error ? caught.message : "Could not publish the agent.");
    } finally {
      setIsPublishing(false);
    }
  }

  return (
    <Layout>
      <div className={styles.heading}>
        <div>
          <p className={styles.eyebrow}>Builder</p>
          <h1>Photo Language Agent</h1>
        </div>
        <p>Only image-based language tutoring is functional in this MVP.</p>
      </div>

      {!isChecking && !hasApiKey ? <ApiKeyConnect compact /> : null}

      <div className={styles.builderGrid}>
        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label htmlFor="agent-name">Agent name</label>
            <input id="agent-name" value={values.name} onChange={(event) => updateField("name", event.target.value)} maxLength={100} />
            {errors.name ? <p className={styles.error}>{errors.name}</p> : null}
          </div>
          <div className={styles.field}>
            <label htmlFor="target-language">Target language</label>
            <input
              id="target-language"
              value={values.targetLanguage}
              onChange={(event) => updateField("targetLanguage", event.target.value)}
              placeholder="Korean"
              maxLength={100}
            />
            {errors.targetLanguage ? <p className={styles.error}>{errors.targetLanguage}</p> : null}
          </div>
          <div className={styles.field}>
            <label htmlFor="native-language">Native language optional</label>
            <input
              id="native-language"
              value={values.nativeLanguage}
              onChange={(event) => updateField("nativeLanguage", event.target.value)}
              placeholder="English"
              maxLength={100}
            />
            {errors.nativeLanguage ? <p className={styles.error}>{errors.nativeLanguage}</p> : null}
          </div>
          <div className={styles.field}>
            <label htmlFor="custom-instructions">Custom instructions optional</label>
            <textarea
              id="custom-instructions"
              value={values.customInstructions}
              onChange={(event) => updateField("customInstructions", event.target.value)}
              placeholder="Use simple examples. Keep explanations short."
              rows={8}
              maxLength={1100}
            />
            <span className={styles.count}>{values.customInstructions.length}/1000</span>
            {errors.customInstructions ? <p className={styles.error}>{errors.customInstructions}</p> : null}
          </div>
          {submitError ? <p className={styles.error}>{submitError}</p> : null}
          <button type="submit" disabled={!isValid || !hasApiKey || isPublishing}>
            <PaperAirplaneIcon aria-hidden="true" />
            {isPublishing ? "Publishing..." : "Publish agent"}
          </button>
        </form>

        <aside className={styles.side}>
          <AgentSummary agent={values} />
          <CapabilityGrid />
        </aside>
      </div>
    </Layout>
  );
}
