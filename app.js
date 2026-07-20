const BASE_TURN_MS = 5500;
// Adaptive difficulty by stage accuracy (correct / questionsInStage):
//   >= 85%      -> level up   (+1 back next stage)
//   66% .. 84%  -> hold       (same back)
//   <= 65%      -> level down (-1 back, min 1-back)
const LEVEL_UP_ACCURACY = 0.85;
const LEVEL_DOWN_ACCURACY = 0.66;
const MISS_PENALTY_MS = 600;
const QUESTIONS_PER_STAGE = 20;
const TICK_MS = 100;
const TIMER_BLOCKS = 18;

const SCHEMA_VERSION = 1;
const APP_ID = "oni-keisan1";
const MAX_EVENTS = 300;
const STATS_KEYS = {
  events: "oniKeisan.stats.events.v1",
  daily: "oniKeisan.stats.daily.v1",
  pending: "oniKeisan.stats.pending.v1",
  bestStage: "oniKeisan.bestStage.v1",
  lastStage: "oniKeisan.lastStage.v1",
};
const DAY_MS = 24 * 60 * 60 * 1000;

class OniCalculationWeb {
  constructor() {
    this.elements = {
      playScreen: document.getElementById("playScreen"),
      resultScreen: document.getElementById("resultScreen"),
      stageLabel: document.getElementById("stageLabel"),
      bestLabel: document.getElementById("bestLabel"),
      turnLabel: document.getElementById("turnLabel"),
      accuracyLabel: document.getElementById("accuracyLabel"),
      problemText: document.getElementById("problemText"),
      instructionText: document.getElementById("instructionText"),
      statusText: document.getElementById("statusText"),
      timerBar: document.getElementById("timerBar"),
      resultTitle: document.getElementById("resultTitle"),
      resultScore: document.getElementById("resultScore"),
      resultAccuracy: document.getElementById("resultAccuracy"),
      resultMessage: document.getElementById("resultMessage"),
      syncStatus: document.getElementById("syncStatus"),
      nextButton: document.getElementById("nextButton"),
      resetButton: document.getElementById("resetButton"),
      keypadButtons: Array.from(document.querySelectorAll(".keypad .key")),
      statToday: document.getElementById("statToday"),
      statBestToday: document.getElementById("statBestToday"),
      statStreak: document.getElementById("statStreak"),
    };

    this.config = window.ONI_CONFIG || {};
    this.sessionId = this.createSessionId();
    this.bestStage = this.loadBestStage();
    this.syncStatusText = "SYNC: waiting";
    this.timerId = null;
    this.timerBlocks = [];

    this.buildTimerBlocks();
    this.bindEvents();
    this.resumeProgress();
    this.startTimer();
    this.renderStatsSummary();
    this.flushPendingEvents();
  }

  buildTimerBlocks() {
    this.elements.timerBar.replaceChildren();
    this.timerBlocks = [];

    for (let index = 0; index < TIMER_BLOCKS; index += 1) {
      const block = document.createElement("span");
      block.className = "timer-block";
      this.elements.timerBar.appendChild(block);
      this.timerBlocks.push(block);
    }
  }

  bindEvents() {
    for (const button of this.elements.keypadButtons) {
      button.addEventListener("click", () => this.handleKeypad(button.dataset.action));
    }

    this.elements.nextButton.addEventListener("click", () => this.nextStage());
    this.elements.resetButton.addEventListener("click", () => this.resetAll());

    window.addEventListener("keydown", (event) => {
      if (event.repeat) {
        return;
      }

      if (event.key.toLowerCase() === "r") {
        this.resetAll();
        return;
      }

      if (this.stageFinished) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          this.nextStage();
        }
        return;
      }

      if (/^[0-9]$/.test(event.key)) {
        this.appendDigit(event.key);
        return;
      }

      if (event.key === "Backspace" || event.key === "Delete") {
        this.deleteDigit();
      }
    });
  }

  startTimer() {
    if (this.timerId !== null) {
      window.clearInterval(this.timerId);
    }

    this.timerId = window.setInterval(() => {
      if (this.stageFinished) {
        return;
      }

      this.turnRemaining -= TICK_MS;
      if (this.turnRemaining <= 0) {
        this.submitTurn(false);
      } else {
        this.render();
      }
    }, TICK_MS);
  }

  resetAll() {
    this.stage = 1;
    this.startStage();
  }

  resumeProgress() {
    // Resume at the last n-back the player was on in the previous session.
    this.stage = this.loadLastStage();
    this.startStage();
  }

  startStage() {
    this.questionsInStage = QUESTIONS_PER_STAGE;
    this.totalTurns = this.questionsInStage + this.stage;
    this.turnLimit = Math.max(2000, BASE_TURN_MS - (this.stage - 1) * 150);
    this.history = [];
    this.turnIndex = 0;
    this.correctAnswers = 0;
    this.totalChecks = 0;
    this.turnResult = "";
    this.stageCleared = false;
    this.stageFinished = false;
    this.stageResultRecorded = false;
    this.levelDelta = 0;
    this.nextStageTarget = this.stage;
    this.stageStartedAt = Date.now();
    this.inputText = "";
    this.currentProblem = null;
    this.expectedAnswer = null;
    this.expectedText = "";
    this.turnRemaining = this.turnLimit;
    this.persistLastStage();
    this.prepareTurn();
    this.render();
  }

  generateProblem() {
    const op = Math.random() < 0.5 ? "+" : "-";
    const displayOp = op === "-" ? "−" : op;

    if (op === "+") {
      const answer = this.randInt(0, 9);
      const left = this.randInt(0, answer);
      const right = answer - left;
      return { text: `${left} ${displayOp} ${right} =`, answer };
    }

    const answer = this.randInt(0, 9);
    const right = this.randInt(0, 9 - answer);
    const left = answer + right;
    return { text: `${left} ${displayOp} ${right} =`, answer };
  }

  randInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  prepareTurn() {
    if (this.turnIndex >= this.totalTurns) {
      this.finishStage();
      return;
    }

    this.inputText = "";
    this.turnRemaining = this.turnLimit;

    if (this.turnIndex < this.questionsInStage) {
      this.currentProblem = this.generateProblem();
      this.history.push(this.currentProblem);
    } else {
      this.currentProblem = null;
    }

    const answerIndex = this.turnIndex - this.stage;
    if (answerIndex >= 0 && answerIndex < this.questionsInStage) {
      this.expectedAnswer = this.history[answerIndex].answer;
      this.expectedText = String(this.expectedAnswer);
      this.turnResult = `Answer ${this.stage}-back`;
    } else {
      this.expectedAnswer = null;
      this.expectedText = "";
      this.turnResult = "Warm-up turn";
    }

    this.render();
  }

  submitTurn(isCorrect) {
    if (this.expectedAnswer !== null) {
      this.totalChecks += 1;
      if (isCorrect) {
        this.correctAnswers += 1;
        this.turnResult = "Correct";
      } else {
        this.turnResult = `Time up  Ans:${this.expectedAnswer}`;
      }
    } else {
      this.turnResult = "Memorize only";
    }

    this.turnIndex += 1;
    this.prepareTurn();
  }

  registerWrongInput() {
    this.turnResult = "Miss";
    this.inputText = "";
    this.turnRemaining = Math.max(TICK_MS, this.turnRemaining - MISS_PENALTY_MS);
    this.render();
  }

  finishStage() {
    this.stageFinished = true;
    const accuracy = this.questionsInStage > 0 ? this.correctAnswers / this.questionsInStage : 0;
    this.levelDelta = accuracy >= LEVEL_UP_ACCURACY ? 1 : accuracy < LEVEL_DOWN_ACCURACY ? -1 : 0;
    this.nextStageTarget = Math.max(1, this.stage + this.levelDelta);
    // "Cleared" now means the player passed this back (>= 85%) and leveled up.
    this.stageCleared = this.levelDelta > 0;
    if (this.stageCleared) {
      this.bestStage = Math.max(this.bestStage, this.nextStageTarget);
    }
    this.recordStageResult();
    this.render();
  }

  nextStage() {
    if (!this.stageFinished) {
      return;
    }

    this.stage = this.nextStageTarget;
    this.startStage();
  }

  appendDigit(digit) {
    if (this.stageFinished || this.expectedAnswer === null) {
      return;
    }

    if (this.inputText.length < this.expectedText.length) {
      this.inputText += digit;
      this.checkAutoAnswer();
      this.render();
    }
  }

  deleteDigit() {
    if (this.stageFinished) {
      return;
    }
    this.inputText = this.inputText.slice(0, -1);
    this.render();
  }

  skipTurn() {
    if (this.stageFinished) {
      return;
    }

    if (this.expectedAnswer !== null) {
      this.totalChecks += 1;
      this.turnResult = `Skip  Ans:${this.expectedAnswer}`;
    } else {
      this.turnResult = "Skip";
    }
    this.turnIndex += 1;
    this.prepareTurn();
  }

  checkAutoAnswer() {
    if (!this.expectedText) {
      return;
    }

    if (!this.expectedText.startsWith(this.inputText)) {
      this.registerWrongInput();
      return;
    }

    if (this.inputText === this.expectedText) {
      this.submitTurn(true);
    }
  }

  handleKeypad(action) {
    if (action === "RESET") {
      this.resetAll();
      return;
    }

    if (this.stageFinished) {
      return;
    }

    if (action === "SKIP") {
      this.skipTurn();
      return;
    }

    this.appendDigit(action);
  }

  render() {
    this.elements.stageLabel.textContent = `STAGE ${this.stage}-BACK`;
    this.elements.bestLabel.textContent = `BEST ${this.bestStage}-BACK`;
    this.elements.turnLabel.textContent = `TURN ${Math.min(this.turnIndex + 1, this.totalTurns)}/${this.totalTurns}`;
    this.elements.accuracyLabel.textContent = this.totalChecks > 0 ? `ACC ${Math.floor((this.correctAnswers * 100) / this.totalChecks)}%` : "ACC --";

    if (this.stageFinished) {
      this.elements.resultTitle.textContent = `${this.stage}-BACK RESULT`;
      this.elements.resultScore.textContent = `Correct: ${this.correctAnswers}/${this.questionsInStage}`;
      this.elements.resultAccuracy.textContent = `Accuracy: ${Math.floor((this.correctAnswers * 100) / this.questionsInStage)}%`;
      const target = this.nextStageTarget;
      const changes = target !== this.stage;
      if (this.levelDelta > 0) {
        this.elements.resultMessage.textContent = `Level up! Next ${target}-back`;
        this.elements.resultMessage.style.color = "var(--good)";
      } else if (this.levelDelta < 0 && changes) {
        this.elements.resultMessage.textContent = `Level down. Next ${target}-back`;
        this.elements.resultMessage.style.color = "var(--warn)";
      } else {
        this.elements.resultMessage.textContent = `Hold ${this.stage}-back`;
        this.elements.resultMessage.style.color = "var(--info)";
      }
      if (this.elements.syncStatus) {
        this.elements.syncStatus.textContent = this.syncStatusText;
      }
      this.elements.nextButton.textContent = changes ? "NEXT" : "RETRY";
      this.elements.nextButton.classList.toggle("action", this.levelDelta <= 0);
      this.elements.nextButton.classList.toggle("digit", this.levelDelta > 0);
      this.elements.playScreen.classList.remove("active");
      this.elements.resultScreen.classList.add("active");
      return;
    }

    this.elements.problemText.textContent = this.currentProblem ? this.currentProblem.text : "ANSWER";
    this.elements.problemText.style.color = this.currentProblem ? "var(--text)" : "var(--title)";
    this.elements.instructionText.textContent = this.expectedAnswer === null ? "Memorize this answer." : `Type the answer from ${this.stage}-back.`;
    this.elements.statusText.textContent = this.turnResult;
    this.elements.statusText.style.color = this.statusColor();
    const fillColor = this.turnRemaining > 1500 ? "#5f5f5f" : "#7a7a7a";
    const activeBlocks = Math.max(0, Math.ceil((this.turnRemaining / this.turnLimit) * TIMER_BLOCKS));
    this.elements.timerBar.style.setProperty("--timer-fill", fillColor);
    for (let index = 0; index < this.timerBlocks.length; index += 1) {
      this.timerBlocks[index].classList.toggle("active", index < activeBlocks);
    }
    this.elements.resultScreen.classList.remove("active");
    this.elements.playScreen.classList.add("active");
  }

  statusColor() {
    if (this.turnResult === "Correct") {
      return "var(--good)";
    }
    if (this.turnResult.startsWith("Miss") || this.turnResult.startsWith("Time up") || this.turnResult.startsWith("Skip")) {
      return "var(--warn)";
    }
    return "var(--text-dim)";
  }

  // --- Stats: ID + date helpers ---------------------------------------------

  createId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  }

  createSessionId() {
    return this.createId();
  }

  createEventId() {
    return this.createId();
  }

  getLocalDate(date = new Date()) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  // --- Stats: localStorage I/O ----------------------------------------------

  readJSON(key, fallback) {
    try {
      const raw = window.localStorage.getItem(key);
      if (raw === null) {
        return fallback;
      }
      return JSON.parse(raw);
    } catch (_error) {
      return fallback;
    }
  }

  writeJSON(key, value) {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (_error) {
      // localStorage may be unavailable or full; stats are best-effort.
    }
  }

  loadStats() {
    const events = this.readJSON(STATS_KEYS.events, []);
    const daily = this.readJSON(STATS_KEYS.daily, {});
    return {
      events: Array.isArray(events) ? events : [],
      daily: daily && typeof daily === "object" ? daily : {},
    };
  }

  saveStats(stats) {
    this.writeJSON(STATS_KEYS.events, stats.events);
    this.writeJSON(STATS_KEYS.daily, stats.daily);
  }

  loadBestStage() {
    const value = this.readJSON(STATS_KEYS.bestStage, 1);
    return Number.isFinite(value) && value >= 1 ? value : 1;
  }

  persistBestStage() {
    this.writeJSON(STATS_KEYS.bestStage, this.bestStage);
  }

  loadLastStage() {
    const value = this.readJSON(STATS_KEYS.lastStage, 1);
    return Number.isFinite(value) && value >= 1 ? value : 1;
  }

  persistLastStage() {
    this.writeJSON(STATS_KEYS.lastStage, this.stage);
  }

  // --- Stats: recording -----------------------------------------------------

  recordStageResult() {
    if (this.stageResultRecorded) {
      return;
    }
    this.stageResultRecorded = true;

    const now = new Date();
    const accuracy = this.questionsInStage > 0 ? this.correctAnswers / this.questionsInStage : 0;
    const event = {
      schemaVersion: SCHEMA_VERSION,
      app: APP_ID,
      eventType: "stage_result",
      eventId: this.createEventId(),
      sessionId: this.sessionId,
      playedAt: now.toISOString(),
      localDate: this.getLocalDate(now),
      // Offset from UTC in minutes, east-positive (JST => 540).
      timezoneOffsetMinutes: -now.getTimezoneOffset(),
      stage: this.stage,
      correctAnswers: this.correctAnswers,
      totalQuestions: this.questionsInStage,
      accuracy,
      cleared: this.stageCleared,
      reachedBack: this.stage,
      nextBackUnlocked: this.stageCleared ? this.stage + 1 : null,
      durationMs: this.stageStartedAt ? Date.now() - this.stageStartedAt : null,
      source: "web",
    };

    const stats = this.loadStats();
    stats.events.push(event);
    if (stats.events.length > MAX_EVENTS) {
      stats.events = stats.events.slice(-MAX_EVENTS);
    }
    this.updateDailySummary(stats, event);
    this.saveStats(stats);
    this.persistBestStage();
    this.renderStatsSummary();
    this.sendStageResult(event);
  }

  updateDailySummary(stats, event) {
    const key = event.localDate;
    const summary = stats.daily[key] || {
      schemaVersion: SCHEMA_VERSION,
      app: APP_ID,
      localDate: key,
      stagesPlayed: 0,
      questionsAnswered: 0,
      correctAnswers: 0,
      bestReachedBack: 0,
      bestClearedBack: 0,
      maxUnlockedBack: 0,
      allClearCount: 0,
      lastPlayedAt: null,
    };

    summary.stagesPlayed += 1;
    summary.questionsAnswered += event.totalQuestions;
    summary.correctAnswers += event.correctAnswers;
    summary.bestReachedBack = Math.max(summary.bestReachedBack, event.reachedBack);
    if (event.cleared) {
      summary.bestClearedBack = Math.max(summary.bestClearedBack, event.reachedBack);
      summary.allClearCount += 1;
    }
    const unlocked = event.nextBackUnlocked === null ? event.reachedBack : event.nextBackUnlocked;
    summary.maxUnlockedBack = Math.max(summary.maxUnlockedBack, unlocked);
    summary.lastPlayedAt = event.playedAt;

    stats.daily[key] = summary;
  }

  computeStreak(daily) {
    const active = new Set(
      Object.keys(daily).filter((date) => daily[date] && daily[date].stagesPlayed >= 1),
    );

    const shift = (dateStr, days) => {
      const [year, month, day] = dateStr.split("-").map(Number);
      const date = new Date(year, month - 1, day);
      date.setTime(date.getTime() + days * DAY_MS);
      return this.getLocalDate(date);
    };

    // Current streak: consecutive active days ending today (or yesterday if
    // today has not been played yet so an ongoing streak still counts).
    let current = 0;
    let cursor = this.getLocalDate();
    if (!active.has(cursor)) {
      cursor = shift(cursor, -1);
    }
    while (active.has(cursor)) {
      current += 1;
      cursor = shift(cursor, -1);
    }

    // Longest streak across all recorded days.
    let longest = 0;
    for (const date of active) {
      if (active.has(shift(date, -1))) {
        continue; // not the start of a run
      }
      let length = 0;
      let runCursor = date;
      while (active.has(runCursor)) {
        length += 1;
        runCursor = shift(runCursor, 1);
      }
      longest = Math.max(longest, length);
    }

    const sorted = [...active].sort();
    return {
      currentStreakDays: current,
      longestStreakDays: longest,
      lastActiveDate: sorted.length ? sorted[sorted.length - 1] : null,
    };
  }

  renderStatsSummary() {
    if (!this.elements.statToday) {
      return;
    }

    const stats = this.loadStats();
    const today = this.getLocalDate();
    const summary = stats.daily[today];
    const streak = this.computeStreak(stats.daily);

    if (summary) {
      this.elements.statToday.textContent = `TODAY ${summary.correctAnswers}/${summary.questionsAnswered}`;
      if (summary.bestClearedBack > 0) {
        this.elements.statBestToday.textContent = `BEST TODAY ${summary.bestClearedBack}-BACK`;
      } else if (summary.bestReachedBack > 0) {
        // Reached but not cleared (100% required) — mark with an asterisk.
        this.elements.statBestToday.textContent = `BEST TODAY ${summary.bestReachedBack}-BACK*`;
      } else {
        this.elements.statBestToday.textContent = "BEST TODAY --";
      }
    } else {
      this.elements.statToday.textContent = "TODAY 0/0";
      this.elements.statBestToday.textContent = "BEST TODAY --";
    }

    const days = streak.currentStreakDays;
    this.elements.statStreak.textContent = `STREAK ${days} DAY${days === 1 ? "" : "S"}`;
  }

  setSyncStatus(message) {
    this.syncStatusText = `SYNC: ${message}`;
    if (this.elements.syncStatus) {
      this.elements.syncStatus.textContent = this.syncStatusText;
    }
  }

  // --- Stats: server send ---------------------------------------------------

  get syncReady() {
    return Boolean(this.config && this.config.statsEndpoint);
  }

  toRow(event) {
    return {
      event_id: event.eventId,
      session_id: event.sessionId,
      schema_version: event.schemaVersion,
      app: event.app,
      event_type: event.eventType,
      played_at: event.playedAt,
      local_date: event.localDate,
      timezone_offset_minutes: event.timezoneOffsetMinutes,
      stage: event.stage,
      correct_answers: event.correctAnswers,
      total_questions: event.totalQuestions,
      accuracy: event.accuracy,
      cleared: event.cleared,
      reached_back: event.reachedBack,
      next_back_unlocked: event.nextBackUnlocked,
      duration_ms: event.durationMs,
      source: event.source,
    };
  }

  async postRow(event) {
    const response = await fetch(this.config.statsEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(this.toRow(event)),
    });
    if (!response.ok) {
      const text = await response.text().catch(() => "");
      throw new Error(`HTTP ${response.status}: ${text.slice(0, 120)}`);
    }
    // The server returns 200 for both a fresh store and a dedup'd retry
    // (event_id is UNIQUE), so any 2xx means this event is safely recorded.
    return true;
  }

  queuePending(event) {
    const pending = this.readJSON(STATS_KEYS.pending, []);
    const list = Array.isArray(pending) ? pending : [];
    if (!list.some((item) => item.eventId === event.eventId)) {
      list.push(event);
    }
    if (list.length > MAX_EVENTS) {
      list.splice(0, list.length - MAX_EVENTS);
    }
    this.writeJSON(STATS_KEYS.pending, list);
  }

  async sendStageResult(event) {
    if (!this.syncReady) {
      this.setSyncStatus("local only / no endpoint config");
      return; // Offline-only mode: keep stats in localStorage.
    }
    this.setSyncStatus("sending...");
    try {
      const ok = await this.postRow(event);
      if (ok) {
        this.setSyncStatus(`sent ${event.localDate} ${event.stage}-BACK`);
        this.flushPendingEvents();
      } else {
        this.setSyncStatus("queued / server rejected");
        this.queuePending(event);
      }
    } catch (error) {
      this.setSyncStatus(`queued / ${error.message || "network error"}`);
      this.queuePending(event); // Network error — retry on next launch.
    }
  }

  async flushPendingEvents() {
    if (!this.syncReady) {
      return;
    }
    const pending = this.readJSON(STATS_KEYS.pending, []);
    if (!Array.isArray(pending) || pending.length === 0) {
      return;
    }

    const remaining = [];
    for (const event of pending) {
      try {
        const ok = await this.postRow(event);
        if (!ok) {
          remaining.push(event);
        }
      } catch (_error) {
        remaining.push(event);
      }
    }
    this.writeJSON(STATS_KEYS.pending, remaining);
  }
}

window.addEventListener("DOMContentLoaded", () => {
  new OniCalculationWeb();
});
