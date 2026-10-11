import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  ReactFlow,
  Handle,
  Position,
  MarkerType,
  useNodesInitialized,
  useReactFlow,
  useNodesState,
} from "@xyflow/react";
import { Check, Clock3, LoaderCircle, Minus, X } from "lucide-react";
import "@xyflow/react/dist/style.css";
import { api } from "../api.js";
import { workspaceError } from "../workspace-errors.js";
import { analysis, rawRecords, stageCount, terminal } from "../execution.js";
import ExecutionReplay, { useExecutionReplay } from "./ExecutionReplay.jsx";

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

function FitExecutionGraph() {
  const initialized = useNodesInitialized();
  const { fitView } = useReactFlow();
  useEffect(() => {
    if (!initialized) return;
    const frame = requestAnimationFrame(() =>
      fitView({ padding: 0.16, duration: 0 }),
    );
    return () => cancelAnimationFrame(frame);
  }, [initialized, fitView]);
  return null;
}

const coordinates = [
  [240, 0],
  [0, 120],
  [240, 120],
  [480, 120],
  [240, 240],
  [480, 240],
  [480, 360],
  [240, 360],
  [0, 360],
  [0, 480],
  [240, 480],
];

const links = [
  ["trigger", "calendar"],
  ["trigger", "email"],
  ["trigger", "web"],
  ["calendar", "extraction"],
  ["email", "extraction"],
  ["web", "extraction"],
  ["extraction", "normalization"],
  ["normalization", "deduplication"],
  ["deduplication", "verification"],
  ["verification", "discrepancy"],
  ["discrepancy", "persistence"],
  ["persistence", "export"],
];

function Stage({ data }) {
  const StateIcon = {
    pending: Clock3,
    running: LoaderCircle,
    completed: Check,
    failed: X,
    skipped: Minus,
  }[data.status];
  return (
    <div className={`flow-stage ${data.status || "blueprint"}`}>
      <Handle type="target" position={Position.Top} />
      {data.status && (
        <span className="eyebrow">
          {StateIcon && (
            <StateIcon
              className={data.status === "running" ? "stage-running-icon" : ""}
              size={12}
              strokeWidth={1.5}
              aria-hidden="true"
            />
          )}
          {data.status.replaceAll("_", " ")}
        </span>
      )}
      <strong>{data.label}</strong>
      {typeof data.count === "number" && (
        <small>
          {data.count} {data.unit || "records"}
        </small>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

const nodeTypes = { stage: Stage };

function elapsed(start, finish) {
  if (!start || !finish) return "Not recorded";
  const milliseconds = Date.parse(finish) - Date.parse(start);
  return Number.isFinite(milliseconds) && milliseconds >= 0
    ? `${(milliseconds / 1000).toFixed(2)} seconds`
    : "Not recorded";
}

function ExecutionData({ value }) {
  if (value === null || value === undefined) return <span>Not recorded</span>;
  if (Array.isArray(value))
    return value.length ? (
      <details className="execution-data">
        <summary>
          {value.length} {value.length === 1 ? "item" : "items"}
        </summary>
        {value.map((item, index) => (
          <div className="execution-data-item" key={index}>
            <ExecutionData value={item} />
          </div>
        ))}
      </details>
    ) : (
      <span>None</span>
    );
  if (typeof value === "object")
    return Object.keys(value).length ? (
      <dl className="execution-data">
        {Object.entries(value).map(([key, item]) => (
          <div key={key}>
            <dt>{key.replaceAll("_", " ")}</dt>
            <dd>
              <ExecutionData value={item} />
            </dd>
          </div>
        ))}
      </dl>
    ) : (
      <span>No values recorded</span>
    );
  return (
    <span>
      {typeof value === "boolean" ? (value ? "Yes" : "No") : String(value)}
    </span>
  );
}

function incomplete(record) {
  return record.issues.some((issue) => issue.startsWith("missing_"));
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
  const detail = useRef(null);
  const [filter, setFilter] = useState("all"),
    [selected, setSelected] = useState(null);
  const [sourceFilter, setSourceFilter] = useState("all"),
    [issueFilter, setIssueFilter] = useState("all"),
    [eventFilter, setEventFilter] = useState("all");
  useEffect(() => {
    setSelected(null);
    setFilter("all");
    setSourceFilter("all");
    setIssueFilter("all");
    setEventFilter("all");
  }, [run.id]);
  const records = run.results || [];
  const stats = analysis(records);
  const rows = records.filter(
    (r) =>
      (filter === "all" ||
        (filter === "incomplete" ? incomplete(r) : r.status === filter)) &&
      (sourceFilter === "all" ||
        r.evidence.some((item) => item.source_type === sourceFilter)) &&
      (issueFilter === "all" || r.issues.includes(issueFilter)) &&
      (eventFilter === "all" || r.event_id === eventFilter),
  );
  const record = records.find((r) => r.id === selected);
  function revealDetail() {
    detail.current?.focus({ preventScroll: true });
    detail.current?.scrollIntoView({
      block: "start",
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth",
    });
  }
  useEffect(() => {
    if (selected) revealDetail();
  }, [selected]);
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
            <option value="unverified">Unverified</option>
            <option value="incomplete">Missing details</option>
          </select>
        </label>
        <label>
          Source{" "}
          <select
            value={sourceFilter}
            onChange={(event) => setSourceFilter(event.target.value)}
          >
            <option value="all">All sources</option>
            {Object.keys(stats.sources).map((source) => (
              <option key={source}>{source}</option>
            ))}
          </select>
        </label>
        <label>
          Event{" "}
          <select
            value={eventFilter}
            onChange={(event) => setEventFilter(event.target.value)}
          >
            <option value="all">All events</option>
            {[...new Set(records.map((record) => record.event_id))].map(
              (event) => (
                <option key={event} value={event}>
                  {event || "Missing event ID"}
                </option>
              ),
            )}
          </select>
        </label>
        <label>
          Discrepancy{" "}
          <select
            value={issueFilter}
            onChange={(event) => setIssueFilter(event.target.value)}
          >
            <option value="all">All discrepancies</option>
            {Object.keys(stats.issues).map((issue) => (
              <option key={issue} value={issue}>
                {issue.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
        {onExport && (
          <>
            <button onClick={() => onExport(false)}>Export all CSV</button>
            <button onClick={() => onExport(true)}>Export verified CSV</button>
          </>
        )}
      </div>
      {terminal(run.status) && (
        <section className="csv-analysis panel" aria-label="CSV analysis">
          <h3>CSV analysis</h3>
          <p>
            Counts from all saved result records; table filters do not change
            this analysis. A multi-source record contributes once to each
            source.
          </p>
          <div className="analysis-columns">
            {[
              ["Status distribution", stats.statuses],
              ["Source contribution", stats.sources],
              ["Discrepancy categories", stats.issues],
            ].map(([title, values]) => (
              <div key={title}>
                <h4>{title}</h4>
                <dl>
                  {Object.entries(values).map(([label, count]) => (
                    <div key={label}>
                      <dt>{label.replaceAll("_", " ")}</dt>
                      <dd>{count}</dd>
                    </div>
                  ))}
                </dl>
                {!Object.keys(values).length && <p>None recorded</p>}
              </div>
            ))}
          </div>
          <p>
            {stats.missing} records with missing fields · {stats.conflicts}{" "}
            records with conflicts or reference mismatches
          </p>
        </section>
      )}
      <div className="metrics">
        {[
          [
            "Retrieved (parsed)",
            stageCount(run.steps, "extraction") ?? "Not recorded",
          ],
          ["Extracted", stageCount(run.steps, "extraction") ?? "Not recorded"],
          [
            "Normalized",
            stageCount(run.steps, "normalization") ?? "Not recorded",
          ],
          ["Records", run.summary?.total ?? "Not recorded"],
          ["Verified", run.summary?.verified ?? "Not recorded"],
          ["Flagged", run.summary?.flagged ?? "Not recorded"],
          [
            "Duplicates merged",
            run.summary?.duplicates_merged ?? "Not recorded",
          ],
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
              {!rows.length && (
                <tr>
                  <td colSpan={7}>No records match this filter.</td>
                </tr>
              )}
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
                  <td title={item.issues.join(", ")}>
                    {item.issues
                      .map((issue) => issue.replaceAll("_", " "))
                      .join(", ") || "None"}
                  </td>
                  <td>
                    <button
                      onClick={() => {
                        if (selected === item.id) revealDetail();
                        else setSelected(item.id);
                      }}
                    >
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
        <section
          ref={detail}
          tabIndex={-1}
          className="panel record-detail"
          aria-label="Record evidence"
        >
          <div className="result-toolbar">
            <h2>{record.full_name || record.title}</h2>
            <button onClick={() => setSelected(null)}>Close detail</button>
          </div>
          <p>
            Decision: <strong>{record.status}</strong>
          </p>
          <h3>Normalized fields</h3>
          <dl className="normalized-fields">
            {[
              ["Event", record.event_id],
              ["Name", record.full_name],
              ["Email", record.email],
              ["Title", record.title],
              ["Schedule", record.starts_at],
              ["Venue", record.venue],
              ["Duplicates", record.duplicate_count],
              ["Discrepancies", record.issues.join(", ")],
            ].map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{value === 0 ? "0" : value || "Not provided"}</dd>
              </div>
            ))}
          </dl>
          <h3>Raw extracted values</h3>
          {rawRecords(run, record).length ? (
            rawRecords(run, record).map((raw, index) => (
              <div className="observed-evidence" key={index}>
                <p>
                  {raw.source_type} / {raw.source_record_id}
                </p>
                <dl className="normalized-fields">
                  {[
                    "event_id",
                    "email",
                    "full_name",
                    "title",
                    "starts_at",
                    "venue",
                  ].map((field) => (
                    <div key={field}>
                      <dt>{field.replaceAll("_", " ")}</dt>
                      <dd>{raw[field] || "Not provided"}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))
          ) : (
            <p>Raw extraction values were not saved for this record.</p>
          )}
          <h3>Field-level verification decisions</h3>
          {record.checks?.length ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Rule / field</th>
                    <th>Actual value</th>
                    <th>Reference / required value</th>
                    <th>Decision</th>
                  </tr>
                </thead>
                <tbody>
                  {record.checks.map((check, index) => (
                    <tr key={index}>
                      <td>
                        {check.rule.replaceAll("_", " ")}
                        <small>{check.field}</small>
                      </td>
                      <td>
                        {Array.isArray(check.actual)
                          ? check.actual.join(", ")
                          : String(check.actual ?? "Not provided") ||
                            "Not provided"}
                      </td>
                      <td>
                        {Array.isArray(check.reference)
                          ? check.reference.join(", ")
                          : String(check.reference ?? "No reference found")}
                      </td>
                      <td>{check.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>
              This older run saved issue codes and reference evidence, but no
              field-level checks.
            </p>
          )}
          <p>
            {record.status === "verified"
              ? "Authoritative references matched and no discrepancy was recorded."
              : `Review is required: ${record.issues.map((issue) => issue.replaceAll("_", " ")).join(", ") || "the saved classification requires review"}. Missing or unmatched information is not verified.`}
          </p>
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
                {item.fields && <ExecutionData value={item.fields} />}
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
  const [searchParams] = useSearchParams();
  const eventFromChat = searchParams.get("event");
  const conversationId = searchParams.get("conversation");
  const journeyQuery = new URLSearchParams();
  if (conversationId && /^[0-9a-f-]{36}$/i.test(conversationId)) journeyQuery.set("conversation", conversationId);
  if (["EVT-101", "EVT-102", "EVT-103"].includes(eventFromChat)) journeyQuery.set("event", eventFromChat);
  const journeySuffix = journeyQuery.size ? `?${journeyQuery}` : "";
  const navigate = useNavigate(),
    [connections, setConnections] = useState([]),
    [runs, setRuns] = useState([]),
    [run, setRun] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [eventId, setEventId] = useState(["EVT-101", "EVT-102", "EVT-103"].includes(eventFromChat) ? eventFromChat : "EVT-101"),
    [limit, setLimit] = useState(20),
    [selected, setSelected] = useState("trigger");
  const [manualSelection, setManualSelection] = useState(false);
  const replay = useExecutionReplay(run);
  const visibleSteps = replay.steps;
  const activeStep = visibleSteps.find((step) => step.status === "running");
  const latestStep = [...visibleSteps]
    .filter((step) => step.finished_at)
    .sort(
      (first, second) =>
        Date.parse(second.finished_at) - Date.parse(first.finished_at),
    )[0];
  useEffect(() => {
    setManualSelection(false);
    setSelected("trigger");
  }, [runId]);
  useEffect(() => {
    if (!manualSelection && (activeStep || latestStep))
      setSelected((activeStep || latestStep).node_id);
  }, [manualSelection, activeStep?.node_id, latestStep?.node_id]);
  function selectStage(id) {
    setManualSelection(true);
    setSelected(id);
  }
  const lock = useRef(false),
    flowSurface = useRef(null);
  const [flow, setFlow] = useState(null);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [listError, setListError] = useState("");
  const [listRevision, setListRevision] = useState(0);
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
    setListError("");
    api
      .connections(c.signal)
      .then((tools) => {
        if (!c.signal.aborted) setConnections(tools);
      })
      .catch((err) => {
        if (!c.signal.aborted) setListError(workspaceError(err));
      });
    api
      .runs(c.signal)
      .then((history) => {
        if (!c.signal.aborted) setRuns(history);
      })
      .catch((err) => {
        if (!c.signal.aborted) setListError(workspaceError(err));
      })
      .finally(() => {
        if (!c.signal.aborted) setLoadingRuns(false);
      });
    return () => c.abort();
  }, [runId, view, listRevision]);
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
            timer = setTimeout(poll, 350);
        } catch (err) {
          if (!c.signal.aborted) setError(workspaceError(err));
        }
      };
      // Defer the initial read so StrictMode cleanup can cancel its trial mount.
      timer = setTimeout(poll, 0);
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
      navigate(`/agents/runs/${result.id}${journeySuffix}`);
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
  const step = visibleSteps.find((item) => item.node_id === selected);
  const nodeUpdates = useMemo(
    () =>
      order.map((key, i) => ({
        id: key,
        type: "stage",
        position: { x: coordinates[i][0], y: coordinates[i][1] },
        data: {
          label: labels[key],
          status: run
            ? visibleSteps.find((s) => s.node_id === key)?.status
            : undefined,
          count:
            visibleSteps.find((s) => s.node_id === key)?.outputs
              ?.record_count ??
            (key === "email"
              ? visibleSteps.find((s) => s.node_id === key)?.outputs
                  ?.messages_read
              : visibleSteps.find((s) => s.node_id === "extraction")?.outputs
                  ?.source_counts?.[key]),
          unit: key === "email" ? "messages read" : "records",
        },
      })),
    [run?.id, visibleSteps],
  );
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  useEffect(() => {
    // Preserve React Flow's measured dimensions across polled status updates.
    // Replacing unmeasured node objects can leave a running graph invisible.
    setNodes((previous) =>
      nodeUpdates.map((node) => ({
        ...previous.find((item) => item.id === node.id),
        ...node,
      })),
    );
  }, [nodeUpdates, setNodes]);
  const edges = useMemo(
    () =>
      links.map(([source, target]) => ({
        id: `${source}-${target}`,
        source,
        target,
        animated: visibleSteps.some(
          (step) => step.node_id === target && step.status === "running",
        ),
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed, color: "#abb1a2" },
        style: { stroke: "#abb1a2", strokeWidth: 1 },
      })),
    [visibleSteps],
  );
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
          {view === "workspace"
            ? "Choose a reference event, then run verification. Sources are read, claims are compared and results are saved automatically."
            : view === "results"
              ? "Open a saved execution. Inspect evidence before exporting all records or only verified matches."
              : "Open a previous execution to revisit its evidence or replay the recorded processing stages."}
        </p>
      </div>
      <nav className="fine-print" aria-label="Reviewer journey">
        <Link to={journeyQuery.has("conversation") ? `/conversations/${conversationId}` : "/workspace"}>1. Ask about an event</Link>
        {" → "}
        <Link to={`/agents${journeySuffix}`}>2. Run verification</Link>
        {" → "}
        <Link to={run ? `/verification/${run.id}${journeySuffix}` : `/verification${journeySuffix}`}>3. Inspect results</Link>
        {" → "}
        <Link to={run ? `/history/${run.id}${journeySuffix}` : `/history${journeySuffix}`}>4. Revisit history</Link>
      </nav>
      {listError && (
        <p role="alert" className="notice error">
          {listError}{" "}
          <button onClick={() => setListRevision((value) => value + 1)}>
            Retry saved executions
          </button>
        </p>
      )}
      {error && (
        <div className="notice error" role="alert">
          {error}
          <button onClick={() => location.reload()}>Reload view</button>
        </div>
      )}
      {view === "results" && (
        <p className="fine-print">
          Verified means the reference checks passed. Flagged records need
          review; unverified records lack a confirmed match. Use Inspect record
          to compare fields and source evidence. CSV exports use all saved
          records, independently of table filters.
        </p>
      )}
      {run?.summary?.execution_mode && (
        <p className="fine-print">
          Data mode: {run.summary.execution_mode.replaceAll("_", " ")}
          {run.summary.execution_mode.startsWith("controlled")
            ? " · Explicit synthetic assessment inputs; no live-provider processing claim."
            : " · Actual external source reads; no fixture fallback."}
        </p>
      )}
      {view === "workspace" && (
        <>
          {loadingRuns && <p role="status">Loading tool configuration…</p>}
          <div className="connection-cards">
            {connections.map((tool) => (
              <div className="panel" key={tool.id}>
                <p className="eyebrow">{tool.label}</p>
                <span
                  className={`status-tag ${run?.steps?.find((step) => step.node_id === tool.id)?.status || tool.status}`}
                >
                  {run?.steps?.find((step) => step.node_id === tool.id)
                    ?.status || tool.status.replace("_", " ")}
                </span>
                <p>
                  {tool.id === "email"
                    ? tool.status === "configured"
                      ? "Read-only sandbox access is configured. Connectivity is checked during a run."
                      : "Connect a Mailtrap sandbox in server settings to read test messages."
                    : tool.note}
                </p>
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
      {runId && !run && !error && <p role="status">Loading saved execution…</p>}
      {(!runId || view === "history" || view === "results") && (
        <section className="panel execution-list">
          <div className="result-toolbar">
            <h2>Saved executions</h2>
            {view === "history" && runId && (
              <button onClick={() => navigate("/history")}>
                Close execution
              </button>
            )}
            <button onClick={() => setListRevision((value) => value + 1)}>
              Refresh executions
            </button>
          </div>
          {loadingRuns ? (
            <p role="status">Loading saved executions…</p>
          ) : runs.length ? (
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
                  <span className="execution-metadata">
                    {item.summary?.total !== undefined
                      ? `${item.summary.total} records`
                      : "Results not recorded"}
                    {item.summary?.tools &&
                      ` · Tools: ${Object.keys(item.summary.tools).join(", ")}`}
                  </span>
                </button>
              ))}
            </div>
          ) : listError ? (
            <p>
              Saved executions are unavailable. Retry saved executions above.
            </p>
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
            {run && terminal(run.status) && <ExecutionReplay replay={replay} />}
          </div>
          <p className="fine-print">
            {run
              ? "Branches show source data converging into extraction. Tool reads execute sequentially; node states come from PostgreSQL. Replay reconstructs recorded timestamps without calling tools."
              : "No execution selected. These labels describe the configured workflow, not completed actions."}
          </p>
          {run && (
            <section
              className="execution-progress"
              aria-label={
                replay.active ? "Recorded progress" : "Execution progress"
              }
            >
              <p role="status">
                {replay.active
                  ? "Recorded replay"
                  : terminal(run.status)
                    ? `Saved outcome: ${run.status}`
                    : "Live execution"}
                {activeStep
                  ? ` · ${labels[activeStep.node_id]} is running`
                  : ""}{" "}
                ·{" "}
                {
                  visibleSteps.filter(
                    (step) =>
                      step.node_id !== "export" &&
                      ["completed", "failed", "skipped"].includes(step.status),
                  ).length
                }{" "}
                of 10 workflow stages settled
              </p>
              <dl>
                {[
                  ["Read (parsed)", stageCount(visibleSteps, "extraction")],
                  ["Extracted", stageCount(visibleSteps, "extraction")],
                  ["Normalized", stageCount(visibleSteps, "normalization")],
                  [
                    "After deduplication",
                    stageCount(visibleSteps, "deduplication"),
                  ],
                  [
                    "Verified",
                    visibleSteps.find((step) => step.node_id === "verification")
                      ?.outputs?.verified,
                  ],
                  [
                    "Flagged",
                    visibleSteps.find((step) => step.node_id === "verification")
                      ?.outputs?.flagged,
                  ],
                ].map(([label, count]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{count ?? "Not recorded"}</dd>
                  </div>
                ))}
              </dl>
            </section>
          )}
          <div className="workflow-columns">
            <div className="workflow-canvas panel">
              <div className="flow-surface" ref={flowSurface}>
                <ReactFlow
                  onInit={setFlow}
                  nodes={nodes}
                  onNodesChange={onNodesChange}
                  edges={edges}
                  nodeTypes={nodeTypes}
                  onNodeClick={(_, node) => selectStage(node.id)}
                  fitView
                  nodesDraggable={false}
                  nodesConnectable={false}
                  edgesFocusable={false}
                  minZoom={0.15}
                  maxZoom={1.5}
                  proOptions={{ hideAttribution: true }}
                >
                  <FitExecutionGraph />
                </ReactFlow>
              </div>
              <div
                className="flow-accessible"
                aria-label="Select execution step"
              >
                {order.map((key) => (
                  <button
                    key={key}
                    aria-pressed={selected === key}
                    onClick={() => selectStage(key)}
                  >
                    {labels[key]}
                    {run
                      ? " · " +
                        (visibleSteps.find((s) => s.node_id === key)?.status ||
                          "unknown")
                      : ""}
                  </button>
                ))}
              </div>
            </div>
            <aside className="panel step-detail">
              <p className="eyebrow">Selected stage</p>
              {run && (
                <button
                  className="follow-progress"
                  aria-pressed={!manualSelection}
                  onClick={() => setManualSelection(false)}
                >
                  Follow progress
                </button>
              )}
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
          <nav className="execution-links" aria-label="Saved execution views">
            <Link to={`/verification/${run.id}${journeySuffix}`}>Open saved results</Link>
            <Link to={`/history/${run.id}${journeySuffix}`}>Open execution history</Link>
            <Link to={`/agents/runs/${run.id}${journeySuffix}`}>Open execution graph</Link>
          </nav>
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
