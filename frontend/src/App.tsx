import { useCallback, useEffect, useState } from "react";

type Repository = {
  id: string;
  full_name: string;
  default_branch: string;
  is_private: boolean;
};

type Scan = {
  id: string;
  repository_id: string;
  repository_full_name: string;
  status: "running" | "completed" | "completed_with_warnings" | "failed";
  error_code: string | null;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
  dependency_count: number;
  checked_count?: number;
  unsupported_count?: number;
  finding_count: number;
  findings?: Array<{ package: string | null; version: string | null; vulnerability_id: string; summary: string | null; severity: string | null; fixed_version: string | null; advisory_url: string | null }>;
  unsupported_dependencies?: Array<{ original_requirement: string; reason: string }>;
};

type RequestState = "idle" | "loading" | "success" | "error";
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  // All browser traffic goes through PatchPulse. GitHub/OSV credentials and calls
  // remain backend-only trust boundaries.
  const response = await fetch(`${apiBaseUrl}/api/v1${path}`, options);
  const payload = (await response.json()) as T & { detail?: string };
  if (!response.ok) {
    throw new Error(payload.detail ?? "PatchPulse could not complete the request.");
  }
  return payload;
}

function App() {
  const [apiStatus, setApiStatus] = useState("Checking API");
  const [databaseStatus, setDatabaseStatus] = useState("Checking database");
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [repositoryState, setRepositoryState] = useState<RequestState>("loading");
  const [scanState, setScanState] = useState<RequestState>("loading");
  const [syncState, setSyncState] = useState<RequestState>("idle");
  const [activeRepository, setActiveRepository] = useState<string | null>(null);
  const [selectedScan, setSelectedScan] = useState<Scan | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const loadRepositories = useCallback(async () => {
    // Repository ownership is enforced again by the backend; this state only drives UI.
    setRepositoryState("loading");
    try {
      setRepositories(await apiRequest<Repository[]>("/repositories"));
      setRepositoryState("success");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load repositories.");
      setRepositoryState("error");
    }
  }, []);

  const loadScans = useCallback(async () => {
    setScanState("loading");
    try {
      setScans(await apiRequest<Scan[]>("/scans"));
      setScanState("success");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load scan history.");
      setScanState("error");
    }
  }, []);

  useEffect(() => {
    // These checks are intentionally independent: liveness may remain healthy while
    // PostgreSQL readiness is unavailable.
    void apiRequest<{ status: string }>("/health")
      .then(() => setApiStatus("API is healthy"))
      .catch(() => setApiStatus("API unavailable"));
    void apiRequest<{ database: string }>("/readiness")
      .then(() => setDatabaseStatus("Database connected"))
      .catch(() => setDatabaseStatus("Database unavailable"));
    void loadRepositories();
    void loadScans();
  }, [loadRepositories, loadScans]);

  async function syncRepositories() {
    setSyncState("loading");
    setMessage(null);
    try {
      const result = await apiRequest<{
        repositories_discovered: number;
        repositories_created: number;
        repositories_updated: number;
      }>("/repositories/sync", { method: "POST" });
      setMessage(
        `Found ${result.repositories_discovered}; created ${result.repositories_created}; updated ${result.repositories_updated}.`,
      );
      setSyncState("success");
      await loadRepositories();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "GitHub synchronization failed.");
      setSyncState("error");
    }
  }

  async function startScan(repositoryId: string) {
    // The active repository disables every Start Scan button during this synchronous
    // request. The backend also rejects an already-running scan for defense in depth.
    setActiveRepository(repositoryId);
    setMessage(null);
    try {
      const scan = await apiRequest<Scan>(`/repositories/${repositoryId}/scans`, {
        method: "POST",
      });
      setMessage(
        scan.status === "completed"
          ? "requirements.txt retrieved successfully."
          : (scan.error_message ?? "Scan failed."),
      );
      setSelectedScan(scan);
      await loadScans();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not start scan.");
    } finally {
      setActiveRepository(null);
    }
  }

  async function viewScan(scanId: string) {
    // Historical results come from PostgreSQL through scan detail; viewing them never
    // re-contacts GitHub or OSV.
    setMessage(null);
    try {
      setSelectedScan(await apiRequest<Scan>(`/scans/${scanId}`));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load scan results.");
    }
  }

  return (
    <main className="app-shell">
      <header className="intro">
        <p className="eyebrow">Dependency vulnerability tracking</p>
        <h1>PatchPulse</h1>
        <p className="description">
          Synchronize GitHub repositories and verify that their default branch contains a usable
          requirements.txt file.
        </p>
        <div className="connection-row" aria-live="polite">
          <span className={apiStatus.includes("unavailable") ? "error" : ""}>{apiStatus}</span>
          <span className={databaseStatus.includes("unavailable") ? "error" : ""}>{databaseStatus}</span>
        </div>
      </header>

      <section className="workspace">
        <div className="section-heading">
          <div>
            <p className="panel-label">GitHub repositories</p>
            <h2>Choose what to scan</h2>
          </div>
          <button disabled={syncState === "loading"} onClick={() => void syncRepositories()}>
            {syncState === "loading" ? "Syncing…" : "Sync GitHub Repositories"}
          </button>
        </div>
        {message && <p className={`notice ${syncState === "error" ? "error" : ""}`}>{message}</p>}
        {repositoryState === "loading" && <p>Loading repositories…</p>}
        {repositoryState === "error" && <p>Repositories are currently unavailable.</p>}
        {repositoryState === "success" && repositories.length === 0 && (
          <p>No repositories yet. Configure GitHub and synchronize to begin.</p>
        )}
        <div className="repository-list">
          {repositories.map((repository) => (
            <article className="repository-card" key={repository.id}>
              <div>
                <h3>{repository.full_name}</h3>
                <p>
                  {repository.is_private ? "Private" : "Public"} · {repository.default_branch}
                </p>
              </div>
              <button
                disabled={activeRepository !== null}
                onClick={() => void startScan(repository.id)}
              >
                {activeRepository === repository.id ? "Scanning…" : "Start Scan"}
              </button>
            </article>
          ))}
        </div>
      </section>

      <section className="workspace">
        <div className="section-heading">
          <div>
            <p className="panel-label">Persisted history</p>
            <h2>Recent scans</h2>
          </div>
          <button className="secondary" onClick={() => void loadScans()}>Refresh</button>
        </div>
        {scanState === "loading" && <p>Loading scan history…</p>}
        {scanState === "error" && <p>Scan history is currently unavailable.</p>}
        {scanState === "success" && scans.length === 0 && <p>No scans have been started.</p>}
        <div className="scan-list">
          {scans.map((scan) => (
            <article className="scan-row" key={scan.id}>
              <div>
                <h3>{scan.repository_full_name}</h3>
                <p>Started {new Date(scan.started_at).toLocaleString()}</p>
                {scan.error_message && <p className="failure">{scan.error_message}</p>}
              </div>
              <span className={`status-badge ${scan.status}`}>
                {scan.status.replace(/_/g, " ")}
              </span>
              <button className="secondary" onClick={() => void viewScan(scan.id)}>View results</button>
            </article>
          ))}
        </div>
      </section>
      {selectedScan && (
        <section className="workspace">
          <div className="section-heading"><div><p className="panel-label">Stored scan result</p><h2>{selectedScan.repository_full_name}</h2></div><span className={`status-badge ${selectedScan.status}`}>{selectedScan.status.replace(/_/g, " ")}</span></div>
          <div className="metrics"><strong>{selectedScan.dependency_count} dependencies</strong><strong>{selectedScan.checked_count ?? 0} checked</strong><strong>{selectedScan.unsupported_count ?? 0} unsupported</strong><strong>{selectedScan.finding_count} vulnerabilities</strong></div>
          {(selectedScan.findings?.length ?? 0) > 0 && <div className="scan-list">{selectedScan.findings?.map((finding) => <article className="scan-row" key={`${finding.package}-${finding.vulnerability_id}`}><div><h3>{finding.package} {finding.version}</h3><p>{finding.vulnerability_id} · {finding.severity ?? "Unknown severity"}</p><p>{finding.summary ?? "No summary available"}</p></div><div>{finding.fixed_version && <p>Fixed in {finding.fixed_version}</p>}{finding.advisory_url && <a href={finding.advisory_url} target="_blank" rel="noreferrer">Advisory</a>}</div></article>)}</div>}
          {(selectedScan.unsupported_dependencies?.length ?? 0) > 0 && <div className="notice"><strong>Unchecked dependencies</strong>{selectedScan.unsupported_dependencies?.map((item) => <p key={item.original_requirement}>{item.original_requirement}: {item.reason}</p>)}</div>}
        </section>
      )}
      <p className="api-url">Using {apiBaseUrl}</p>
    </main>
  );
}

export default App;
