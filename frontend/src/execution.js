// Recorded timestamps are the only replay clock. No backend operation is started here.
export const terminal = (status) =>
  ["completed", "partial", "failed"].includes(status);

const timestamp = (value) => (value ? Date.parse(value) : NaN);

// Replay bounds are the earliest and latest timestamps of all non-export steps, or null if the
// run is not terminal or has no timestamps. The end bound is the earliest of the latest step
// timestamp and the run's finished_at timestamp, if present.
export function replayBounds(run) {
  const times = (run?.steps || [])
    .filter((step) => step.node_id !== "export")
    .flatMap((step) => [
      timestamp(step.started_at),
      timestamp(step.finished_at),
    ])
    .filter(Number.isFinite);

  if (!terminal(run?.status) || times.length < 2) return null;

  const start = Math.min(...times);

  const finished = timestamp(run.finished_at);

  const end = Number.isFinite(finished)
    ? Math.min(finished, Math.max(...times))
    : Math.max(...times);

  return end > start ? { start, end, duration: end - start } : null;
}

// Replay steps at a given timestamp. Steps that have finished before the timestamp are returned
// unchanged. Steps that have started but not finished are returned as running. Steps that have
// not started are returned as pending. The export step is always returned as outside_replay.
// Terminal steps without timestamps are returned as time_not_recorded.
export function replaySteps(steps, at) {
  return steps.map((step) => {
    if (step.node_id === "export")
      return {
        ...step,
        status: "outside_replay",
        inputs: {},
        outputs: {},
        error: null,
        started_at: null,
        finished_at: null,
      };

    const start = timestamp(step.started_at),
      finish = timestamp(step.finished_at);

    if (Number.isFinite(finish) && at >= finish) return step;

    if (Number.isFinite(start) && at >= start)
      return {
        ...step,
        status: "running",
        outputs: {},
        error: null,
        finished_at: null,
      };

    // A terminal step without timestamps cannot be reconstructed. Keep it explicit.
    if (
      !Number.isFinite(start) &&
      !Number.isFinite(finish) &&
      step.status !== "pending"
    )
      return { ...step, status: "time_not_recorded", outputs: {}, error: null };
    return {
      ...step,
      status: "pending",
      inputs: {},
      outputs: {},
      error: null,
      started_at: null,
      finished_at: null,
    };
  });
}

export function stageCount(steps, id) {
  const output = steps?.find((step) => step.node_id === id)?.outputs;

  return typeof output?.record_count === "number" ? output.record_count : null;
}

// This function takes an error object and returns a user-friendly error message based on the
// error's content. It checks for specific error messages related to PostgreSQL and connection
// issues, providing a more understandable message for the user. If the error does not match any
// known patterns, it returns the original error message.
export function analysis(records) {
  const statuses = {},
    sources = {},
    issues = {};

  let missing = 0,
    conflicts = 0;

  for (const record of records) {
    statuses[record.status] = (statuses[record.status] || 0) + 1;

    for (const source of new Set(
      (record.evidence || []).map((item) => item.source_type),
    ))
      sources[source] = (sources[source] || 0) + 1;

    for (const issue of new Set(record.issues || []))
      issues[issue] = (issues[issue] || 0) + 1;

    if (record.issues?.some((issue) => issue.startsWith("missing_")))
      missing += 1;

    if (
      record.issues?.some(
        (issue) =>
          issue.startsWith("conflicting_") || issue.endsWith("_mismatch"),
      )
    )
      conflicts += 1;
  }

  return { statuses, sources, issues, missing, conflicts };
}

// This function takes an error object and returns a user-friendly error message based on the
// error's content. It checks for specific error messages related to PostgreSQL and connection
// issues, providing a more understandable message for the user. If the error does not match any
// known patterns, it returns the original error message.
export function rawRecords(run, result) {
  const evidence = new Set(
    (result.evidence || []).map((item) =>
      JSON.stringify([item.source_type, item.source_record_id]),
    ),
  );
  return (
    run.steps?.find((step) => step.node_id === "extraction")?.outputs
      ?.records || []
  ).filter((record) =>
    evidence.has(JSON.stringify([record.source_type, record.source_record_id])),
  );
}
