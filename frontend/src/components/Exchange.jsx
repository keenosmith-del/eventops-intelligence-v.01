import Evidence from "./Evidence.jsx";

const statusText = {
  not_requested: "Evidence only · AI generation was not requested.",
  generated: "AI answer generated · review its supporting sources below.",
  unavailable:
    "AI answer unavailable · generation is disabled, unconfigured or failed. Retrieved evidence is still available.",
  insufficient_evidence:
    "Insufficient evidence · the backend could not produce a supported AI answer.",
};

export function groupExchanges(messages) {
  const groups = [];
  for (const message of messages) {
    if (message.kind === "question") groups.push({ question: message });
    else if (groups.length && message.kind === "retrieval")
      groups.at(-1).retrieval = message;
    else if (groups.length && message.kind === "answer")
      groups.at(-1).answer = message;
  }
  return groups;
}

export default function Exchange({
  exchange,
  status,
  compact = false,
  onInspect,
}) {
  const { question, retrieval, answer } = exchange;
  const context = retrieval?.query_plan?.context_resolution;
  status = retrieval?.query_plan?.generation_status || status;
  return (
    <article className="exchange">
      <div className="question">
        <div className="eyebrow">
          Your question{" "}
          <time>
            {new Date(question.created_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </time>
        </div>
        <h2>{question.content}</h2>
      </div>
      <div className="result">
        <div className="section-label">
          <img className="assistant-avatar" src="/mascot-head.png" alt="EventOps assistant" />
          <span>Retrieved evidence</span>
          <span className="pill">
            {retrieval?.evidence?.length || 0}{" "}
            {retrieval?.evidence?.length === 1 ? "source" : "sources"}
          </span>
        </div>
        {context?.used_context && (
          <p className="context-note">
            Context carried forward: {context.inherited_event_id}. Your original
            question is preserved above.
          </p>
        )}
        {retrieval && (
          <>
            {compact ? (
              <button className="text-button" onClick={onInspect}>
                Inspect {retrieval.evidence.length}{" "}
                {retrieval.evidence.length === 1
                  ? "source record"
                  : "source records"}
              </button>
            ) : (
              <Evidence records={retrieval.evidence} messageId={retrieval.id} />
            )}

          </>
        )}
        <p
          className={`generation-note ${status === "unavailable" || status === "insufficient_evidence" ? "attention" : ""}`}
        >
          {statusText[status] ||
            (answer
              ? statusText.generated
              : "Evidence only · This older exchange has no saved generation outcome.")}
        </p>
        {answer && (
          <section className="answer">
            <div className="eyebrow">
              AI-generated answer{" "}
              <span>{answer.query_plan?.generation?.model}</span>
            </div>
            <p>{answer.content}</p>
            <div className="citations" aria-label="Answer citations">
              {answer.evidence.map((citation, index) => {
                const evidenceIndex =
                  retrieval?.evidence.findIndex(
                    (item) =>
                      item.record_id === citation.record_id &&
                      item.source_reference === citation.source_reference,
                  ) ?? -1;
                return (
                  <div key={`${citation.record_id}-${index}`}>
                    {evidenceIndex >= 0 ? (
                      <a
                        href={`#evidence-${retrieval.id}-${evidenceIndex}`}
                        onClick={(event) => {
                          if (compact) {
                            event.preventDefault();
                            onInspect?.();
                            requestAnimationFrame(() => {
                              const panel = document.getElementById(
                                `evidence-${retrieval.id}-${evidenceIndex}`,
                              );
                              if (panel) {
                                panel.open = true;
                                panel.scrollIntoView({ block: "nearest" });
                              }
                            });
                            return;
                          }
                          const element = document.getElementById(
                            `evidence-${retrieval.id}-${evidenceIndex}`,
                          );
                          if (element) element.open = true;
                        }}
                      >
                        {citation.record_id}
                      </a>
                    ) : (
                      <strong>{citation.record_id}</strong>
                    )}
                    <span>{citation.source_reference}</span>
                  </div>
                );
              })}
            </div>
            <p className="fine-print">
              Citations are checked against retrieved records. Review the source
              text to assess the answer.
            </p>
          </section>
        )}
      </div>
    </article>
  );
}
