import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ReactFlow, Handle, Position, MarkerType } from "@xyflow/react";
import { Check, Clock3, LoaderCircle, Minus, X } from "lucide-react";
import "@xyflow/react/dist/style.css";
import { api } from "../api.js";
import { workspaceError } from "../workspace-errors.js";

const labels = {
  trigger: "Run trigger",
  calendar: "Calendar feed",
  email: "Email sandbox",
  web: "Web reference",
  extraction: "Extract claims",
  normalization: "Normalize fields",
  deduplication: "Merge duplicates",
  verification: "Reference checks",
  discrepancy: "Flag discrepancies",
  persistence: "Save results",
  export: "CSV export",
};
const order = Object.keys(labels);
const coordinates = [
  [0, 0],
  [240, 0],
  [480, 0],
  [480, 120],
  [240, 120],
  [0, 120],
  [0, 240],
  [240, 240],
  [480, 240],
  [480, 360],
  [240, 360],
];
function Stage({ data }) {
  const StateIcon = { pending: Clock3, running: LoaderCircle, completed: Check, failed: X, skipped: Minus }[data.status];
  return (
    <div className={`flow-stage ${data.status || "blueprint"}`}>
      <Handle type="target" position={Position.Top} />
      <span className="eyebrow">
        {StateIcon && <StateIcon size={12} strokeWidth={1.5} aria-hidden="true" />}
        {data.status || "Workflow stage"}
      </span>
      <strong>{data.label}</strong>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
const nodeTypes = { stage: Stage };

function elapsed(start, finish) {
  if (!start || !finish) return "Not recorded";
  const milliseconds = Date.parse(finish) - Date.parse(start);
  return Number.isFinite(milliseconds) && milliseconds >= 0 ? `${(milliseconds / 1000).toFixed(2)} seconds` : "Not recorded";
}

function ExecutionData({ value }) {
  if (value === null || value === undefined) return <span>Not recorded</span>;
  if (Array.isArray(value)) return value.length ? <details className="execution-data"><summary>{value.length} {value.length === 1 ? "item" : "items"}</summary>{value.map((item, index) => <div className="execution-data-item" key={index}><ExecutionData value={item} /></div>)}</details> : <span>None</span>;
  if (typeof value === "object") return Object.keys(value).length ? <dl className="execution-data">{Object.entries(value).map(([key, item]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd><ExecutionData value={item} /></dd></div>)}</dl> : <span>No values recorded</span>;
  return <span>{typeof value === "boolean" ? value ? "Yes" : "No" : String(value)}</span>;
}

function incomplete(record) {
  return record.issues.some(issue => issue.startsWith("missing_"));
}

export async function downloadResults(runId, verifiedOnly = false) {
  const blob = await api.exportRun(runId, verifiedOnly),
    url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `eventops-${runId}${verifiedOnly ? "-verified" : ""}.csv`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function ResultTable({ run, onExport }) {
  const [filter, setFilter] = useState("all"),
    [selected, setSelected] = useState(null);
  const records = run.results || [];
  const rows = records.filter((r) => filter === "all" || (filter === "incomplete" ? incomplete(r) : r.status === filter));
  const record = records.find((r) => r.id === selected);
  return (
    <section className="results-section">
      <div className="result-toolbar">
        <h2>Verification results</h2>
        <label htmlFor="result-filter">
          Show{" "}
          <select
            id="result-filter"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All records</option>
            <option value="verified">Verified</option>
            <option value="review_required">Flagged</option>
            <option value="incomplete">Missing details</option>
          </select>
        </label>
        {onExport && (
          <>
            <button onClick={() => onExport(false)}>Export all CSV</button>
            <button onClick={() => onExport(true)}>Export verified CSV</button>
          </>
        )}
      </div>
      <div className="metrics">
        {[
          ["Records", run.summary?.total ?? "Not recorded"],
          ["Verified", run.summary?.verified ?? "Not recorded"],
          ["Flagged", run.summary?.flagged ?? "Not recorded"],
          ["Duplicates merged", run.summary?.duplicates_merged ?? "Not recorded"],
        ].map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      {!records.length ? (
        <div className="panel">
          <p>
            {["pending", "running"].includes(run.status)
              ? "Results will appear after persistence completes."
              : "No extracted result records were saved for this run. Inspect the tool and step outcomes."}
          </p>
        </div>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Status</th>
                <th>Claim / person</th>
                <th>Event / email</th>
                <th>Schedule</th>
                <th>Duplicates</th>
                <th>Discrepancies</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {!rows.length && <tr><td colSpan={7}>No records match this filter.</td></tr>}
              {rows.map((item) => (
                <tr key={item.id}>
                  <td>
                    <span className={`status-tag ${item.status}`}>
                      {item.status === "verified"
                        ? "Verified"
                        : "Review required"}
                    </span>
                    {incomplete(item) && <small>Missing details</small>}
                  </td>
                  <td>{item.full_name || item.title || "Missing name"}</td>
                  <td>
                    {item.event_id || "Missing event ID"}
                    <small>{item.email || "No email extracted"}</small>
                  </td>
                  <td>{item.starts_at || "Not provided"}</td>
                  <td>{item.duplicate_count}</td>
                  <td title={item.issues.join(", ")}>{item.issues.map(issue => issue.replaceAll("_", " ")).join(", ") || "None"}</td>
                  <td>
                    <button onClick={() => setSelected(item.id)}>
                      Inspect record
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!rows.length && (
            <p className="muted">No records match this filter.</p>
          )}
        </div>
      )}
      {record && (
        <section className="panel record-detail" aria-label="Record evidence">
          <div className="result-toolbar">
            <h2>{record.full_name || record.title}</h2>
            <button onClick={() => setSelected(null)}>Close detail</button>
          </div>
          <p>
            Decision: <strong>{record.status}</strong>
          </p>
          <h3>Normalized fields</h3>
          <dl className="normalized-fields">{[
            ["Event", record.event_id], ["Name", record.full_name], ["Email", record.email],
            ["Title", record.title], ["Schedule", record.starts_at], ["Venue", record.venue],
            ["Duplicates", record.duplicate_count], ["Discrepancies", record.issues.join(", ")],
          ].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value === 0 ? "0" : value || "Not provided"}</dd></div>)}</dl>
          <h3>Observed evidence</h3>
          {record.evidence.map((item, i) => (
            <div className="observed-evidence" key={i}>
              <p className="eyebrow">
                {item.source_type} / {item.source_record_id}
              </p>
              <p>{item.excerpt}</p>
              <code>{item.source_reference}</code>
            </div>
          ))}
          <h3>Authoritative reference matches</h3>
          {record.matches.length ? (
            record.matches.map((item) => (
              <div className="observed-evidence" key={item.record_id}>
                <strong>{item.record_id}</strong>
                <p>{item.content}</p>
                <code>{item.source_reference}</code>
              </div>
            ))
          ) : (
            <p>No authoritative record matched. The claim remains flagged.</p>
          )}
        </section>
      )}
    </section>
  );
}

export default function AgentWorkspace({ runId, view = "workspace" }) {
  const navigate = useNavigate(),
    [connections, setConnections] = useState([]),
    [runs, setRuns] = useState([]),
    [run, setRun] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [eventId, setEventId] = useState("EVT-101"),
    [limit, setLimit] = useState(20),
    [selected, setSelected] = useState("trigger");
  const lock = useRef(false),
    flowSurface = useRef(null);
  const [flow, setFlow] = useState(null);
  const [loadingRuns, setLoadingRuns] = useState(true);
  useEffect(() => {
    if (!flow || !flowSurface.current) return;
    const observer = new ResizeObserver(() =>
      flow.fitView({ padding: 0.16, duration: 0 }),
    );
    observer.observe(flowSurface.current);
    return () => observer.disconnect();
  }, [flow]);
  useEffect(() => {
    const c = new AbortController();
    setLoadingRuns(true);
    Promise.all([api.connections(c.signal), api.runs(c.signal)])
      .then(([tools, history]) => {
        if (!c.signal.aborted) {
          setConnections(tools);
          setRuns(history);
        }
      })
      .catch((err) => {
        if (!c.signal.aborted) setError(workspaceError(err));
      }).finally(() => { if (!c.signal.aborted) setLoadingRuns(false); });
    return () => c.abort();
  }, [runId, view]);
  useEffect(() => {
    const c = new AbortController();
    let timer;
    setRun(null);
    setError("");
    if (runId) {
      const poll = async () => {
        try {
          const result = await api.run(runId, c.signal);
          if (c.signal.aborted) return;
          setRun(result);
          if (["pending", "running"].includes(result.status))
            timer = setTimeout(poll, 1500);
        } catch (err) {
          if (!c.signal.aborted) setError(workspaceError(err));
        }
      };
      poll();
    }
    return () => {
      c.abort();
      clearTimeout(timer);
    };
  }, [runId]);
  async function start(event) {
    event.preventDefault();
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await api.startRun({
        event_id: eventId,
        max_records: Number(limit),
      });
      navigate(`/agents/runs/${result.id}`);
    } catch (err) {
      setError(workspaceError(err));
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function exportCsv(verifiedOnly) {
    setBusy(true);
    setError("");
    try {
      await downloadResults(runId, verifiedOnly);
      setRun(await api.run(runId));
    } catch (err) {
      setError(workspaceError(err));
    } finally {
      setBusy(false);
    }
  }
  const step = run?.steps?.find((item) => item.node_id === selected);
  const nodes = useMemo(() => order.map((key, i) => ({
    id: key,
    type: "stage",
    position: { x: coordinates[i][0], y: coordinates[i][1] },
    data: {
      label: labels[key],
      status: run?.steps?.find((s) => s.node_id === key)?.status,
    },
  })), [run?.steps]);
  const edges = useMemo(() => order
    .slice(1)
    .map((key, i) => ({
      id: `${order[i]}-${key}`,
      source: order[i],
      target: key,
      type: "smoothstep",
      markerEnd: { type: MarkerType.ArrowClosed, color: "#abb1a2" },
      style: { stroke: "#abb1a2", strokeWidth: 1 },
    })), []);
  const title =
    view === "results"
      ? "Verification results"
      : view === "history"
        ? "Execution history"
        : "Agent workspace";
  return (
    <div className="agent-page">
      <div className="page-intro">

        <h1>{title}</h1>
        <p>
          Review source reads, verification checks and saved execution results.
        </p>
      </div>
      {error && (
        <div className="notice error" role="alert">
          {error}
          <button onClick={() => location.reload()}>Reload view</button>
        </div>
      )}
      {view === "workspace" && (
        <>
          {loadingRuns && <p role="status">Loading tool configuration…</p>}
          <div className="connection-cards">
            {connections.map((tool) => (
              <div className="panel" key={tool.id}>
                <p className="eyebrow">{tool.label}</p>
                <span
                  className={`status-tag ${run?.summary?.tools?.[tool.id] || tool.status}`}
                >
                  {run?.summary?.tools?.[tool.id] ||
                    tool.status.replace("_", " ")}
                </span>
                <p>{tool.id === "email" ? tool.status === "configured" ? "Read-only sandbox access is configured. Connectivity is checked during a run." : "Connect a Mailtrap sandbox in server settings to read test messages." : tool.note}</p>
                <code>
                  {tool.source || "Server-side configuration required"}
                </code>
              </div>
            ))}
          </div>
          <form className="run-controls panel" onSubmit={start}>
            <div>
              <label htmlFor="event-id">Reference event</label>
              <select
                id="event-id"
                value={eventId}
                onChange={(e) => setEventId(e.target.value)}
                disabled={busy}
              >
                <option>EVT-101</option>
                <option>EVT-102</option>
                <option>EVT-103</option>
              </select>
            </div>
            <div>
              <label htmlFor="record-limit">Records per source</label>
              <input
                id="record-limit"
                type="number"
                min={1}
                max={30}
                value={limit}
                onChange={(e) => setLimit(e.target.value)}
                disabled={busy}
                required
              />
            </div>
            <button
              className="primary"
              disabled={busy || ["pending", "running"].includes(run?.status)}
            >
              {busy ? "Starting…" : "Run verification"}
            </button>
            <p>
              Calendar and web sources are fetched over HTTPS. Mailtrap reads at
              most 3 sandbox messages. No email is sent. Public holiday claims
              remain flagged unless authoritative EVT references match.
            </p>
          </form>
        </>
      )}
      {(!runId || view === "history" || view === "results") && (
        <section className="panel execution-list">
          <div className="result-toolbar">
            <h2>Saved executions</h2>
            <button
              onClick={() =>
                api
                  .runs()
                  .then(setRuns)
                  .catch((err) => setError(workspaceError(err)))
              }
            >
              Refresh executions
            </button>
          </div>
          {loadingRuns ? <p role="status">Loading saved executions…</p> : runs.length ? (
            <div className="recent-grid">
              {runs.map((item) => (
                <button
                  key={item.id}
                  onClick={() =>
                    navigate(
                      `${view === "results" ? "/verification" : view === "history" ? "/history" : "/agents/runs"}/${item.id}`,
                    )
                  }
                >
                  <strong>
                    {item.event_id} · {item.status}
                  </strong>
                  <small>
                    {new Date(item.created_at).toLocaleString()} ·{" "}
                    {item.id.slice(0, 8)}
                  </small>
                  <span className="execution-metadata">{item.summary?.total !== undefined ? `${item.summary.total} records` : "Results not recorded"}{item.summary?.tools && ` · Tools: ${Object.keys(item.summary.tools).join(", ")}`}</span>
                </button>
              ))}
            </div>
          ) : error ? <p>Saved executions are unavailable. Reload this view to retry.</p> : (
            <p>
              No executions saved yet. Run verification from the Agent
              Workspace.
            </p>
          )}
        </section>
      )}
      {(view === "workspace" || (view === "history" && run)) && (
        <section className="workflow-section">
          <div className="result-toolbar">
            <h2>{run ? `Execution · ${run.status}` : "Workflow blueprint"}</h2>
            {run && <code>{run.id}</code>}
          </div>
          <p className="fine-print">
            {run
              ? "Each node reflects its persisted backend step. Tool reads are executed sequentially; failures or missing connections are retained. Export completes only after a CSV is downloaded."
              : "No execution selected. These labels describe the configured workflow, not completed actions."}
          </p>
          <div className="workflow-columns">
            <div className="workflow-canvas panel">
              <div className="flow-surface" ref={flowSurface}>
                <ReactFlow
                  onInit={setFlow}
                  nodes={nodes}
                  edges={edges}
                  nodeTypes={nodeTypes}
                  onNodeClick={(_, node) => setSelected(node.id)}
                  fitView
                  nodesDraggable={false}
                  nodesConnectable={false}
                  edgesFocusable={false}
                  minZoom={0.4}
                  maxZoom={1.5}
                  proOptions={{ hideAttribution: true }}
                />
              </div>
              <div
                className="flow-accessible"
                aria-label="Select execution step"
              >
                {order.map((key) => (
                  <button key={key} aria-pressed={selected === key} onClick={() => setSelected(key)}>
                    {labels[key]}
                    {run
                      ? " · " +
                        (run.steps.find((s) => s.node_id === key)?.status ||
                          "unknown")
                      : ""}
                  </button>
                ))}
              </div>
            </div>
            <aside className="panel step-detail">
              <p className="eyebrow">Selected stage</p>
              <h2>{labels[selected]}</h2>
              {step ? (
                <>
                  <span className={`status-tag ${step.status}`}>
                    {step.status}
                  </span>
                  <dl>
                    <dt>Started</dt>
                    <dd>
                      {step.started_at
                        ? new Date(step.started_at).toLocaleString()
                        : "Not started"}
                    </dd>
                    <dt>Finished</dt>
                    <dd>
                      {step.finished_at
                        ? new Date(step.finished_at).toLocaleString()
                        : "Not finished"}
                    </dd>
                    <dt>Recorded duration</dt>
                    <dd>{elapsed(step.started_at, step.finished_at)}</dd>
                  </dl>
                  {step.error && <p className="error-text">{step.error}</p>}
                  <h3>Inputs</h3>
                  <ExecutionData value={step.inputs} />
                  <h3>Outputs / validation</h3>
                  <ExecutionData value={step.outputs} />
                </>
              ) : (
                <p>
                  Select a saved run to inspect actual timestamps, inputs,
                  outputs and errors.
                </p>
              )}
            </aside>
          </div>
        </section>
      )}
      {run && (
        <>
          <p className="fine-print">
            Created {new Date(run.created_at).toLocaleString()}
            {run.finished_at
              ? " · Finished " + new Date(run.finished_at).toLocaleString()
              : ""}
            . {run.error}
          </p>
          <ResultTable
            run={run}
            onExport={
              !busy && !["pending", "running"].includes(run.status)
                ? exportCsv
                : null
            }
          />
        </>
      )}
    </div>
  );
}
