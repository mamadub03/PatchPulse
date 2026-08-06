import { useEffect, useState } from "react";

type HealthResponse = {
  status: "healthy";
  service: string;
};

type ReadinessResponse = {
  status: "ready" | "not_ready";
  database: "connected" | "unavailable";
};

type BackendState =
  | { status: "checking" }
  | { status: "healthy"; data: HealthResponse }
  | { status: "error"; message: string };

type DatabaseState =
  | { status: "checking" }
  | { status: "connected"; data: ReadinessResponse }
  | { status: "unavailable"; message: string };

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function App() {
  const [backendState, setBackendState] = useState<BackendState>({ status: "checking" });
  const [databaseState, setDatabaseState] = useState<DatabaseState>({ status: "checking" });

  useEffect(() => {
    const controller = new AbortController();

    async function checkBackendHealth(): Promise<void> {
      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/health`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Backend returned HTTP ${response.status}`);
        }

        const data = (await response.json()) as HealthResponse;
        setBackendState({ status: "healthy", data });
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        setBackendState({
          status: "error",
          message: error instanceof Error ? error.message : "Backend health check failed",
        });
      }
    }

    void checkBackendHealth();

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function checkDatabaseReadiness(): Promise<void> {
      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/readiness`, {
          signal: controller.signal,
        });

        const data = (await response.json()) as ReadinessResponse;

        if (response.status === 503) {
          setDatabaseState({
            status: "unavailable",
            message: "Database readiness check reported unavailable.",
          });
          return;
        }

        if (!response.ok) {
          throw new Error(`Readiness endpoint returned HTTP ${response.status}`);
        }

        setDatabaseState({ status: "connected", data });
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        setDatabaseState({
          status: "unavailable",
          message: error instanceof Error ? error.message : "Database readiness check failed",
        });
      }
    }

    void checkDatabaseReadiness();

    return () => controller.abort();
  }, []);

  return (
    <main className="app-shell">
      <section className="intro">
        <p className="eyebrow">Dependency vulnerability tracking</p>
        <h1>PatchPulse</h1>
        <p className="description">
          Track vulnerable Python dependencies from GitHub repositories and keep remediation
          history visible as the product grows.
        </p>
      </section>

      <section className="status-panel" aria-live="polite">
        <StatusBlock
          label="Backend connection"
          title={getBackendStatusTitle(backendState)}
          badge={backendState.status}
          badgeTone={backendState.status}
          detail={getBackendStatusDetail(backendState)}
        />
        <StatusBlock
          label="Database readiness"
          title={getDatabaseStatusTitle(databaseState)}
          badge={databaseState.status}
          badgeTone={databaseState.status}
          detail={getDatabaseStatusDetail(databaseState)}
        />
        <p className="api-url">Using {apiBaseUrl}</p>
      </section>
    </main>
  );
}

function StatusBlock({
  label,
  title,
  badge,
  badgeTone,
  detail,
}: {
  label: string;
  title: string;
  badge: string;
  badgeTone: string;
  detail: string;
}) {
  return (
    <div className="status-block">
      <div>
        <p className="panel-label">{label}</p>
        <h2>{title}</h2>
      </div>
      <span className={`status-badge ${badgeTone}`}>{badge}</span>
      <p className="status-detail">{detail}</p>
    </div>
  );
}

function getBackendStatusTitle(backendState: BackendState): string {
  if (backendState.status === "healthy") {
    return "API is healthy";
  }

  if (backendState.status === "error") {
    return "API unavailable";
  }

  return "Checking API";
}

function getBackendStatusDetail(backendState: BackendState): string {
  if (backendState.status === "healthy") {
    return `${backendState.data.service} responded with ${backendState.data.status}.`;
  }

  if (backendState.status === "error") {
    return backendState.message;
  }

  return "Waiting for the health endpoint to respond.";
}

function getDatabaseStatusTitle(databaseState: DatabaseState): string {
  if (databaseState.status === "connected") {
    return "Database connected";
  }

  if (databaseState.status === "unavailable") {
    return "Database unavailable";
  }

  return "Checking database";
}

function getDatabaseStatusDetail(databaseState: DatabaseState): string {
  if (databaseState.status === "connected") {
    return `PostgreSQL readiness is ${databaseState.data.database}.`;
  }

  if (databaseState.status === "unavailable") {
    return databaseState.message;
  }

  return "Waiting for the readiness endpoint to respond.";
}

export default App;
