import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { workspaceError } from "../workspace-errors.js";

export default function KnowledgeSources() {
  const [data, setData] = useState(null),
    [error, setError] = useState("");

  useEffect(() => {
    const c = new AbortController();
    api
      .sources(c.signal)
      .then(setData)
      .catch((err) => {
        if (!c.signal.aborted) setError(workspaceError(err));
      });
    return () => c.abort();
  }, []);

  useEffect(() => {
    if (data && window.location.hash)
      document
        .getElementById(decodeURIComponent(window.location.hash.slice(1)))
        ?.scrollIntoView({ block: "start" });
  }, [data]);

  return (
    <div className="sources-page">
      <div className="page-intro">
        <h1>Knowledge sources</h1>
        <p>
          Events, policies and participant records used to ground answers and
          verify registrations. External Calendar, Email and Web observations
          are compared against these reference sources.
        </p>
        <Link className="text-button" to="/workspace">
          Ask about this knowledge
        </Link>
      </div>

      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}

      {!data && !error && <p role="status">Loading indexed sources…</p>}

      {data && (
        <>
          <p className="pill">
            {data.total_records} total records · {data.sources.length} source
            documents
          </p>
          <div className="source-documents">
            {data.sources.map((source) => (
              <section
                className="panel"
                id={`source-${source.document_id}`}
                key={source.document_id}
              >
                <header className="source-heading">
                  <h2>{source.document_id}</h2>
                  <span>
                    {source.document_id.split(".").at(-1).toLowerCase()} source
                  </span>
                </header>
                <p>
                  {source.record_count} records · {source.indexed_count}{" "}
                  embeddings stored
                </p>
                <p className="source-index-state">
                  {source.indexed_count === source.record_count
                    ? "All records indexed"
                    : "Indexing incomplete"}{" "}
                  ·{" "}
                  {Array.from(
                    new Set(source.records.map((record) => record.record_type)),
                  ).join(", ")}
                </p>

                {source.records.map((record) => (
                  <details className="source-row" key={record.record_id}>
                    <summary>
                      <strong>{record.record_id}</strong>
                      <span>
                        {record.record_type} ·{" "}
                        {record.indexed ? "Indexed" : "Awaiting embedding"}
                      </span>
                    </summary>
                    <p>{record.content}</p>
                    <code>{record.metadata.source_reference}</code>
                  </details>
                ))}
              </section>
            ))}
          </div>
          {!data.sources.length && <p>No indexed sources are available.</p>}
          <p className="fine-print">
            Document uploads are unavailable. These sources are managed by the
            workspace administrator.
          </p>
        </>
      )}
    </div>
  );
}
