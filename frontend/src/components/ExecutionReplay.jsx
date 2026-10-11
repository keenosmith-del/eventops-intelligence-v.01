import { useEffect, useMemo, useState } from "react";
import { replayBounds, replaySteps } from "../execution.js";

export function useExecutionReplay(run) {
  const bounds = useMemo(() => replayBounds(run), [run]);
  const [active, setActive] = useState(false), [playing, setPlaying] = useState(false);
  const [offset, setOffset] = useState(0), [speed, setSpeed] = useState(.25);
  useEffect(() => { setActive(false); setPlaying(false); setOffset(0); }, [run?.id]);
  useEffect(() => {
    if (!playing || !bounds) return;
    let previous = performance.now();
    const timer = setInterval(() => {
      const now = performance.now(), elapsed = (now - previous) * speed;
      previous = now;
      setOffset(value => Math.min(value + elapsed, bounds.duration));
    }, 80);
    return () => clearInterval(timer);
  }, [playing, speed, bounds]);
  useEffect(() => { if (bounds && offset >= bounds.duration) setPlaying(false); }, [offset, bounds]);
  const steps = useMemo(() => active && bounds ? replaySteps(run.steps, bounds.start + offset) : run?.steps || [], [active, bounds, run?.steps, offset]);
  return {
    active, playing, offset, speed, bounds,
    steps,
    start: () => { setOffset(0); setActive(true); setPlaying(true); },
    pause: () => setPlaying(false),
    resume: () => { if (offset >= bounds.duration) setOffset(0); setPlaying(true); },
    finish: () => { setPlaying(false); setActive(false); },
    seek: value => { setOffset(Number(value)); setPlaying(false); },
    setSpeed,
  };
}
export default function ExecutionReplay({ replay }) {
  if (!replay.bounds) return <p className="fine-print">Replay requires a finished run with recorded step timestamps.</p>;
  if (!replay.active) return <button onClick={replay.start}>Replay execution</button>;
  return <section className="execution-replay" aria-label="Recorded execution replay">
    <p role="status">Recorded replay · {replay.playing ? "Playing" : "Paused"} · No new run or tool calls · CSV downloads are outside this timeline</p>
    <div className="replay-controls">
      <button onClick={replay.playing ? replay.pause : replay.resume}>{replay.playing ? "Pause replay" : "Resume replay"}</button>
      <button onClick={replay.finish}>Return to complete execution</button>
      <label>Replay speed <select value={replay.speed} onChange={event => replay.setSpeed(Number(event.target.value))}>{[.1, .25, 1, 2].map(speed => <option key={speed} value={speed}>{speed}×</option>)}</select></label>
      <label className="replay-seek">Recorded timeline <input type="range" min="0" max={replay.bounds.duration} step="1" value={replay.offset} onChange={event => replay.seek(event.target.value)} /></label>
      <span>{(replay.offset / 1000).toFixed(2)} / {(replay.bounds.duration / 1000).toFixed(2)} recorded seconds</span>
    </div>
  </section>;
}
