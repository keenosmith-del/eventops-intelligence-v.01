import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { api } from "../api.js";
import ApplicationFooter from "./ApplicationFooter.jsx";
import "../introduction.css";

function useIntroTransition() {
  const [leaving, setLeaving] = useState(false);
  const timer = useRef(null);
  const navigate = useNavigate();
  useEffect(() => () => clearTimeout(timer.current), []);
  function transition(event, to) {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (leaving) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      navigate(to);
      return;
    }
    setLeaving(true);
    timer.current = setTimeout(() => navigate(to), 180);
  }
  return { leaving, transition };
}

export function Landing() {
  const { leaving, transition } = useIntroTransition();
  return (
    <main className={`intro-screen intro-landing ${leaving ? "intro-leaving" : ""}`}>
      <section className="intro-hero" aria-labelledby="landing-title">
        <img className="intro-head intro-arrive" src="/mascot-head.png" alt="EventOps mascot" width="1280" height="1280" fetchPriority="high" />
        <h1 id="landing-title" className="intro-title intro-arrive">EventOps<br />Intelligence</h1>
        <p className="intro-description intro-arrive">An intelligent workspace for knowledge retrieval, agent orchestration and operational verification.</p>
        <Link className="intro-action intro-start intro-arrive" to="/signin" onClick={(event) => transition(event, "/signin")}>Start <ArrowRight size={16} strokeWidth={1.4} aria-hidden="true" /></Link>
      </section>
      <ApplicationFooter />
    </main>
  );
}

export function SignIn({ onEnter }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const { leaving, transition } = useIntroTransition();
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
    <main className={`intro-screen intro-signin ${leaving ? "intro-leaving" : ""}`}>
      <Link className="intro-back" to="/" onClick={(event) => transition(event, "/")}><ArrowLeft size={16} strokeWidth={1.4} aria-hidden="true" /> Back</Link>
      <div className="intro-entry-layout">
        <div className="intro-character intro-arrive">
          <img src="/mascot-full-length.png" alt="EventOps mascot welcoming you to the workspace" width="1086" height="1448" fetchPriority="high" />
        </div>
        <section className="intro-entry-panel intro-arrive" aria-labelledby="signin-title">
          <h1 id="signin-title">Welcome to EventOps</h1>
          <p className="intro-entry-description">Enter the workspace to explore grounded knowledge, automated workflows and verified operational data.</p>
          <button className="intro-action" disabled={busy} aria-busy={busy} onClick={enter}>{busy ? "Opening workspace…" : "Enter workspace"}<ArrowRight size={18} strokeWidth={1.4} aria-hidden="true" /></button>
          {busy && <p className="intro-access-note" role="status">The service may take up to 90 seconds to wake up. Please wait.</p>}
          {error && <p className="intro-error" role="alert">{error} Try Enter workspace again.</p>}
          <p className="intro-access-note">Reviewer demonstration access<span className="intro-account-note">No account required for demonstration access.</span></p>
        </section>
      </div>
      <ApplicationFooter />
    </main>
  );
}
