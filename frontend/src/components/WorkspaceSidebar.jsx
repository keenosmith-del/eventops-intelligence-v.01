import { useEffect, useRef, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Database,
  History,
  ListChecks,
  MessageCircle,
  Plus,
  Settings,
  Workflow,
} from "lucide-react";
import { api, UUID_PATTERN } from "../api.js";
import { workspaceError } from "../workspace-errors.js";

export const navigation = [
  ["/workspace", "Knowledge assistant", MessageCircle],
  ["/agents", "Agent workspace", Workflow],
  ["/verification", "Verification results", ListChecks],
  ["/history", "Execution history", History],
  ["/sources", "Knowledge sources", Database],
];

export default function WorkspaceSidebar({
  token,
  knowledge,
  collapsed,
  mobile,
  drawer,
  close,
  toggle,
  health,
  check,
  leave,
}) {
  const [history, setHistory] = useState([]),
    [historyError, setHistoryError] = useState("");
  const [settings, setSettings] = useState(false),
    [uuid, setUuid] = useState(""),
    [uuidError, setUuidError] = useState("");
  const aside = useRef(null),
    settingsControl = useRef(null);
  const [tooltip, setTooltip] = useState(null);
  const location = useLocation(),
    navigate = useNavigate();
  useEffect(() => {
    if (!settings) return;
    function dismiss(event) {
      if (event.type === "keydown" && event.key === "Escape")
        setSettings(false);
      if (
        event.type === "pointerdown" &&
        !settingsControl.current?.contains(event.target)
      )
        setSettings(false);
    }
    document.addEventListener("pointerdown", dismiss);
    document.addEventListener("keydown", dismiss);
    return () => {
      document.removeEventListener("pointerdown", dismiss);
      document.removeEventListener("keydown", dismiss);
    };
  }, [settings]);
  useEffect(() => {
    setSettings(false);
  }, [location.key]);
  useEffect(() => {
    setTooltip(null);
  }, [location.key, collapsed, drawer]);
  useEffect(() => {
    const dismiss = () => setTooltip(null);
    const keydown = (event) => {
      if (event.key === "Escape") dismiss();
    };
    document.addEventListener("pointerdown", dismiss, true);
    document.addEventListener("click", dismiss, true);
    document.addEventListener("keydown", keydown);
    window.addEventListener("blur", dismiss);
    return () => {
      document.removeEventListener("pointerdown", dismiss, true);
      document.removeEventListener("click", dismiss, true);
      document.removeEventListener("keydown", keydown);
      window.removeEventListener("blur", dismiss);
    };
  }, []);
  function tooltipEvents(id) {
    return {
      onPointerEnter: (event) => {
        if (collapsed && event.pointerType !== "touch") setTooltip(id);
      },
      onPointerLeave: () => setTooltip(null),
      onFocus: (event) => {
        if (collapsed && event.currentTarget.matches(":focus-visible"))
          setTooltip(id);
      },
      onBlur: () => setTooltip(null),
      onClickCapture: () => setTooltip(null),
    };
  }
  const tooltipClass = (id) =>
    `rail-tooltip${tooltip === id ? " is-visible" : ""}`;
  useEffect(() => {
    if (!knowledge) return;
    const controller = new AbortController();
    let sequence = 0;
    async function refresh() {
      const current = ++sequence;
      try {
        const items = await api.list(controller.signal);
        const titled = await Promise.all(
          items.map(async (item) => {
            if (item.title) return item;
            const detail = await api.detail(item.id, controller.signal);
            return {
              ...item,
              title:
                detail.messages.find((message) => message.kind === "question")
                  ?.content || "Empty chat",
            };
          }),
        );
        if (!controller.signal.aborted && current === sequence) {
          setHistory(titled);
          setHistoryError("");
        }
      } catch (error) {
        if (!controller.signal.aborted && current === sequence)
          setHistoryError(workspaceError(error));
      }
    }
    refresh();
    window.addEventListener("eventops-history-updated", refresh);
    return () => {
      controller.abort();
      window.removeEventListener("eventops-history-updated", refresh);
    };
  }, [token, knowledge]);
  useEffect(() => {
    if (!mobile || !drawer) return;
    const previous = document.activeElement;
    const oldOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    aside.current.querySelector("button")?.focus();
    function keydown(event) {
      if (event.key === "Escape") close();
      if (event.key === "Tab") {
        const elements = [
          ...aside.current.querySelectorAll(
            "a[href], button:not(:disabled), input, summary",
          ),
        ].filter((element) => element.getClientRects().length);
        const first = elements[0],
          last = elements.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    }
    document.addEventListener("keydown", keydown);
    return () => {
      document.removeEventListener("keydown", keydown);
      document.body.style.overflow = oldOverflow;
      previous?.focus();
    };
  }, [mobile, drawer]);
  function openUuid(event) {
    event.preventDefault();
    if (!UUID_PATTERN.test(uuid.trim())) {
      setUuidError("Enter a valid conversation UUID.");
      return;
    }
    navigate(`/conversations/${uuid.trim()}`);
    setUuid("");
    setUuidError("");
    close();
  }
  return (
    <aside
      ref={aside}
      className="sidebar unified-sidebar"
      aria-label="Workspace navigation"
      role={mobile ? "dialog" : undefined}
      aria-modal={mobile && drawer ? true : undefined}
      aria-hidden={mobile && !drawer}
      inert={mobile && !drawer}
    >
      <div className="sidebar-identity">
        <NavLink
          to="/workspace"
          aria-label="Return to assistant"
          onClick={close}
        >
          <img
            className="sidebar-avatar"
            src="/mascot-head.png"
            alt="EventOps"
          />
        </NavLink>
        {!collapsed && (
          <div className="sidebar-wordmark">
            EventOps<span>Intelligence</span>
          </div>
        )}
      </div>
      <button
        {...tooltipEvents("expand-tooltip")}
        className="collapse-control icon-button"
        onClick={toggle}
        aria-expanded={mobile ? drawer : !collapsed}
        aria-label={
          mobile
            ? "Close navigation"
            : collapsed
              ? "Expand sidebar"
              : "Collapse sidebar"
        }
        aria-describedby={collapsed ? "expand-tooltip" : undefined}
      >
        {collapsed ? (
          <ArrowRight size={19} aria-hidden="true" />
        ) : (
          <ArrowLeft size={19} aria-hidden="true" />
        )}
        {collapsed && (
          <span
            className={tooltipClass("expand-tooltip")}
            role="tooltip"
            id="expand-tooltip"
          >
            Expand sidebar
          </span>
        )}
      </button>
      <nav aria-label="Main navigation">
        {navigation.map(([path, label, Icon], index) => (
          <NavLink
            {...tooltipEvents(`nav-tooltip-${index}`)}
            key={path}
            to={path}
            end={path === "/workspace" || path === "/agents"}
            aria-label={label}
            aria-describedby={collapsed ? `nav-tooltip-${index}` : undefined}
            className={({ isActive }) =>
              `nav-item ${isActive || (path === "/workspace" && knowledge) || (path === "/agents" && location.pathname.startsWith("/agents/runs/")) ? "active" : ""}`
            }
          >
            <Icon size={18} strokeWidth={1.5} aria-hidden="true" />
            {!collapsed && <span>{label}</span>}
            {collapsed && (
              <span
                className={tooltipClass(`nav-tooltip-${index}`)}
                role="tooltip"
                id={`nav-tooltip-${index}`}
              >
                {label}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
      {knowledge && (
        <div className="sidebar-chats">
          <button
            {...tooltipEvents("new-chat-tooltip")}
            className="new-chat"
            onClick={() => {
              navigate("/workspace", { state: { reset: Date.now() } });
              window.dispatchEvent(new Event("eventops-new-chat"));
              close();
            }}
            aria-label="New chat"
            aria-describedby={collapsed ? "new-chat-tooltip" : undefined}
          >
            <Plus size={18} strokeWidth={1.5} aria-hidden="true" />
            {!collapsed && "New chat"}
            {collapsed && (
              <span
                className={tooltipClass("new-chat-tooltip")}
                role="tooltip"
                id="new-chat-tooltip"
              >
                New chat
              </span>
            )}
          </button>
          {!collapsed && (
            <>
              <div
                className="sidebar-history"
                aria-label="Recent conversations"
              >
                {historyError ? (
                  <p role="alert">
                    Could not load chats.{" "}
                    <button
                      onClick={() =>
                        window.dispatchEvent(
                          new Event("eventops-history-updated"),
                        )
                      }
                    >
                      Retry
                    </button>
                  </p>
                ) : !history.length ? (
                  <p className="sidebar-empty">No conversations yet.</p>
                ) : (
                  history.map((item) => (
                    <NavLink
                      key={item.id}
                      to={`/conversations/${item.id}`}
                      className={({ isActive }) =>
                        `chat-history-item ${isActive ? "selected" : ""}`
                      }
                      title={item.title}
                    >
                      {item.title}
                    </NavLink>
                  ))
                )}
              </div>
              <details className="uuid-disclosure">
                <summary>Open saved chat</summary>
                <form onSubmit={openUuid}>
                  <label htmlFor="restore-id">Open by UUID</label>
                  <input
                    id="restore-id"
                    value={uuid}
                    onChange={(event) => setUuid(event.target.value)}
                    placeholder="Conversation UUID"
                    required
                  />
                  <button>Open conversation by UUID</button>
                  {uuidError && <p role="alert">{uuidError}</p>}
                </form>
              </details>
            </>
          )}
        </div>
      )}
      <div className="sidebar-bottom">
        <div ref={settingsControl}>
          <button
            {...tooltipEvents("settings-tooltip")}
            className="sidebar-setting"
            aria-label="Settings"
            aria-expanded={settings}
            aria-describedby={collapsed ? "settings-tooltip" : undefined}
            onClick={() => setSettings((value) => !value)}
          >
            <Settings size={18} strokeWidth={1.5} aria-hidden="true" />
            {!collapsed && "Settings"}
            {collapsed && (
              <span
                className={tooltipClass("settings-tooltip")}
                role="tooltip"
                id="settings-tooltip"
              >
                Settings
              </span>
            )}
          </button>
          {settings && (
            <section className="workspace-settings" aria-label="Settings">
              <p>EventOps Intelligence v.01</p>
              <p>Reviewer demonstration access</p>
              <p role="status">
                {health === "online"
                  ? "Service available"
                  : health === "checking"
                    ? "Checking connection…"
                    : "Connection unavailable"}
              </p>
              {health === "offline" && (
                <button onClick={check}>Retry connection</button>
              )}
            </section>
          )}
        </div>
        <button
          {...tooltipEvents("leave-tooltip")}
          className="sidebar-setting"
          aria-label="Leave reviewer session"
          aria-describedby={collapsed ? "leave-tooltip" : undefined}
          onClick={leave}
        >
          <ArrowLeft size={18} strokeWidth={1.5} aria-hidden="true" />
          {!collapsed && "Leave session"}
          {collapsed && (
            <span
              className={tooltipClass("leave-tooltip")}
              role="tooltip"
              id="leave-tooltip"
            >
              Leave session
            </span>
          )}
        </button>
      </div>
    </aside>
  );
}
