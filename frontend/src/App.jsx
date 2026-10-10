import { useEffect, useState } from "react";
import {
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import { api } from "./api.js";
import KnowledgeAssistant from "./components/KnowledgeAssistant.jsx";
import AgentWorkspace from "./components/AgentWorkspace.jsx";
import KnowledgeSources from "./components/KnowledgeSources.jsx";
import "./workspace.css";

function KnowledgeRoute() {
  const { id } = useParams();
  return <KnowledgeAssistant id={id} />;
}
function AgentRoute({ view }) {
  const { runId } = useParams();
  return <AgentWorkspace runId={runId} view={view} />;
}

function SignIn({ onEnter }) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function enter() {
    setBusy(true);
    setError("");
    try {
      const result = await api.startDemo();
      sessionStorage.setItem("eventops-demo-token", result.session_token);
      onEnter(result.session_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="entry-screen">
      <div className="entry-brand">
        <span className="brand-symbol">
          e<span>o</span>
        </span>
        EventOps Intelligence <span className="pill">v.01</span>
      </div>
      <section>
        <p className="eyebrow">Inference Group / AI Engineering</p>
        <h1>
          Operational clarity.
          <br />
          From evidence
          <br />
          to action.
        </h1>
        <p>
          A unified workspace for source-grounded answers, observable tooling
          and verified event operations.
        </p>
        <button className="primary" disabled={busy} onClick={enter}>
          {busy ? "Opening workspace…" : "Continue as reviewer"}
        </button>
        {error && (
          <p className="notice error" role="alert">
            {error}
          </p>
        )}
        <p className="fine-print">
          Demonstration access, not account authentication. No personal
          credentials required. Use synthetic assessment data only.
        </p>
      </section>
      <footer>
        Structured knowledge. Auditable decisions. / EventOps Intelligence v.01
      </footer>
    </main>
  );
}
export default function App() {
  const [token, setToken] = useState(() =>
      sessionStorage.getItem("eventops-demo-token"),
    ),
    [collapsed, setCollapsed] = useState(false),
    [health, setHealth] = useState("checking");
  const navigate = useNavigate(),
    location = useLocation();
  useEffect(() => {
    const expired = () => {
      sessionStorage.removeItem("eventops-demo-token");
      setToken(null);
      navigate("/signin");
    };
    window.addEventListener("eventops-session-expired", expired);
    return () =>
      window.removeEventListener("eventops-session-expired", expired);
  }, [navigate]);
  async function check() {
    setHealth("checking");
    try {
      const result = await api.health();
      setHealth(result.status === "ok" ? "online" : "offline");
    } catch {
      setHealth("offline");
    }
  }
  useEffect(() => {
    check();
  }, []);
  if (!token || location.pathname === "/signin")
    return (
      <SignIn
        onEnter={(value) => {
          setToken(value);
          navigate(location.pathname === "/signin" ? "/" : location.pathname);
        }}
      />
    );
  const nav = [
    ["/", "Knowledge Assistant", "01"],
    ["/agents", "Agent Workspace", "02"],
    ["/verification", "Verification Results", "03"],
    ["/history", "Execution History", "04"],
    ["/sources", "Knowledge Sources", "05"],
  ];
  return (
    <div className={`app-shell ${collapsed ? "is-collapsed" : ""}`}>
      <a className="skip-link" href="#workspace">
        Skip to workspace
      </a>
      <aside className="sidebar unified-sidebar">
        <div className="brand">
          <span className="brand-symbol" aria-hidden="true">
            e<span>o</span>
          </span>
          <div>
            EventOps<span>Intelligence / v.01</span>
          </div>
        </div>
        <button
          className="collapse-control"
          onClick={() => setCollapsed((value) => !value)}
          aria-expanded={!collapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? "Expand" : "Collapse"}
        </button>
        <div className="nav-label">Operations workspace</div>
        <nav aria-label="Main navigation">
          {nav.map(([path, label, number]) => (
            <NavLink
              key={path}
              to={path}
              end={path === "/" || path === "/agents"}
              className={({ isActive }) =>
                `nav-item ${isActive || (path === "/" && location.pathname.startsWith("/conversations/")) || (path === "/agents" && location.pathname.startsWith("/agents/runs/")) ? "active" : ""}`
              }
            >
              <span aria-hidden="true">{number}</span>
              <span className="nav-text">{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="reviewer-card">
          <span className="pill">Reviewer demo</span>
          <p>
            No account authentication.
            <br />
            Synthetic assessment data.
          </p>
          <button
            className="text-button"
            onClick={() => {
              sessionStorage.removeItem("eventops-demo-token");
              setToken(null);
              navigate("/signin");
            }}
          >
            Leave reviewer session
          </button>
        </div>
        <div className="sidebar-footer">
          <span className={`connection-dot ${health}`} />
          <span>
            {health === "online"
              ? "API process online"
              : health === "checking"
                ? "Checking API…"
                : "API unreachable"}
          </span>
          <button
            className="text-button"
            onClick={check}
            aria-label="Recheck backend connection"
          >
            Refresh
          </button>
        </div>
      </aside>
      <main id="workspace" className="main" tabIndex={-1}>
        <header className="topbar">
          <span>Evidence to operations.</span>
          <span className="edition">ASSESSMENT / v.01</span>
        </header>
        {health === "offline" && (
          <div className="notice shell-notice" role="status">
            The backend is unreachable. Check the configured API address and
            retry the connection.
          </div>
        )}
        <div className="unified-content">
          <Routes>
            <Route path="/" element={<KnowledgeRoute />} />
            <Route path="/conversations/:id" element={<KnowledgeRoute />} />
            <Route path="/agents" element={<AgentRoute view="workspace" />} />
            <Route
              path="/agents/runs/:runId"
              element={<AgentRoute view="workspace" />}
            />
            <Route
              path="/verification"
              element={<AgentRoute view="results" />}
            />
            <Route
              path="/verification/:runId"
              element={<AgentRoute view="results" />}
            />
            <Route path="/history" element={<AgentRoute view="history" />} />
            <Route
              path="/history/:runId"
              element={<AgentRoute view="history" />}
            />
            <Route path="/sources" element={<KnowledgeSources />} />
            <Route
              path="*"
              element={
                <section className="panel">
                  <h1>Page not found.</h1>
                  <NavLink to="/">Open Knowledge Assistant</NavLink>
                </section>
              }
            />
          </Routes>
          <footer className="workspace-footer">
            <span>Grounded in sources. Built for operations.</span>
            <span>EventOps Intelligence v.01</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
