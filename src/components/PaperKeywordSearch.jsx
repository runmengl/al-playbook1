import { useEffect, useRef, useState } from "react";
import { paperLibrary } from "../data/paperLibrary";
import { searchPapers } from "../logic/searchPapers";

const searchStages = ["Idle", "Searching", "Classifying", "Complete"];
const activityLabels = {
  idle: "Ready for local keyword search",
  metadata: "Fetching metadata...",
  relevance: "Checking relevance...",
  methodology: "Classifying methodology...",
  cards: "Building result cards...",
  complete: "Search complete."
};
const stepDelayMs = 650;

function getStatusForStep(index) {
  if (index >= 6 && index <= 8) {
    return "Classifying";
  }

  if (index >= 9) {
    return "Complete";
  }

  return "Searching";
}

function getActivityForStep(index) {
  if (index <= 2) {
    return activityLabels.metadata;
  }

  if (index >= 3 && index <= 5) {
    return activityLabels.relevance;
  }

  if (index >= 6 && index <= 8) {
    return activityLabels.methodology;
  }

  if (index >= 9) {
    return activityLabels.cards;
  }

  return activityLabels.idle;
}

function buildSearchSteps(query, results) {
  const keyword = query || "featured papers";
  const firstResult = results[0]?.title || "No direct candidate found";
  const secondResult = results[1]?.title || "Reviewing featured public administration papers";

  return [
    "[00:00] Initializing paper search module...",
    "[00:01] Reading local public administration paper index...",
    `[00:02] Search keyword: ${keyword}`,
    "[00:03] Matching keyword against titles, abstracts, and tags...",
    `[00:04] Found candidate paper: ${firstResult}`,
    `[00:05] Found candidate paper: ${secondResult}`,
    "[00:06] Extracting abstract and metadata...",
    "[00:07] Classifying methodology...",
    "[00:08] Applying AI Playbook relevance filters...",
    "[00:09] Preparing search results...",
    "[00:10] Search complete."
  ];
}

export default function PaperKeywordSearch({ onUsePaper }) {
  const [query, setQuery] = useState("");
  const [lines, setLines] = useState([]);
  const [status, setStatus] = useState(searchStages[0]);
  const [activity, setActivity] = useState(activityLabels.idle);
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [totalSteps, setTotalSteps] = useState(1);
  const timersRef = useRef([]);
  const outputRef = useRef(null);

  const progress = Math.round((lines.length / totalSteps) * 100);

  function clearTimers() {
    timersRef.current.forEach((timerId) => window.clearTimeout(timerId));
    timersRef.current = [];
  }

  function resetSearch() {
    clearTimers();
    setLines([]);
    setStatus(searchStages[0]);
    setActivity(activityLabels.idle);
    setIsRunning(false);
    setResults([]);
    setHasSearched(false);
    setSelectedPaper(null);
    setTotalSteps(1);
  }

  function finishSearch(matches) {
    setIsRunning(false);
    setStatus(searchStages[3]);
    setActivity(activityLabels.complete);
    setResults(matches);
    setHasSearched(true);
    setSelectedPaper(null);
  }

  function startSearch() {
    resetSearch();

    const trimmedQuery = query.trim();
    const matches = searchPapers({ query: trimmedQuery, papers: paperLibrary });
    const steps = buildSearchSteps(trimmedQuery, matches);

    setIsRunning(true);
    setStatus(searchStages[1]);
    setActivity(activityLabels.metadata);
    setTotalSteps(steps.length);

    steps.forEach((line, index) => {
      const timerId = window.setTimeout(() => {
        setStatus(getStatusForStep(index));
        setActivity(getActivityForStep(index));
        setLines((currentLines) => [...currentLines, line]);

        if (index === steps.length - 1) {
          finishSearch(matches);
        }
      }, index * stepDelayMs);

      timersRef.current.push(timerId);
    });
  }

  function handleUsePaper(paper) {
    setSelectedPaper(paper);
    onUsePaper?.(paper);
  }

  useEffect(() => clearTimers, []);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [lines]);

  return (
    <article className="card paper-search-card" id="paper-search">
      <div className="paper-search-header">
        <div>
          <p className="eyebrow">Local Library</p>
          <h2>Paper Keyword Search</h2>
        </div>
        <span className="demo-status">{status}</span>
      </div>

      <label className="field-label" htmlFor="paper-keyword-input">
        Keyword
      </label>
      <div className="search-input-row">
        <input
          id="paper-keyword-input"
          type="text"
          placeholder="Enter keyword, e.g., public policy"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !isRunning) {
              startSearch();
            }
          }}
        />
        <button className="button primary" type="button" onClick={startSearch} disabled={isRunning}>
          {isRunning ? "Searching" : "Start Paper Search"}
        </button>
      </div>

      <div className="live-status-row paper-status-row" aria-label="Paper search status">
        {searchStages.map((stage) => (
          <span
            className={`status-pill${status === stage ? " is-active" : ""}`}
            aria-current={status === stage ? "step" : "false"}
            key={stage}
          >
            {stage}
          </span>
        ))}
      </div>

      <div className={`search-activity-label${isRunning ? " is-active" : ""}`} aria-live="polite">
        {activity}
      </div>

      <div className="progress-wrap" aria-label="Paper search progress">
        <div className="progress-meta">
          <span>Progress</span>
          <span>{progress}%</span>
        </div>
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="terminal paper-terminal" aria-label="Simulated paper search terminal output">
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

      {hasSearched && (
        <section className="paper-results" aria-label="Paper search results">
          <h3>Search Results</h3>
          {results.length === 0 ? (
            <p className="empty-results">No local papers matched "{query.trim()}". Try public policy, motivation, or innovation.</p>
          ) : (
            results.map((paper) => (
              <article className="paper-result" key={paper.id}>
                <h4>{paper.title}</h4>
                <p className="paper-meta">
                  {paper.authors} | {paper.year} | {paper.methodology}
                </p>
                <p className="paper-abstract">{paper.abstract}</p>
                <div className="paper-keywords">
                  {paper.keywords.map((keyword) => (
                    <span key={keyword}>{keyword}</span>
                  ))}
                </div>
                <button
                  className="button secondary compact use-paper-button"
                  type="button"
                  onClick={() => handleUsePaper(paper)}
                >
                  Use This Paper
                </button>
              </article>
            ))
          )}
        </section>
      )}

      {selectedPaper && (
        <section className="paper-loaded" aria-live="polite">
          <strong>Paper loaded for demo</strong>
          <span>
            {selectedPaper.title} | {selectedPaper.methodology}
          </span>
        </section>
      )}
    </article>
  );
}
