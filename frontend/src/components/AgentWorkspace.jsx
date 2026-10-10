import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ReactFlow, Handle, Position, MarkerType } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { api } from "../api.js";

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
  return (
    <div className={`flow-stage ${data.status || "blueprint"}`}>
      <Handle type="target" position={Position.Top} />
      <span className="eyebrow">
        {data.number} / {data.status || "Workflow stage"}
      </span>
      <strong>{data.label}</strong>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
const nodeTypes = { stage: Stage };

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
  const rows = records.filter((r) => filter === "all" || r.status === filter);
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
          ["Records", run.summary?.total || 0],
          ["Verified", run.summary?.verified || 0],
          ["Flagged", run.summary?.flagged || 0],
          ["Duplicates merged", run.summary?.duplicates_merged || 0],
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
              {rows.map((item) => (
                <tr key={item.id}>
                  <td>
                    <span className={`status-tag ${item.status}`}>
                      {item.status === "verified"
                        ? "Verified"
                        : "Review required"}
                    </span>
                  </td>
                  <td>{item.full_name || item.title || "Missing name"}</td>
                  <td>
                    {item.event_id || "Missing event ID"}
                    <small>{item.email || "No email extracted"}</small>
                  </td>
                  <td>{item.starts_at || "Not provided"}</td>
                  <td>{item.duplicate_count}</td>
                  <td>{item.issues.join(", ") || "None"}</td>
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
          <pre>
            {JSON.stringify(
              Object.fromEntries(
                [
                  "id",
                  "event_id",
                  "full_name",
                  "email",
                  "title",
                  "starts_at",
                  "venue",
                  "duplicate_count",
                  "issues",
                ].map((k) => [k, record[k]]),
              ),
              null,
              2,
            )}
          </pre>
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
    Promise.all([api.connections(c.signal), api.runs(c.signal)])
      .then(([tools, history]) => {
        if (!c.signal.aborted) {
          setConnections(tools);
          setRuns(history);
        }
      })
      .catch((err) => {
        if (!c.signal.aborted) setError(err.message);
      });
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
          if (!c.signal.aborted) setError(err.message);
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
      setError(err.message);
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
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  const step = run?.steps?.find((item) => item.node_id === selected);
  const nodes = order.map((key, i) => ({
    id: key,
    type: "stage",
    position: { x: coordinates[i][0], y: coordinates[i][1] },
    data: {
      label: labels[key],
      number: String(i + 1).padStart(2, "0"),
      status: run?.steps?.find((s) => s.node_id === key)?.status,
    },
  }));
  const edges = order
    .slice(1)
    .map((key, i) => ({
      id: `${order[i]}-${key}`,
      source: order[i],
      target: key,
      type: "smoothstep",
      markerEnd: { type: MarkerType.ArrowClosed, color: "#abb1a2" },
      style: { stroke: "#abb1a2", strokeWidth: 1 },
    }));
  const title =
    view === "results"
      ? "Evidence, reconciled."
      : view === "history"
        ? "Every execution, retained."
        : "From sources to decisions.";
  return (
    <div className="agent-page">
      <div className="page-intro">
        <p className="eyebrow">
          {view === "results"
            ? "03 / Verification Results"
            : view === "history"
              ? "04 / Execution History"
              : "02 / Agent Workspace"}
        </p>
        <h1>{title}</h1>
        <p>
          Read-only tools, deterministic checks and a durable record of what
          actually happened.
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
                <p>{tool.note}</p>
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
                  .catch((err) => setError(err.message))
              }
            >
              Refresh executions
            </button>
          </div>
          {runs.length ? (
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
                </button>
              ))}
            </div>
          ) : (
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
                  <button key={key} onClick={() => setSelected(key)}>
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
                  </dl>
                  {step.error && <p className="error-text">{step.error}</p>}
                  <h3>Inputs</h3>
                  <pre>{JSON.stringify(step.inputs, null, 2)}</pre>
                  <h3>Outputs / validation</h3>
                  <pre>{JSON.stringify(step.outputs, null, 2)}</pre>
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
