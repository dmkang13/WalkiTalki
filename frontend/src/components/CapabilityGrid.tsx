import {
  AcademicCapIcon,
  ArchiveBoxIcon,
  ArrowPathRoundedSquareIcon,
  BookOpenIcon,
  CameraIcon,
  ChartBarIcon,
  CodeBracketSquareIcon,
  CpuChipIcon,
  DocumentTextIcon,
  SpeakerWaveIcon
} from "@heroicons/react/24/outline";
import styles from "./CapabilityGrid.module.css";

const capabilities = [
  { label: "Image Input", enabled: true, Icon: CameraIcon },
  { label: "Flashcards", enabled: false, Icon: ArchiveBoxIcon },
  { label: "Memory", enabled: false, Icon: CpuChipIcon },
  { label: "Documents", enabled: false, Icon: DocumentTextIcon },
  { label: "Vector Recall", enabled: false, Icon: ArrowPathRoundedSquareIcon },
  { label: "Audio", enabled: false, Icon: SpeakerWaveIcon },
  { label: "API Tools", enabled: false, Icon: CodeBracketSquareIcon },
  { label: "Scripts", enabled: false, Icon: BookOpenIcon },
  { label: "Classroom", enabled: false, Icon: AcademicCapIcon },
  { label: "Progress", enabled: false, Icon: ChartBarIcon }
];

export default function CapabilityGrid() {
  return (
    <section className={styles.panel} aria-labelledby="capability-title">
      <h2 id="capability-title">Capabilities</h2>
      <div className={styles.grid}>
        {capabilities.map(({ label, enabled, Icon }) => (
          <button
            key={label}
            type="button"
            className={`${styles.item} ${enabled ? styles.active : styles.disabled}`}
            disabled={!enabled}
            title={enabled ? "Included in this agent." : "Not included in this MVP."}
            aria-label={`${label}${enabled ? " enabled" : " disabled. Not included in this MVP."}`}
          >
            <Icon aria-hidden="true" />
            <span>{label}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
