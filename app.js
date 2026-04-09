const BASE_TURN_MS = 5500;
const CLEAR_ACCURACY = 1.0;
const MISS_PENALTY_MS = 600;
const QUESTIONS_PER_STAGE = 20;
const TICK_MS = 100;
const TIMER_BLOCKS = 18;

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
      nextButton: document.getElementById("nextButton"),
      resetButton: document.getElementById("resetButton"),
      keypadButtons: Array.from(document.querySelectorAll(".keypad .key")),
    };

    this.bestStage = 1;
    this.timerId = null;
    this.timerBlocks = [];

    this.buildTimerBlocks();
    this.bindEvents();
    this.resetAll();
    this.startTimer();
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
    this.inputText = "";
    this.currentProblem = null;
    this.expectedAnswer = null;
    this.expectedText = "";
    this.turnRemaining = this.turnLimit;
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
    const accuracy = this.correctAnswers / this.questionsInStage;
    this.stageCleared = accuracy >= CLEAR_ACCURACY;
    if (this.stageCleared) {
      this.bestStage = Math.max(this.bestStage, this.stage + 1);
    }
    this.render();
  }

  nextStage() {
    if (!this.stageFinished) {
      return;
    }

    if (this.stageCleared) {
      this.stage += 1;
    }
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
      this.elements.resultMessage.textContent = this.stageCleared ? "Clear! Next back unlocked" : "Retry this back";
      this.elements.resultMessage.style.color = this.stageCleared ? "var(--good)" : "var(--warn)";
      this.elements.nextButton.textContent = this.stageCleared ? "NEXT" : "RETRY";
      this.elements.nextButton.classList.toggle("action", !this.stageCleared);
      this.elements.nextButton.classList.toggle("digit", this.stageCleared);
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
}

window.addEventListener("DOMContentLoaded", () => {
  new OniCalculationWeb();
});
