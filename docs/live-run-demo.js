(() => {
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

  const stepDelayMs = 700;
  const commandText = "python ai_playbook_policy_document_finder.py --quick --max-results 10";
  const statusStages = [
    "Idle",
    "Initializing",
    "Fetching",
    "Classifying",
    "Generating files",
    "Complete"
  ];

  const elements = {
    panel: document.getElementById("run"),
    howToRunButton: document.getElementById("how-to-run-button"),
    startButton: document.getElementById("start-demo-run"),
    resetButton: document.getElementById("reset-demo-run"),
    copyButton: document.getElementById("copy-demo-command"),
    command: document.getElementById("demo-command"),
    output: document.getElementById("terminal-output"),
    cursor: document.getElementById("terminal-cursor"),
    progressBar: document.getElementById("demo-progress-bar"),
    progressLabel: document.getElementById("demo-progress-label"),
    summary: document.getElementById("demo-summary"),
    status: document.getElementById("demo-status"),
    statusPills: Array.from(document.querySelectorAll("[data-live-status]"))
  };

  if (!elements.panel || !elements.startButton || !elements.output) {
    return;
  }

  const state = {
    timers: [],
    running: false
  };

  function clearTimers() {
    state.timers.forEach((timerId) => window.clearTimeout(timerId));
    state.timers = [];
  }

  function showPanel(shouldScroll = false) {
    elements.panel.hidden = false;
    if (shouldScroll) {
      elements.panel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function setProgress(completedSteps) {
    const percent = Math.round((completedSteps / demoSteps.length) * 100);
    elements.progressBar.style.width = `${percent}%`;
    elements.progressLabel.textContent = `${percent}%`;
  }

  function setStatus(label) {
    elements.status.textContent = label;
    elements.statusPills.forEach((pill) => {
      pill.classList.toggle("is-active", pill.dataset.liveStatus === label);
      pill.setAttribute("aria-current", pill.dataset.liveStatus === label ? "step" : "false");
    });
  }

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

  function appendTerminalLine(line) {
    const row = document.createElement("div");
    row.className = "terminal-line";

    const match = line.match(/^(\[[^\]]+\])\s(.+)$/);
    if (match) {
      const time = document.createElement("span");
      time.className = "terminal-time";
      time.textContent = match[1];

      const message = document.createElement("span");
      message.textContent = ` ${match[2]}`;

      row.append(time, message);
    } else {
      row.textContent = line;
    }

    elements.output.append(row);
    elements.output.scrollTop = elements.output.scrollHeight;
  }

  function resetDemo() {
    clearTimers();
    state.running = false;
    elements.output.replaceChildren();
    elements.summary.hidden = true;
    elements.startButton.disabled = false;
    elements.startButton.textContent = "Start Demo Run";
    elements.cursor.classList.remove("is-running");
    setProgress(0);
    setStatus(statusStages[0]);
  }

  function finishDemo() {
    state.running = false;
    elements.summary.hidden = false;
    elements.startButton.disabled = false;
    elements.startButton.textContent = "Run Demo Again";
    elements.cursor.classList.remove("is-running");
    setStatus(statusStages[5]);
  }

  function startDemo() {
    showPanel();
    resetDemo();
    state.running = true;
    elements.startButton.disabled = true;
    elements.startButton.textContent = "Demo Running";
    elements.cursor.classList.add("is-running");
    setStatus(statusStages[1]);

    demoSteps.forEach((line, index) => {
      const timerId = window.setTimeout(() => {
        setStatus(getStatusForStep(index));
        appendTerminalLine(line);
        setProgress(index + 1);

        if (index === demoSteps.length - 1) {
          finishDemo();
        }
      }, index * stepDelayMs);

      state.timers.push(timerId);
    });
  }

  async function copyCommand() {
    const originalLabel = elements.copyButton.textContent;
    const value = elements.command.textContent.trim() || commandText;

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(value);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = value;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.append(textarea);
        textarea.select();
        document.execCommand("copy");
        textarea.remove();
      }

      elements.copyButton.textContent = "Copied";
    } catch {
      elements.copyButton.textContent = "Copy Failed";
    }

    window.setTimeout(() => {
      elements.copyButton.textContent = originalLabel;
    }, 1600);
  }

  elements.howToRunButton?.addEventListener("click", (event) => {
    event.preventDefault();
    showPanel(true);
    startDemo();
  });

  elements.startButton.addEventListener("click", startDemo);
  elements.resetButton.addEventListener("click", resetDemo);
  elements.copyButton?.addEventListener("click", copyCommand);

  if (window.location.hash === "#run") {
    showPanel();
  }
})();
