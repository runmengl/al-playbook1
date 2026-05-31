(() => {
  const paperLibrary = [
    {
      id: "public-sector-innovation-policy-capacity",
      title: "Public Sector Innovation and Policy Capacity",
      authors: "Maya Chen and Daniel R. Hayes",
      year: "2024",
      methodology: "mixed_methods",
      keywords: ["public policy", "public sector innovation", "policy capacity", "public management"],
      abstract:
        "Examines how agency capacity, leadership routines, and cross-sector learning shape innovation in public policy programs.",
      research_text:
        "This mixed methods study examines public sector innovation and policy capacity across city and state agencies."
    },
    {
      id: "administrative-burden-policy-implementation",
      title: "Administrative Burden and Public Policy Implementation",
      authors: "Lena Ortiz and Samuel Green",
      year: "2023",
      methodology: "quantitative",
      keywords: ["public policy", "administrative burden", "implementation", "service access"],
      abstract:
        "Tests whether paperwork costs, waiting time, and compliance rules are associated with lower program uptake.",
      research_text:
        "This quantitative analysis studies administrative burden in public policy implementation using enrollment and survey data."
    },
    {
      id: "street-level-policy-delivery",
      title: "Street-Level Bureaucracy and Public Policy Delivery",
      authors: "Ari Patel",
      year: "2022",
      methodology: "qualitative",
      keywords: ["public policy", "street-level bureaucracy", "frontline discretion", "implementation"],
      abstract:
        "Uses interview evidence to show how frontline discretion changes the practical delivery of policy goals.",
      research_text:
        "This qualitative paper investigates how street-level bureaucracy shapes public policy delivery."
    },
    {
      id: "public-service-motivation-local-government",
      title: "Public Service Motivation in Local Government Teams",
      authors: "Rachel Kim and Thomas Bell",
      year: "2021",
      methodology: "quantitative",
      keywords: ["public service motivation", "local government", "employee engagement", "public management"],
      abstract:
        "Analyzes survey patterns linking public service motivation with engagement and retention in local agencies.",
      research_text:
        "This quantitative study analyzes survey data from local government employees to explore public service motivation."
    },
    {
      id: "collaborative-governance-climate-planning",
      title: "Collaborative Governance Networks in Regional Climate Planning",
      authors: "Nora Williams and Ethan Brooks",
      year: "2024",
      methodology: "case_study",
      keywords: ["collaborative governance", "climate planning", "regional networks", "public administration"],
      abstract:
        "Studies how public agencies, nonprofit partners, and community groups coordinate regional climate plans.",
      research_text:
        "This case study examines collaborative governance in regional climate planning."
    },
    {
      id: "performance-management-feedback-loops",
      title: "Performance Management Feedback Loops in City Agencies",
      authors: "Grace Liu",
      year: "2020",
      methodology: "quantitative",
      keywords: ["performance management", "city agencies", "data dashboards", "public management"],
      abstract:
        "Assesses whether performance dashboards are associated with faster service adjustments in city agencies.",
      research_text:
        "This quantitative paper evaluates performance management feedback loops in city agencies."
    },
    {
      id: "crisis-management-public-health",
      title: "Crisis Management Coordination During Public Health Emergencies",
      authors: "Ibrahim Saleh and Julia Martin",
      year: "2023",
      methodology: "qualitative",
      keywords: ["crisis management", "public health", "interagency coordination", "emergency response"],
      abstract:
        "Explores how interagency coordination routines affect response consistency during public health emergencies.",
      research_text:
        "This qualitative study explores crisis management coordination during public health emergencies."
    },
    {
      id: "coproduction-digital-service-design",
      title: "Co-Production and Digital Service Design",
      authors: "Sofia Ramirez and Mark Ellis",
      year: "2022",
      methodology: "mixed_methods",
      keywords: ["co-production", "digital services", "user-centered design", "public service delivery"],
      abstract:
        "Combines usability data and resident interviews to study co-production in digital public services.",
      research_text:
        "This mixed methods paper studies co-production in digital service design."
    },
    {
      id: "equity-audits-public-management",
      title: "Equity Audits in Public Management",
      authors: "Hannah Morgan",
      year: "2021",
      methodology: "systematic_review",
      keywords: ["equity audits", "public management", "administrative data", "service equity"],
      abstract:
        "Reviews public management studies that use equity audits to identify service access disparities.",
      research_text:
        "This systematic review synthesizes public management studies using equity audits."
    },
    {
      id: "evidence-translation-administrative-reform",
      title: "Evidence Translation for Administrative Reform",
      authors: "Priya Nair and Owen Clarke",
      year: "2024",
      methodology: "theoretical",
      keywords: ["evidence translation", "administrative reform", "policy learning", "public policy"],
      abstract:
        "Develops a framework for translating research findings into usable administrative reform guidance.",
      research_text:
        "This theoretical paper develops a framework for evidence translation in administrative reform and public policy."
    }
  ];

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

  const elements = {
    input: document.getElementById("paper-keyword-input"),
    startButton: document.getElementById("start-paper-search"),
    status: document.getElementById("paper-search-status"),
    activity: document.getElementById("paper-search-activity"),
    statusPills: Array.from(document.querySelectorAll("[data-paper-status]")),
    progressBar: document.getElementById("paper-search-progress-bar"),
    progressLabel: document.getElementById("paper-search-progress-label"),
    output: document.getElementById("paper-terminal-output"),
    cursor: document.getElementById("paper-terminal-cursor"),
    results: document.getElementById("paper-results"),
    loadedMessage: document.getElementById("paper-loaded-message")
  };

  if (!elements.input || !elements.startButton || !elements.output) {
    return;
  }

  const state = {
    timers: [],
    running: false,
    activeResults: []
  };

  function searchPapers({ query, papers }) {
    const normalizedQuery = (query || "").trim().toLowerCase();
    const library = Array.isArray(papers) ? papers : [];

    if (!normalizedQuery) {
      return library.slice(0, 4);
    }

    return library.filter((paper) => {
      const searchableText = [
        paper.title,
        paper.authors,
        paper.abstract,
        paper.methodology,
        ...paper.keywords
      ]
        .join(" ")
        .toLowerCase();

      return searchableText.includes(normalizedQuery);
    });
  }

  function clearTimers() {
    state.timers.forEach((timerId) => window.clearTimeout(timerId));
    state.timers = [];
  }

  function setStatus(label) {
    elements.status.textContent = label;
    elements.statusPills.forEach((pill) => {
      pill.classList.toggle("is-active", pill.dataset.paperStatus === label);
      pill.setAttribute("aria-current", pill.dataset.paperStatus === label ? "step" : "false");
    });
  }

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

  function setActivity(label, isActive = false) {
    elements.activity.textContent = label;
    elements.activity.classList.toggle("is-active", isActive);
  }

  function setProgress(completedSteps, totalSteps) {
    const percent = Math.round((completedSteps / totalSteps) * 100);
    elements.progressBar.style.width = `${percent}%`;
    elements.progressLabel.textContent = `${percent}%`;
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

  function resetSearch() {
    clearTimers();
    state.running = false;
    state.activeResults = [];
    elements.output.replaceChildren();
    elements.results.replaceChildren();
    elements.results.hidden = true;
    elements.loadedMessage.replaceChildren();
    elements.loadedMessage.hidden = true;
    elements.startButton.disabled = false;
    elements.cursor.classList.remove("is-running");
    setProgress(0, 1);
    setStatus(searchStages[0]);
    setActivity(activityLabels.idle);
  }

  function createTextElement(tagName, className, text) {
    const element = document.createElement(tagName);
    if (className) {
      element.className = className;
    }
    element.textContent = text;
    return element;
  }

  function renderResults(results, query) {
    elements.results.replaceChildren();
    elements.results.hidden = false;

    const heading = createTextElement("h3", "", "Search Results");
    elements.results.append(heading);

    if (results.length === 0) {
      elements.results.append(
        createTextElement("p", "empty-results", `No local papers matched "${query}". Try public policy, motivation, or innovation.`)
      );
      return;
    }

    results.forEach((paper) => {
      const item = document.createElement("article");
      item.className = "paper-result";

      item.append(createTextElement("h4", "", paper.title));
      item.append(createTextElement("p", "paper-meta", `${paper.authors} | ${paper.year} | ${paper.methodology}`));
      item.append(createTextElement("p", "paper-abstract", paper.abstract));

      const keywordList = document.createElement("div");
      keywordList.className = "paper-keywords";
      paper.keywords.forEach((keyword) => {
        keywordList.append(createTextElement("span", "", keyword));
      });
      item.append(keywordList);

      const button = document.createElement("button");
      button.className = "button secondary compact use-paper-button";
      button.type = "button";
      button.textContent = "Use This Paper";
      button.addEventListener("click", () => handleUsePaper(paper));
      item.append(button);

      elements.results.append(item);
    });
  }

  function handleUsePaper(paper) {
    elements.loadedMessage.replaceChildren();
    elements.loadedMessage.hidden = false;
    elements.loadedMessage.append(createTextElement("strong", "", "Paper loaded for demo"));
    elements.loadedMessage.append(createTextElement("span", "", `${paper.title} | ${paper.methodology}`));
  }

  function finishSearch(query, results) {
    state.running = false;
    elements.startButton.disabled = false;
    elements.startButton.textContent = "Start Paper Search";
    elements.cursor.classList.remove("is-running");
    setStatus(searchStages[3]);
    setActivity(activityLabels.complete);
    renderResults(results, query || "featured papers");
  }

  function startSearch() {
    resetSearch();

    const query = elements.input.value.trim();
    const results = searchPapers({ query, papers: paperLibrary });
    const steps = buildSearchSteps(query, results);

    state.running = true;
    state.activeResults = results;
    elements.startButton.disabled = true;
    elements.startButton.textContent = "Searching";
    elements.cursor.classList.add("is-running");
    setStatus(searchStages[1]);
    setActivity(activityLabels.metadata, true);

    steps.forEach((line, index) => {
      const timerId = window.setTimeout(() => {
        setStatus(getStatusForStep(index));
        setActivity(getActivityForStep(index), true);
        appendTerminalLine(line);
        setProgress(index + 1, steps.length);

        if (index === steps.length - 1) {
          finishSearch(query, results);
        }
      }, index * stepDelayMs);

      state.timers.push(timerId);
    });
  }

  elements.startButton.addEventListener("click", startSearch);
  elements.input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !state.running) {
      startSearch();
    }
  });

  resetSearch();
})();
