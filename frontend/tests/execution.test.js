import { describe, expect, it } from "vitest";
import { analysis, rawRecords, replayBounds, replaySteps } from "../src/execution.js";
const steps = [
  { node_id: "calendar", status: "completed", started_at: "2026-10-10T12:00:00Z", finished_at: "2026-10-10T12:00:02Z", inputs: { limit: 1 }, outputs: { record_count: 1 } },
  { node_id: "email", status: "skipped", finished_at: "2026-10-10T12:00:03Z", error: "Not configured" },
  { node_id: "export", status: "pending" },
];
describe("Recorded execution and saved analysis", () => {
  it("reconstructs only timestamp-supported states and hides future outputs", () => {
    const bounds = replayBounds({ status: "partial", steps });
    expect(bounds.duration).toBe(3000);
    const during = replaySteps(steps, bounds.start + 1000);
    expect(during.map(step => step.status)).toEqual(["running", "pending", "pending"]);
    expect(during[0].outputs).toEqual({});
    expect(during[1].error).toBeNull();
    expect(replaySteps(steps, bounds.end).map(step => step.status)).toEqual(["completed", "skipped", "pending"]);
    expect(replaySteps(steps, bounds.end)[0]).toEqual(steps[0]);
    expect(steps[0].status).toBe("completed");
  });
  it("does not invent a replay for active or untimed executions", () => {
    expect(replayBounds({ status: "running", steps })).toBeNull();
    expect(replayBounds({ status: "completed", steps: [{ status: "completed" }] })).toBeNull();
    expect(replaySteps([{ status: "completed" }], 0)[0].status).toBe("time_not_recorded");
  });
  it("counts distinct contributing sources and issues per persisted record", () => {
    const result = analysis([{ status: "review_required", issues: ["missing_event_id", "missing_event_id", "name_mismatch"], evidence: [{ source_type: "email" }, { source_type: "email" }, { source_type: "web" }] }, { status: "verified", issues: [], evidence: [{ source_type: "web" }] }]);
    expect(result).toEqual({ statuses: { review_required: 1, verified: 1 }, sources: { email: 1, web: 2 }, issues: { missing_event_id: 1, name_mismatch: 1 }, missing: 1, conflicts: 1 });
  });
  it("associates raw values by both source type and source record ID", () => {
    const email = { source_type: "email", source_record_id: "1", email: "RAW@EXAMPLE.COM" };
    const run = { steps: [{ node_id: "extraction", outputs: { records: [email, { source_type: "web", source_record_id: "1" }] } }] };
    expect(rawRecords(run, { evidence: [{ source_type: "email", source_record_id: "1" }] })).toEqual([email]);
  });
});
