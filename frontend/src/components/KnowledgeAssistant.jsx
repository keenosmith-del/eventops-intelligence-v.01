import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  ArrowUp,
  ArrowDown,
  LoaderCircle,
  Plus,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { api, UUID_PATTERN } from "../api.js";
import Evidence from "./Evidence.jsx";
import Exchange, { groupExchanges } from "./Exchange.jsx";
import { workspaceError as displayError } from "../workspace-errors.js";

function SourcesMenu({ close }) {
  const [sources, setSources] = useState(null),
    [error, setError] = useState("");
  const menu = useRef(null);
  useEffect(() => {
    const controller = new AbortController();
    api
      .sources(controller.signal)
      .then(setSources)
      .catch((error) => {
        if (!controller.signal.aborted) setError(displayError(error));
      });
    function dismiss(event) {
      if (event.type === "keydown" && event.key === "Escape") close();
      if (
        event.type === "pointerdown" &&
        !menu.current?.contains(event.target) &&
        !event.target.closest(".source-menu-toggle")
      )
        close();
    }
    document.addEventListener("pointerdown", dismiss);
    document.addEventListener("keydown", dismiss);
    return () => {
      controller.abort();
      document.removeEventListener("pointerdown", dismiss);
      document.removeEventListener("keydown", dismiss);
    };
  }, []);
  return (
    <section
      className="source-menu"
      id="source-menu"
      ref={menu}
      aria-label="Indexed documents"
    >
      <Link to="/sources">Open knowledge sources</Link>
      {!sources && !error && <p role="status">Loading documents…</p>}
      {error && <p role="alert">{error}</p>}
      {sources?.sources.map((source) => (
        <Link
          key={source.document_id}
          to={`/sources#source-${source.document_id}`}
        >
          {source.document_id}
          <small>{source.record_count} records</small>
        </Link>
      ))}
      {sources && !sources.sources.length && <p>No indexed documents.</p>}
      <p>Document uploads are unavailable.</p>
    </section>
  );
}

export default function KnowledgeAssistant({ id }) {
  const navigate = useNavigate(),
    location = useLocation();
  const [conversation, setConversation] = useState(null),
    [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState(location.state?.draft || ""),
    [topK, setTopK] = useState(location.state?.options?.topK || 5),
    [generate, setGenerate] = useState(
      location.state?.options?.generate || false,
    );
  const [statuses, setStatuses] = useState(location.state?.generation || {});
  const [loading, setLoading] = useState(Boolean(id)),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(location.state?.error || "");
  const [revision, setRevision] = useState(0),
    [tab, setTab] = useState("evidence"),
    [selected, setSelected] = useState(null),
    [evidenceOpen, setEvidenceOpen] = useState(false),
    [sourcesOpen, setSourcesOpen] = useState(false);
  const lock = useRef(false),
    mounted = useRef(true),
    textarea = useRef(null),
    end = useRef(null),
    pendingQuestion = useRef(null),
    scrollTarget = useRef(null);
  const [pending, setPending] = useState("");
  const [awayFromBottom, setAwayFromBottom] = useState(false);
  const exchanges = groupExchanges(messages);
  const active =
    exchanges.find((exchange) => exchange.question.id === selected) ||
    exchanges.at(-1);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    if (!id) return;
    const controller = new AbortController();
    if (!UUID_PATTERN.test(id)) {
      setError("Enter a valid conversation UUID.");
      setLoading(false);
      return;
    }
    setLoading(true);
    api
      .detail(id, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        setConversation(result.conversation);
        setMessages(result.messages);
        scrollTarget.current = result.messages.filter(message => message.kind === "question").at(-1)?.id;
        setEvidenceOpen(
          window.matchMedia("(min-width: 1121px)").matches &&
            result.messages.some((message) => message.kind === "retrieval"),
        );
      })
      .catch((error) => {
        if (!controller.signal.aborted) setError(displayError(error));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [id, revision]);
  useEffect(() => {
    const media = window.matchMedia("(max-width: 1120px)");
    const update = () => {
      if (media.matches) setEvidenceOpen(false);
    };
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    if (textarea.current) {
      textarea.current.style.height = "auto";
      textarea.current.style.height = `${Math.min(textarea.current.scrollHeight, 140)}px`;
    }
  }, [question]);
  useEffect(() => {
    const update = () => {
      const rect = end.current?.getBoundingClientRect();
      setAwayFromBottom(Boolean(rect && rect.top > window.innerHeight - 180));
    };
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    const observer = new ResizeObserver(update);
    if (end.current?.parentElement) observer.observe(end.current.parentElement);
    update();
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
      observer.disconnect();
    };
  }, [messages, pending]);
  useEffect(() => {
    const target = pending ? pendingQuestion.current
      : scrollTarget.current ? document.getElementById(`exchange-${scrollTarget.current}`) : null;
    if (target) {
      target.scrollIntoView({ block: "start", behavior: "auto" });
      scrollTarget.current = null;
    }
  }, [messages, pending]);
  function jumpToBottom() {
    end.current?.scrollIntoView({ block: "end", behavior:
      window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }

  async function ask(event) {
    event.preventDefault();
    const text = question.trim();
    if (
      lock.current ||
      loading ||
      !text ||
      text.length > 500 ||
      (id && !conversation)
    )
      return;
    lock.current = true;
    setBusy(true);
    setPending(text);
    setError("");
    let target = conversation;
    try {
      if (!target) {
        target = await api.create(text.replace(/\s+/g, " ").slice(0, 120));
        window.dispatchEvent(new Event("eventops-history-updated"));
      }
      const result = await api.ask(target.id, {
        question: text,
        top_k: Number(topK),
        generate_answer: generate,
      });
      const retrieval = result.messages.find(
        (message) => message.kind === "retrieval",
      );
      const generation = retrieval
        ? { [retrieval.id]: result.generation_status }
        : {};
      if (!mounted.current) return;
      if (!id) {
        navigate(`/conversations/${target.id}`, {
          state: { generation, options: { topK, generate } },
        });
      } else {
        // Keep the reader at their question when the answer arrives.
        scrollTarget.current = result.messages.find(message => message.kind === "question")?.id;
        setMessages((previous) => [
          ...previous,
          ...result.messages.filter(
            (message) => !previous.some((old) => old.id === message.id),
          ),
        ]);
        setStatuses((previous) => ({ ...previous, ...generation }));
        setSelected(
          result.messages.find((message) => message.kind === "question")?.id,
        );
        setEvidenceOpen(window.matchMedia("(min-width: 1121px)").matches);
        setQuestion("");
      }
    } catch (error) {
      if (!mounted.current) return;
      if (!id && target)
        navigate(`/conversations/${target.id}`, {
          state: {
            draft: question,
            error: displayError(error),
            options: { topK, generate },
          },
        });
      else setError(displayError(error));
    } finally {
      window.dispatchEvent(new Event("eventops-history-updated"));
      lock.current = false;
      if (mounted.current) {
        setBusy(false);
        setPending("");
        textarea.current?.focus({ preventScroll: true });
      }
    }
  }

  const empty = !messages.length;
  return (
    <div
      className={`knowledge-page conversational-page ${empty ? "chat-empty" : "chat-active"} ${active && evidenceOpen ? "has-evidence" : ""}`}
    >
      <div className="conversation-main">
        {loading && (
          <p className="chat-loading" role="status">
            <LoaderCircle className="loading-icon" size={18} />
            Restoring conversation…
          </p>
        )}
        {error && (
          <div className="notice error" role="alert">
            <p>{error}</p>
            {id && (
              <button
                disabled={busy}
                onClick={() => {
                  setError("");
                  setRevision((value) => value + 1);
                }}
              >
                Reload saved conversation
              </button>
            )}
          </div>
        )}
        {empty && !loading && (
          <section className="chat-welcome">
            <div className={`mascot-presence ${busy ? "is-thinking" : ""}`}>
              <img
                className="chat-mascot"
                src="/mascot-thinking.png"
                alt="EventOps assistant"
              />
            </div>
            <h1>What would you like to know?</h1>
            <p>
              Ask about the indexed events, policies and participant directory.
              Choose a question below to begin.
            </p>
            <div className="example-questions" aria-label="Example questions">
              {[
                "Where is EVT-101 being held?",
                "What time does check-in close for EVT-101?",
                "Who is registered for EVT-101?",
              ].map((example) => (
                <button
                  key={example}
                  type="button"
                  disabled={busy || loading}
                  onClick={() => {
                    setQuestion(example);
                    textarea.current?.focus();
                  }}
                >
                  {example}
                </button>
              ))}
            </div>
          </section>
        )}
        <p className="fine-print">
          Source evidence is shown by default. To check incoming registrations
          against these references,{" "}
          <Link to={`/agents?${new URLSearchParams({
            ...(active?.retrieval?.query_plan?.event_id ? { event: active.retrieval.query_plan.event_id } : {}),
            ...(conversation?.id ? { conversation: conversation.id } : {}),
          })}`}>continue to Agent Workspace</Link>.
        </p>
        {!empty && (
          <div className="conversation-heading">
            <span>{conversation?.title || "Conversation"}</span>
            {!evidenceOpen && (
              <button onClick={() => setEvidenceOpen(true)}>
                Evidence & context
              </button>
            )}
          </div>
        )}
        {!empty && (
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
                  setEvidenceOpen(true);
                }}
              />
            ))}

          </div>
        )}
        {pending && !empty && (
          <article ref={pendingQuestion} className="exchange pending-question">
            <div className="question"><div className="eyebrow">Your question</div><h2>{pending}</h2></div>
          </article>
        )}
        {busy && (
          <p className="chat-loading" role="status">
            {!empty && (
              <span className="mascot-presence is-thinking pending-mascot">
                <img
                  className="chat-mascot"
                  src="/mascot-thinking.png"
                  alt=""
                />
              </span>
            )}
            Reviewing sources{generate ? " and requesting an answer" : ""}…
          </p>
        )}
        <div ref={end} className="chat-end" aria-hidden="true" />
        <form className="chat-composer" onSubmit={ask} aria-busy={busy}>
          {awayFromBottom && !empty && <button type="button" className="jump-to-bottom"
            aria-label="Jump to latest message" onClick={jumpToBottom}><ArrowDown size={17} /> <span>Latest</span></button>}
          <div className="composer-surface">
            <button
              className="source-menu-toggle icon-button"
              type="button"
              aria-label="Knowledge documents"
              aria-expanded={sourcesOpen}
              aria-controls="source-menu"
              onClick={() => setSourcesOpen((value) => !value)}
            >
              <Plus size={20} strokeWidth={1.5} />
            </button>
            {sourcesOpen && <SourcesMenu close={() => setSourcesOpen(false)} />}
            <textarea
              ref={textarea}
              id="question"
              rows={1}
              maxLength={500}
              required
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              disabled={busy || loading || Boolean(id && !conversation)}
              placeholder="Ask EventOps anything..."
              aria-label={
                messages.length
                  ? "Continue the conversation"
                  : "Ask your first question"
              }
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing
                ) {
                  event.preventDefault();
                  event.currentTarget.form.requestSubmit();
                }
              }}
            />
            <button
              className="composer-submit icon-button"
              aria-label="Ask question"
              disabled={
                busy ||
                loading ||
                !question.trim() ||
                question.trim().length > 500 ||
                Boolean(id && !conversation)
              }
            >
              {busy ? (
                <LoaderCircle className="loading-icon" size={19} />
              ) : (
                <ArrowUp size={20} strokeWidth={1.5} />
              )}
            </button>
          </div>
          <details className="answer-options">
            <summary>
              <SlidersHorizontal size={14} strokeWidth={1.5} />
              Answer options
            </summary>
            <div>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={generate}
                  onChange={(event) => setGenerate(event.target.checked)}
                  disabled={busy}
                />
                Request Gemini answer
              </label>
              <label htmlFor="top-k">
                Sources{" "}
                <select
                  id="top-k"
                  value={topK}
                  onChange={(event) => setTopK(event.target.value)}
                  disabled={busy}
                >
                  {Array.from({ length: 20 }, (_, index) => (
                    <option key={index + 1}>{index + 1}</option>
                  ))}
                </select>
              </label>
              <p>
                Generation depends on service availability. Up to five retrieved
                records support an answer.
              </p>
            </div>
          </details>
        </form>
      </div>
      {active && evidenceOpen && (
        <aside
          className="context-panel panel"
          aria-label="Conversation context"
        >
          <div className="context-toolbar">
            <div className="tabs" role="tablist" aria-label="Contextual panel">
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
            <button
              className="icon-button"
              aria-label="Close evidence panel"
              onClick={() => setEvidenceOpen(false)}
            >
              <X size={17} />
            </button>
          </div>
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
              <h2>Conversation context</h2>
              <p className="fine-print">
                Event context retained for this exchange.
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
                <dt>Retrieval question</dt>
                <dd>{active.retrieval?.query_plan?.query || "Not recorded"}</dd>
              </dl>
            </div>
          )}
        </aside>
      )}
    </div>
  );
}
