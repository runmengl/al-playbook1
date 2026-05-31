import { useEffect, useRef, useState } from "react";

const demoSteps = [
  "[00:00] Initializing AI Playbook source finder...",
  "[00:01] Loading seed URLs...",
  "[00:02] Checking source authority rules...",
  "[00:03] Searching for public policy documents...",
  "[00:04] Found source: National Academy of Public Administration",
  "[00:05] Found source: GAO report index",
  "[00:06] Found source: Brookings public management archive",
  "[00:07] Classifying source type: government report",
  "[00:08] Classifying source type: policy research institute",
  "[00:09] Extracting title, URL, organization, and topic tags...",
  "[00:10] Applying AI Playbook relevance filters...",
  "[00:11] Organizing results into structured records...",
  "[00:12] Generating CSV output...",
  "[00:13] Generating Markdown summary...",
  "[00:14] Generating DOCX-ready report structure...",
  "[00:15] Writing run log...",
  "[00:16] Demo run complete."
];

const commandText = "python ai_playbook_policy_document_finder.py --quick --max-results 10";
const stepDelayMs = 700;
const statusStages = [
  "Idle",
  "Initializing",
  "Fetching",
  "Classifying",
  "Generating files",
  "Complete"
];

function getStatusForStep(index) {
  if (index === 0) {
    return "Initializing";
  }

  if (index >= 1 && index <= 6) {
    return "Fetching";
  }

  if (index >= 7 && index <= 11) {
    return "Classifying";
  }

  if (index >= 12 && index <= 15) {
    return "Generating files";
  }

  return "Complete";
}

export default function LiveRunDemo({ autoStart = false }) {
  const [lines, setLines] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [status, setStatus] = useState(statusStages[0]);
  const [copyLabel, setCopyLabel] = useState("Copy Command");
  const timersRef = useRef([]);
  const outputRef = useRef(null);

  const progress = Math.round((lines.length / demoSteps.length) * 100);

  function clearTimers() {
    timersRef.current.forEach((timerId) => window.clearTimeout(timerId));
    timersRef.current = [];
  }

  function resetDemo() {
    clearTimers();
    setLines([]);
    setIsRunning(false);
    setIsComplete(false);
    setStatus(statusStages[0]);
  }

  function startDemo() {
    resetDemo();
    setIsRunning(true);
    setStatus(statusStages[1]);

    demoSteps.forEach((line, index) => {
      const timerId = window.setTimeout(() => {
        setStatus(getStatusForStep(index));
        setLines((currentLines) => [...currentLines, line]);

        if (index === demoSteps.length - 1) {
          setIsRunning(false);
          setIsComplete(true);
          setStatus(statusStages[5]);
        }
      }, index * stepDelayMs);

      timersRef.current.push(timerId);
    });
  }

  async function copyCommand() {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(commandText);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = commandText;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.append(textarea);
        textarea.select();
        document.execCommand("copy");
        textarea.remove();
      }

      setCopyLabel("Copied");
    } catch {
      setCopyLabel("Copy Failed");
    }

    window.setTimeout(() => setCopyLabel("Copy Command"), 1600);
  }

  useEffect(() => {
    if (autoStart) {
      startDemo();
    }

    return clearTimers;
  }, [autoStart]);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [lines]);

  return (
    <article className="live-demo-panel" id="run">
      <div className="live-demo-header">
        <div>
          <p className="eyebrow">How to Run</p>
          <h2>Live Run Demo</h2>
          <p>
            This is a simulated browser demo for classroom walkthroughs. It does not run Python,
            crawl websites, call external APIs, or use credentials.
          </p>
        </div>
        <span className="demo-status">{status}</span>
      </div>

      <div className="command-row" aria-label="Example command">
        <code>{commandText}</code>
        <button className="button secondary compact" type="button" onClick={copyCommand}>
          {copyLabel}
        </button>
      </div>

      <div className="demo-controls">
        <button className="button primary" type="button" onClick={startDemo} disabled={isRunning}>
          {isRunning ? "Demo Running" : isComplete ? "Run Demo Again" : "Start Demo Run"}
        </button>
        <button className="button secondary" type="button" onClick={resetDemo}>
          Reset Demo
        </button>
      </div>

      <div className="progress-wrap" aria-label="Demo progress">
        <div className="progress-meta">
          <span>Progress</span>
          <span>{progress}%</span>
        </div>
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="live-status-row" aria-label="Live demo status">
        {statusStages.map((stage) => (
          <span
            className={`status-pill${status === stage ? " is-active" : ""}`}
            aria-current={status === stage ? "step" : "false"}
            key={stage}
          >
            {stage}
          </span>
        ))}
      </div>

      <div className="terminal" aria-label="Simulated terminal output">
        <div className="terminal-top" aria-hidden="true">
          <span className="terminal-dot red" />
          <span className="terminal-dot yellow" />
          <span className="terminal-dot green" />
        </div>
        <div className="terminal-output" ref={outputRef} aria-live="polite">
          {lines.map((line) => {
            const match = line.match(/^(\[[^\]]+\])\s(.+)$/);

            return (
              <div className="terminal-line" key={line}>
                {match ? (
                  <>
                    <span className="terminal-time">{match[1]}</span>
                    <span> {match[2]}</span>
                  </>
                ) : (
                  line
                )}
              </div>
            );
          })}
        </div>
        <div className="terminal-prompt">
          <span>$</span>
          <span className={`cursor${isRunning ? " is-running" : ""}`} aria-hidden="true" />
        </div>
      </div>

      {isComplete && (
        <section className="demo-summary" aria-label="Demo run summary">
          <h3>Demo Run Summary</h3>
          <ul>
            <li>
              <strong>Sources scanned:</strong> 12
            </li>
            <li>
              <strong>Relevant sources found:</strong> 7
            </li>
            <li>
              <strong>Output formats prepared:</strong> CSV, Markdown, DOCX, run log
            </li>
            <li>
              <strong>Status:</strong> Complete
            </li>
          </ul>
          <div className="file-badges" aria-label="Simulated output files">
            <span>sources.csv</span>
            <span>source_summary.md</span>
            <span>playbook_report.docx</span>
            <span>run_log.txt</span>
          </div>
        </section>
      )}
    </article>
  );
}
