import { useEffect, useState } from "react";
import { NavLink, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";
import { ArrowRight, Brain } from "lucide-react";
import { api } from "./api.js";
import KnowledgeAssistant from "./components/KnowledgeAssistant.jsx";
import AgentWorkspace from "./components/AgentWorkspace.jsx";
import KnowledgeSources from "./components/KnowledgeSources.jsx";
import WorkspaceSidebar, { navigation } from "./components/WorkspaceSidebar.jsx";
import { Landing, SignIn } from "./components/Introduction.jsx";
import "./workspace.css";
import "./workspace-redesign.css";

function KnowledgeRoute() {
  const { id } = useParams();
  const location = useLocation();
  return <KnowledgeAssistant key={id || location.state?.reset || "new"} id={id} />;
}
function AgentRoute({ view }) {
  const { runId } = useParams();
  return <AgentWorkspace runId={runId} view={view} />;
}

export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem("eventops-demo-token"));
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("eventops-sidebar-collapsed") === "true");
  const [drawer, setDrawer] = useState(false);
  const [mobile, setMobile] = useState(() => window.matchMedia("(max-width: 760px)").matches);
  const [health, setHealth] = useState("checking");
  const navigate = useNavigate(), location = useLocation();
  useEffect(() => {
    const media = window.matchMedia("(max-width: 760px)");
    const update = () => { setMobile(media.matches); setDrawer(false); };
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  useEffect(() => { setDrawer(false); }, [location.pathname]);
  useEffect(() => {
    const expired = () => {
      sessionStorage.removeItem("eventops-demo-token");
      setToken(null);
      navigate("/signin");
    };
    window.addEventListener("eventops-session-expired", expired);
    return () => window.removeEventListener("eventops-session-expired", expired);
  }, [navigate]);
  async function check() {
    setHealth("checking");
    try { const result = await api.health(); setHealth(result.status === "ok" ? "online" : "offline"); }
    catch { setHealth("offline"); }
  }
  useEffect(() => { check(); }, []);
  if (location.pathname === "/") return <Landing />;
  if (!token || location.pathname === "/signin") return <SignIn onEnter={value => {
    setToken(value);
    navigate(location.pathname === "/signin" ? "/workspace" : location.pathname);
  }} />;
  const knowledge = location.pathname === "/workspace" || location.pathname.startsWith("/conversations/");
  const pageName = knowledge ? "Knowledge assistant" : navigation.find(([path]) => location.pathname.startsWith(path))?.[1] || "Workspace";
  function toggleSidebar() {
    if (mobile) { setDrawer(value => !value); return; }
    setCollapsed(value => { localStorage.setItem("eventops-sidebar-collapsed", String(!value)); return !value; });
  }
  return (
    <div className={`app-shell ${collapsed && !mobile ? "is-collapsed" : ""} ${drawer ? "drawer-open" : ""}`}>
      <a className="skip-link" href="#workspace">Skip to workspace</a>
      {mobile && drawer && <button className="drawer-backdrop" aria-label="Close navigation" onClick={() => setDrawer(false)} />}
      <WorkspaceSidebar token={token} knowledge={knowledge} collapsed={collapsed && !mobile} mobile={mobile} drawer={drawer} close={() => setDrawer(false)} toggle={toggleSidebar} health={health} check={check} leave={() => {
        sessionStorage.removeItem("eventops-demo-token"); setToken(null); navigate("/signin");
      }} />
      <main id="workspace" className="main" tabIndex={-1} inert={mobile && drawer}>
        <header className="topbar">
          <button className="mobile-nav-toggle icon-button" aria-label="Open navigation" aria-expanded={drawer} onClick={() => setDrawer(true)}><ArrowRight size={20} aria-hidden="true" /></button>
          <span>{pageName}</span>
        </header>
        {health === "offline" && <div className="notice shell-notice" role="status">Connection unavailable. <button onClick={check}>Retry connection</button></div>}
        <div className="unified-content">
          <Routes>
            <Route path="/workspace" element={<KnowledgeRoute />} />
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
                  <NavLink to="/workspace">Open Knowledge Assistant</NavLink>
                </section>
              }
            />
          </Routes>
        </div>
        <footer className="workspace-footer" role="contentinfo" aria-label="Application credits">
          <span><Brain size={12} strokeWidth={1.3} aria-hidden="true" />Designed &amp; Engineering by Keeno Smith</span>
          <span>October 2026 (c) EventOps Intelligence v.01</span>
        </footer>
      </main>
    </div>
  );
}
