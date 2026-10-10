export default function Evidence({ records = [], messageId }) {
  if (!records.length)
    return (
      <p className="muted">
        No source records matched this question. Try a specific event ID or a
        different question.
      </p>
    );
  return (
    <div className="evidence-list">
      {records.map((record, index) => (
        <details
          className="evidence"
          key={`${record.record_id}-${index}`}
          id={`evidence-${messageId}-${index}`}
          open={index === 0}
        >
          <summary>
            <span className="evidence-title">
              <strong>{record.record_id}</strong>
              <span>
                {record.record_type}
                {record.event_id ? ` · ${record.event_id}` : ""}
              </span>
            </span>
            <span
              className="score"
              title="Cosine similarity; relevance, not confidence"
            >
              {Number.isFinite(record.score) ? record.score.toFixed(3) : "—"}{" "}
              <span>similarity</span>
            </span>
          </summary>
          <div className="evidence-body">
            <p className="source-content">{record.content}</p>
            <dl>
              <div>
                <dt>Source</dt>
                <dd>{record.source_reference}</dd>
              </div>
              <div>
                <dt>Document</dt>
                <dd>{record.document_id}</dd>
              </div>
            </dl>

          </div>
        </details>
      ))}
    </div>
  );
}
