import { Link, NavLink } from "react-router-dom";
import { CameraIcon } from "@heroicons/react/24/outline";
import type { ReactNode } from "react";
import { useApiKeySession } from "../hooks/useApiKeySession";
import styles from "./Layout.module.css";

export default function Layout({ children }: { children: ReactNode }) {
  const { hasApiKey, disconnect } = useApiKeySession();

  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <Link to="/" className={styles.brand}>
          <CameraIcon aria-hidden="true" />
          <span>WalkiTalki</span>
        </Link>
        <nav className={styles.nav} aria-label="Primary navigation">
          <NavLink to="/build">Build</NavLink>
          {hasApiKey ? (
            <button type="button" className={styles.textButton} onClick={() => void disconnect()}>
              Disconnect key
            </button>
          ) : (
            <span className={styles.status}>No key connected</span>
          )}
        </nav>
      </header>
      <main className={styles.main}>{children}</main>
    </div>
  );
}
