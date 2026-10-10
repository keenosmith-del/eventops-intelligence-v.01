import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, UUID_PATTERN } from "../api.js";
import Evidence from "./Evidence.jsx";
import Exchange, { groupExchanges } from "./Exchange.jsx";

export default function KnowledgeAssistant({ id }) {
  const navigate = useNavigate();
  const [conversation, setConversation] = useState(null),
    [messages, setMessages] = useState([]),
    [history, setHistory] = useState([]);
  const [question, setQuestion] = useState(""),
    [title, setTitle] = useState(""),
    [uuid, setUuid] = useState("");
  const [topK, setTopK] = useState(5),
    [generate, setGenerate] = useState(false),
    [statuses, setStatuses] = useState({});
  const [loading, setLoading] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [historyError, setHistoryError] = useState("");
  const [revision, setRevision] = useState(0),
    [tab, setTab] = useState("evidence"),
    [selected, setSelected] = useState(null);
  const lock = useRef(false),
    activeId = useRef(id),
    textarea = useRef(null);
  activeId.current = id;
  const exchanges = groupExchanges(messages);
  const active =
    exchanges.find((x) => x.question.id === selected) || exchanges.at(-1);

  async function refresh(signal) {
    try {
      setHistory(await api.list(signal));
      setHistoryError("");
    } catch (err) {
      if (!signal?.aborted) setHistoryError(err.message);
    }
  }
  useEffect(() => {
    const c = new AbortController();
    refresh(c.signal);
    return () => c.abort();
  }, []);
  useEffect(() => {
    const c = new AbortController();
    setConversation(null);
    setMessages([]);
    setError("");
    setQuestion("");
    setSelected(null);
    setLoading(false);
    if (id) {
      if (!UUID_PATTERN.test(id)) {
        setError("Enter a valid conversation UUID.");
        return;
      }
      setLoading(true);
      api
        .detail(id, c.signal)
        .then((result) => {
          if (!c.signal.aborted) {
            setConversation(result.conversation);
            setMessages(result.messages);
          }
        })
        .catch((err) => {
          if (!c.signal.aborted) setError(err.message);
        })
        .finally(() => {
          if (!c.signal.aborted) setLoading(false);
        });
    }
    return () => c.abort();
  }, [id, revision]);

  async function create(event) {
    event.preventDefault();
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await api.create(title.trim());
      setTitle("");
      navigate(`/conversations/${result.id}`);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function ask(event) {
    event.preventDefault();
    if (lock.current || !conversation) return;
    if (!question.trim()) {
      setError("Enter a question between 1 and 500 characters.");
      return;
    }
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await api.ask(id, {
        question: question.trim(),
        top_k: Number(topK),
        generate_answer: generate,
      });
      if (activeId.current === id) {
        setMessages((previous) => [
          ...previous,
          ...result.messages.filter(
            (message) => !previous.some((old) => old.id === message.id),
          ),
        ]);
        const retrieval = result.messages.find(
          (message) => message.kind === "retrieval",
        );
        if (retrieval)
          setStatuses((previous) => ({
            ...previous,
            [retrieval.id]: result.generation_status,
          }));
        setSelected(
          result.messages.find((message) => message.kind === "question")?.id,
        );
        setQuestion("");
      }
      await refresh();
    } catch (err) {
      if (activeId.current === id) setError(err.message);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  function openUuid(event) {
    event.preventDefault();
    if (!UUID_PATTERN.test(uuid.trim())) {
      setError("Enter a valid conversation UUID.");
      return;
    }
    navigate(`/conversations/${uuid.trim()}`);
    setRevision((v) => v + 1);
    setUuid("");
  }

  return (
    <div className="knowledge-page">
      <div className="page-intro">
        <p className="eyebrow">01 / Knowledge Assistant</p>
        <h1>{conversation?.title || "Ask with confidence."}</h1>
        <p>
          Operational questions, grounded in your sources. Follow-ups retain the
          backend’s event context.
        </p>
      </div>
      <details className="history-drawer">
        <summary>
          Conversation history{" "}
          <span className="pill">{history.length} recent</span>
        </summary>
        <div className="history-controls">
          <button disabled={busy} onClick={() => navigate("/")}>
            New conversation
          </button>
          <button disabled={busy} onClick={() => refresh()}>
            Refresh history
          </button>
        </div>
        {historyError && <p role="alert">{historyError}</p>}
        {!history.length && !historyError && <p>No conversations yet.</p>}
        <div className="recent-grid">
          {history.map((item) => (
            <button
              key={item.id}
              disabled={busy}
              onClick={() => {
                navigate(`/conversations/${item.id}`);
                setRevision((v) => v + 1);
              }}
            >
              <strong>{item.title || "Untitled conversation"}</strong>
              <small>
                {new Date(item.updated_at).toLocaleString()} ·{" "}
                {item.id.slice(0, 8)}
              </small>
            </button>
          ))}
        </div>
        <form className="restore-form" onSubmit={openUuid}>
          <label htmlFor="restore-id">Open by UUID</label>
          <input
            id="restore-id"
            value={uuid}
            onChange={(e) => setUuid(e.target.value)}
            required
            pattern="[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
            placeholder="Conversation UUID"
            disabled={busy}
          />
          <button disabled={busy}>Open conversation by UUID</button>
        </form>
      </details>
      {error && (
        <div className="notice error" role="alert">
          <strong>Request could not be completed.</strong>
          <p>{error}</p>
          {id && (
            <button disabled={busy} onClick={() => setRevision((v) => v + 1)}>
              Reload saved conversation
            </button>
          )}
        </div>
      )}
      {loading && (
        <div className="panel loading" role="status">
          <span className="spinner" /> Restoring conversation…
        </div>
      )}
      {!id && (
        <section className="panel start-panel">
          <p className="eyebrow">A new line of enquiry</p>
          <h2>Start with what matters.</h2>
          <p>
            Every question, evidence snapshot and generated citation is stored
            by the backend.
          </p>
          <form onSubmit={create}>
            <label htmlFor="title">
              Conversation title <span className="muted">(optional)</span>
            </label>
            <input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={120}
              disabled={busy}
              placeholder="EVT-101 operations briefing"
            />
            <button className="primary" disabled={busy}>
              {busy ? "Creating…" : "Create conversation"}
            </button>
          </form>
        </section>
      )}
      {conversation && (
        <>
          <div className="conversation-meta">
            <span className="pill">Persistent conversation</span>
            <code>{conversation.id}</code>
            <button
              className="text-button"
              disabled={busy}
              onClick={() => setRevision((v) => v + 1)}
            >
              Reload history
            </button>
          </div>
          <div className="knowledge-columns">
            <div className="chat-column">
              <div className="exchanges">
                {exchanges.map((exchange) => (
                  <Exchange
                    key={exchange.question.id}
                    exchange={exchange}
                    status={statuses[exchange.retrieval?.id]}
                    compact
                    onInspect={() => {
                      setSelected(exchange.question.id);
                      setTab("evidence");
                    }}
                  />
                ))}
                {!messages.length && (
                  <div className="empty-conversation">
                    <h2>Begin with a question.</h2>
                    <p>Try an event ID, operational policy or participant.</p>
                    <div className="examples">
                      {[
                        "What time does check-in close for EVT-101?",
                        "Where is EVT-101 being held?",
                      ].map((example) => (
                        <button
                          key={example}
                          onClick={() => {
                            setQuestion(example);
                            textarea.current?.focus();
                          }}
                        >
                          {example}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <form className="composer panel" onSubmit={ask} aria-busy={busy}>
                <label htmlFor="question">
                  {messages.length
                    ? "Continue the conversation"
                    : "Ask your first question"}
                </label>
                <textarea
                  ref={textarea}
                  id="question"
                  rows={3}
                  maxLength={500}
                  required
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={busy}
                  placeholder={
                    messages.length
                      ? "What time does its check-in close?"
                      : "What would you like to know about EVT-101?"
                  }
                  aria-describedby="question-help"
                />
                <div className="composer-options">
                  <label className="toggle">
                    <input
                      type="checkbox"
                      checked={generate}
                      onChange={(e) => setGenerate(e.target.checked)}
                      disabled={busy}
                    />
                    Request Gemini answer
                  </label>
                  <label className="top-k" htmlFor="top-k">
                    Sources{" "}
                    <select
                      id="top-k"
                      value={topK}
                      onChange={(e) => setTopK(e.target.value)}
                      disabled={busy}
                    >
                      {Array.from({ length: 20 }, (_, i) => (
                        <option key={i + 1}>{i + 1}</option>
                      ))}
                    </select>
                  </label>
                  <button
                    className="primary"
                    disabled={busy || !question.trim()}
                  >
                    {busy ? (
                      <>
                        <span className="spinner" />
                        Processing…
                      </>
                    ) : (
                      "Ask question"
                    )}
                  </button>
                </div>
                <div className="composer-foot">
                  <p id="question-help">
                    {generate
                      ? "Optional generation depends on server configuration. At most 5 records are sent to Gemini."
                      : "Evidence only. Enable Gemini to request a grounded answer."}
                  </p>
                  <span>{question.length}/500</span>
                </div>
              </form>
            </div>
            <aside
              className="context-panel panel"
              aria-label="Conversation context"
            >
              <div
                className="tabs"
                role="tablist"
                aria-label="Contextual panel"
              >
                <button
                  role="tab"
                  id="evidence-tab"
                  aria-selected={tab === "evidence"}
                  aria-controls="evidence-panel"
                  onClick={() => setTab("evidence")}
                >
                  Evidence
                </button>
                <button
                  role="tab"
                  id="context-tab"
                  aria-selected={tab === "context"}
                  aria-controls="context-detail"
                  onClick={() => setTab("context")}
                >
                  Context
                </button>
              </div>
              {active ? (
                <>
                  {tab === "evidence" ? (
                    <div
                      role="tabpanel"
                      id="evidence-panel"
                      aria-labelledby="evidence-tab"
                    >
                      <p className="fine-print">
                        Sources for: {active.question.content}
                      </p>
                      <Evidence
                        records={active.retrieval?.evidence}
                        messageId={active.retrieval?.id}
                      />
                      <p className="fine-print">
                        Similarity measures relevance, not factual certainty.
                      </p>
                    </div>
                  ) : (
                    <div
                      role="tabpanel"
                      id="context-detail"
                      aria-labelledby="context-tab"
                    >
                      <h2>Backend query context</h2>
                      <p className="fine-print">
                        This is the persisted retrieval decision, not a claim of
                        general-purpose memory.
                      </p>
                      <dl>
                        <dt>Original question</dt>
                        <dd>{active.question.content}</dd>
                        <dt>Inherited event</dt>
                        <dd>
                          {active.retrieval?.query_plan?.context_resolution
                            ?.inherited_event_id || "None"}
                        </dd>
                        <dt>Context used</dt>
                        <dd>
                          {active.retrieval?.query_plan?.context_resolution
                            ?.used_context
                            ? "Yes"
                            : "No"}
                        </dd>
                      </dl>
                      <pre>
                        {JSON.stringify(active.retrieval?.query_plan, null, 2)}
                      </pre>
                    </div>
                  )}
                </>
              ) : (
                <p className="muted">
                  Ask a question to inspect its evidence and context.
                </p>
              )}
            </aside>
          </div>
        </>
      )}
    </div>
  );
}
