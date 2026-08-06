import { useEffect, useState } from "react";

type HealthResponse = {
  status: "healthy";
  service: string;
};

type BackendState =
  | { status: "checking" }
  | { status: "healthy"; data: HealthResponse }
  | { status: "error"; message: string };

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function App() {
  const [backendState, setBackendState] = useState<BackendState>({ status: "checking" });

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
        <div>
          <p className="panel-label">Backend connection</p>
          <h2>{getStatusTitle(backendState)}</h2>
        </div>
        <StatusBadge backendState={backendState} />
        <p className="status-detail">{getStatusDetail(backendState)}</p>
        <p className="api-url">Using {apiBaseUrl}</p>
      </section>
    </main>
  );
}

function StatusBadge({ backendState }: { backendState: BackendState }) {
  return <span className={`status-badge ${backendState.status}`}>{backendState.status}</span>;
}

function getStatusTitle(backendState: BackendState): string {
  if (backendState.status === "healthy") {
    return "API is healthy";
  }

  if (backendState.status === "error") {
    return "API unavailable";
  }

  return "Checking API";
}

function getStatusDetail(backendState: BackendState): string {
  if (backendState.status === "healthy") {
    return `${backendState.data.service} responded with ${backendState.data.status}.`;
  }

  if (backendState.status === "error") {
    return backendState.message;
  }

  return "Waiting for the health endpoint to respond.";
}

export default App;
