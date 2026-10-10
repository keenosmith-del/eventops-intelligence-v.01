import { useEffect, useState } from "react";
import { api } from "../api.js";
export default function KnowledgeSources() {
  const [data, setData] = useState(null),
    [error, setError] = useState("");
  useEffect(() => {
    const c = new AbortController();
    api
      .sources(c.signal)
      .then(setData)
      .catch((err) => {
        if (!c.signal.aborted) setError(err.message);
      });
    return () => c.abort();
  }, []);
  return (
    <div className="sources-page">
      <div className="page-intro">
        <p className="eyebrow">05 / Knowledge Sources</p>
        <h1>A traceable foundation.</h1>
        <p>
          Live indexed records from PostgreSQL. Each source retains its original
          identifiers and provenance.
        </p>
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
              <section className="panel" key={source.document_id}>
                <h2>{source.document_id}</h2>
                <p>
                  {source.record_count} records · {source.indexed_count}{" "}
                  embeddings stored
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
                    <dl>
                      <dt>Source SHA-256</dt>
                      <dd>{record.metadata.source_sha256}</dd>
                    </dl>
                  </details>
                ))}
              </section>
            ))}
          </div>
          <p className="fine-print">
            There is no upload action: no HTTP ingestion endpoint is
            implemented. New sources must be validated and indexed server-side.
          </p>
        </>
      )}
    </div>
  );
}
