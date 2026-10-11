"""Bounded API smoke probe. Never requests Gemini generation or prints tokens.

Run with backend/.venv/bin/python scripts/smoke-production.py --api URL --frontend URL.
Add --agent only for one intentional live read-only agent execution.
"""
import argparse
import csv
import io
import sys
import time
from urllib.parse import urlsplit

import httpx


def check(condition, label):
    if not condition:
        raise RuntimeError(label)
    print("PASS", label)


def probe(api, frontend, agent=False, require_email=False):
    with httpx.Client(base_url=api, timeout=90, follow_redirects=False) as client:
        check(client.get("/health").status_code == 200, "backend health")
        check(client.get("/ready").status_code == 200, "database and source readiness")
        cors = client.options("/api/demo/session", headers={
            "Origin": frontend, "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-demo-session",
        })
        check(cors.headers.get("access-control-allow-origin") == frontend, "exact frontend CORS")
        check(client.get("/api/conversations").status_code == 401, "session required")
        session = client.post("/api/demo/session", json={})
        check(session.status_code == 200 and session.json()["demo_mode"], "real reviewer session")
        client.headers["X-Demo-Session"] = session.json()["session_token"]
        sources = client.get("/api/knowledge/sources").json()
        check(sources["total_records"] == 19 and len(sources["sources"]) == 3
              and sum(s["indexed_count"] for s in sources["sources"]) == 19,
              "three documents / 19 records / 19 embeddings")
        conversation = client.post("/api/conversations", json={"title": "Synthetic deployment smoke"})
        check(conversation.status_code == 201, "conversation creation")
        path = "/api/conversations/" + conversation.json()["id"]
        for question in ["What time does check-in close for EVT-101?", "What time does its check-in close?"]:
            response = client.post(path + "/messages", json={
                "question": question, "top_k": 5, "generate_answer": False,
            })
            check(response.status_code == 200, "RAG question or contextual follow-up")
        saved = client.get(path)
        check(saved.status_code == 200 and "POL-003" in saved.text, "persisted source citation POL-003")
        with httpx.Client(base_url=api, headers=dict(client.headers), timeout=90) as fresh:
            check(fresh.get(path).json() == saved.json(), "conversation restored through fresh connection")
        other = client.post("/api/demo/session", json={}).json()["session_token"]
        check(client.get(path, headers={"X-Demo-Session": other}).status_code == 404,
              "second reviewer cannot access first conversation")
        if agent:
            run = client.post("/api/agents/runs", json={"event_id": "EVT-101", "max_records": 10})
            check(run.status_code == 202, "LangGraph run admitted")
            run_path = "/api/agents/runs/" + run.json()["id"]
            deadline = time.monotonic() + 180
            while True:
                response = client.get(run_path)
                check(response.status_code == 200, "saved execution accessible")
                result = response.json()
                if result["status"] in {"completed", "partial", "failed"}:
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError("Agent polling deadline exceeded; inspect history before starting another run")
                time.sleep(2)
            check(result["status"] in {"completed", "partial"}, "agent terminal outcome")
            outcomes = result["summary"]["tools"]
            for name in ["calendar", "web"] + (["email"] if require_email else []):
                check(outcomes.get(name) == "completed", name + " actual remote read")
            print("Email outcome:", outcomes.get("email", "unknown"))
            exported = client.get(run_path + "/export.csv")
            check(exported.status_code == 200, "CSV export")
            rows = list(csv.DictReader(io.StringIO(exported.text.lstrip("\ufeff"))))
            check(len(rows) == len(result["results"]), "CSV rows match persisted results")
            check(client.get(run_path).json()["results"] == result["results"], "saved verification restored")
            check(any(x["id"] == run.json()["id"] for x in client.get("/api/agents/runs").json()), "execution history")
            print("Execution ID:", run.json()["id"])
        print("Conversation ID:", conversation.json()["id"])
        print("Keep the reviewer browser tab for restart/redeploy persistence checks; this probe does not prove redeploy survival.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True)
    parser.add_argument("--frontend", required=True)
    parser.add_argument("--agent", action="store_true")
    parser.add_argument("--require-email", action="store_true")
    args = parser.parse_args()
    for value in [args.api, args.frontend]:
        url = urlsplit(value)
        if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in {"", "/"}:
            parser.error("Use public HTTPS origins without paths or credentials.")
    if args.require_email and not args.agent:
        parser.error("--require-email requires --agent")
    try:
        probe(args.api.rstrip("/"), args.frontend.rstrip("/"), args.agent, args.require_email)
    except Exception:
        print("FAIL: Smoke verification stopped. Inspect provider logs and saved execution; no provider exception or credentials are printed.", file=sys.stderr)
        sys.exit(1)
