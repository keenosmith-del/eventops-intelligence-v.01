"""Bounded autonomous read/verify workflow. Each transition is durably observed."""

from typing import TypedDict

from app.integrations import tools
from app.services import agent_repository as store
from app.verification import pipeline
from langgraph.graph import END, START, StateGraph


class State(TypedDict, total=False):
    run_id: str
    event_id: str
    limit: int
    sources: dict
    records: list
    results: list
    tool_outcomes: dict
    execution_mode: str


def graph_for(*, adapters=None):
    adapters = adapters or {
        "calendar": tools.read_calendar,
        "email": tools.read_email,
        "web": tools.read_web,
    }
    graph = StateGraph(State)

    def trigger(state):
        store.set_run(state["run_id"], "running")
        store.step(
            state["run_id"],
            "trigger",
            "running",
            inputs={"event_id": state["event_id"], "max_records": state["limit"]},
        )
        store.step(
            state["run_id"],
            "trigger",
            "completed",
            outputs={"mode": state["execution_mode"], "orchestrator": "LangGraph"},
        )
        return {"sources": {}, "tool_outcomes": {}}

    graph.add_node("trigger", trigger)
    for name, adapter in adapters.items():

        def tool_node(state, name=name, adapter=adapter):
            store.step(
                state["run_id"], name, "running", inputs={"max_records": state["limit"]}
            )
            sources = dict(state["sources"])
            outcomes = dict(state["tool_outcomes"])
            try:
                payload = adapter(state["limit"])
                sources[name] = payload
                outcomes[name] = "completed"
                # Store provenance and bounded input summaries; never credentials.
                store.step(
                    state["run_id"],
                    name,
                    "completed",
                    outputs={
                        "source_reference": payload["source_reference"],
                        "bytes_read": len(payload.get("body", "").encode()),
                        "messages_read": len(payload.get("messages", [])),
                    },
                )
            except tools.NotConnected as exc:
                outcomes[name] = "skipped"
                store.step(state["run_id"], name, "skipped", error=str(exc))
            except tools.ToolError as exc:
                outcomes[name] = "failed"
                store.step(state["run_id"], name, "failed", error=str(exc))
            return {"sources": sources, "tool_outcomes": outcomes}

        graph.add_node(name, tool_node)

    def transformation(name, fn):
        def node(state):
            store.step(
                state["run_id"],
                name,
                "running",
                inputs={
                    "input_count": len(state.get("records", [])),
                    "event_id": state["event_id"],
                },
            )
            result = fn(state)
            items = result.get("records", result.get("results", []))
            outputs = {"record_count": len(items), "records": items}
            if name == "extraction":
                outputs["source_counts"] = {
                    source: sum(r["source_type"] == source for r in items)
                    for source in state["sources"]
                }
            if name == "verification":
                outputs.update(pipeline.summary(items))
            store.step(
                state["run_id"],
                name,
                "completed",
                outputs=outputs,
            )
            return result

        return node

    graph.add_node(
        "extraction",
        transformation(
            "extraction",
            lambda s: {"records": pipeline.extract(s["sources"], s["limit"])},
        ),
    )
    graph.add_node(
        "normalization",
        transformation(
            "normalization", lambda s: {"records": pipeline.normalize(s["records"])}
        ),
    )
    graph.add_node(
        "deduplication",
        transformation(
            "deduplication", lambda s: {"records": pipeline.deduplicate(s["records"])}
        ),
    )
    graph.add_node(
        "verification",
        transformation(
            "verification",
            lambda s: {
                "results": pipeline.verify(
                    s["records"], store.reference_records(), s["event_id"]
                )
            },
        ),
    )

    def discrepancies(state):
        store.step(
            state["run_id"],
            "discrepancy",
            "running",
            inputs={"records": len(state["results"])},
        )
        store.step(
            state["run_id"],
            "discrepancy",
            "completed",
            outputs=pipeline.summary(state["results"]),
        )
        return {}

    graph.add_node("discrepancy", discrepancies)

    def persist(state):
        store.step(
            state["run_id"],
            "persistence",
            "running",
            inputs={"records": len(state["results"])},
        )
        outcomes = state["tool_outcomes"]
        status = (
            "completed"
            if all(x == "completed" for x in outcomes.values())
            else "partial"
        )
        if not state["sources"]:
            status = "failed"
        store.set_run(
            state["run_id"],
            status,
            results=state["results"],
            summary={**pipeline.summary(state["results"]), "tools": outcomes, "execution_mode": state["execution_mode"]},
            error="No tool source was available." if status == "failed" else None,
            persistence_outputs={"storage": "PostgreSQL", "record_count": len(state["results"])},
        )
        return {}

    graph.add_node("persistence", persist)
    names = [
        "trigger",
        "calendar",
        "email",
        "web",
        "extraction",
        "normalization",
        "deduplication",
        "verification",
        "discrepancy",
        "persistence",
    ]
    graph.add_edge(START, names[0])
    for first, second in zip(names, names[1:]):
        graph.add_edge(first, second)
    graph.add_edge(names[-1], END)
    return graph.compile()


def execute(run_id, event_id, limit, *, adapters=None, execution_mode=None):
    try:
        graph_for(adapters=adapters).invoke(
            {"run_id": str(run_id), "event_id": event_id, "limit": limit,
             "execution_mode": execution_mode or ("controlled_adapter_test" if adapters is not None else "real_https_read_only")},
            config={"recursion_limit": 16},
        )
    except Exception:
        # No exception text can leak credential-bearing HTTP context.
        store.set_run(
            run_id,
            "failed",
            error="The workflow was interrupted by an extraction, validation or persistence error. Review the step log.",
        )
        current = store.get_run(run_id)
        if current:
            for node in current["steps"]:
                if node["status"] == "running":
                    store.step(
                        run_id,
                        node["node_id"],
                        "failed",
                        error="Step failed; source format or persistence could not be processed.",
                    )
                elif node["status"] == "pending":
                    store.step(
                        run_id,
                        node["node_id"],
                        "skipped",
                        error="Skipped after workflow failure.",
                    )
