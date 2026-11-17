class RestorationUI {
  constructor() {
    this.canvas = document.querySelector("#painting-canvas");
    this.context = this.canvas.getContext("2d");
    this.selectedCell = 0;
    this.selectedTool = null;
    this.currentLayer = 2;
    this.moveLog = [];
    this.bindControls();
    this.draw();
  }

  bindControls() {
    this.canvas.addEventListener("keydown", (event) => this.handleCanvasKey(event));
    this.canvas.addEventListener("click", (event) => this.selectCanvasCell(event));
    document.querySelectorAll("[data-tool]").forEach((button) => {
      button.addEventListener("click", () => this.selectTool(button));
    });
    document.querySelectorAll(".mixing input").forEach((input) => {
      input.addEventListener("input", () => this.updateMix());
    });
    document.querySelector("#apply-solvent").addEventListener("click", () => this.apply());
    document.querySelector("#export-png").addEventListener("click", () => this.exportPng());
  }

  handleCanvasKey(event) {
    const moves = { ArrowUp: -4, ArrowDown: 4, ArrowLeft: -1, ArrowRight: 1 };
    if (event.key in moves) {
      event.preventDefault();
      const row = Math.floor(this.selectedCell / 4);
      const column = this.selectedCell % 4;
      if (event.key === "ArrowUp" && row > 0) this.selectedCell += moves[event.key];
      if (event.key === "ArrowDown" && row < 3) this.selectedCell += moves[event.key];
      if (event.key === "ArrowLeft" && column > 0) this.selectedCell += moves[event.key];
      if (event.key === "ArrowRight" && column < 3) this.selectedCell += moves[event.key];
      this.announce(`Selected row ${Math.floor(this.selectedCell / 4) + 1}, column ${(this.selectedCell % 4) + 1}.`);
      this.draw();
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      this.announce("Canvas cell selected. Choose a tool and solvent, then apply.");
    }
  }

  selectCanvasCell(event) {
    const bounds = this.canvas.getBoundingClientRect();
    const column = Math.min(3, Math.floor(((event.clientX - bounds.left) / bounds.width) * 4));
    const row = Math.min(3, Math.floor(((event.clientY - bounds.top) / bounds.height) * 4));
    this.selectedCell = row * 4 + column;
    this.canvas.focus();
    this.draw();
    this.announce(`Selected row ${row + 1}, column ${column + 1}.`);
  }

  selectTool(button) {
    document.querySelectorAll("[data-tool]").forEach((tool) => tool.setAttribute("aria-pressed", "false"));
    button.setAttribute("aria-pressed", "true");
    this.selectedTool = button.dataset.tool;
    document.querySelector("#selected-tool").textContent = button.textContent.trim();
  }

  updateMix() {
    ["water", "oil", "acid"].forEach((name) => {
      const value = document.querySelector(`#${name}`).value;
      document.querySelector(`#${name}-output`).textContent = `${value}%`;
    });
  }

  apply() {
    if (!this.selectedTool) {
      this.announce("Choose a tool before applying solvent.");
      return;
    }
    const mixture = ["water", "oil", "acid"].reduce((values, name) => {
      values[`${name}_ratio`] = Number(document.querySelector(`#${name}`).value);
      return values;
    }, {});
    this.moveLog.push({
      x: this.selectedCell % 4,
      y: Math.floor(this.selectedCell / 4),
      layer: this.currentLayer,
      solvent_mixture: mixture,
      tool: this.selectedTool
    });
    this.announce(
      `Move ${this.moveLog.length} queued locally for server verification in Step 5.`
    );
  }

  exportPng() {
    const download = document.createElement("a");
    download.href = this.canvas.toDataURL("image/png");
    download.download = "golden-valley-restoration.png";
    download.click();
  }

  announce(message) {
    document.querySelector("#game-status").textContent = message;
  }

  draw() {
    const { context: ctx, canvas } = this;
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#bd9c4f";
    ctx.fillRect(35, 28, width - 70, height - 56);
    ctx.fillStyle = "#f4e3ad";
    ctx.fillRect(50, 43, width - 100, height - 86);
    ctx.fillStyle = "#f6f0df";
    ctx.fillRect(65, 58, width - 130, height - 116);
    ctx.fillStyle = "#d5d6df";
    ctx.beginPath(); ctx.moveTo(65, 300); ctx.lineTo(200, 190); ctx.lineTo(310, 280); ctx.lineTo(430, 180); ctx.lineTo(535, 270); ctx.lineTo(535, 430); ctx.lineTo(65, 430); ctx.fill();
    ctx.fillStyle = "#abc1aa";
    ctx.fillRect(65, 325, 470, 170);
    ctx.fillStyle = "#849d78";
    ctx.beginPath(); ctx.moveTo(65, 460); ctx.quadraticCurveTo(180, 380, 290, 465); ctx.quadraticCurveTo(410, 380, 535, 450); ctx.lineTo(535, 605); ctx.lineTo(65, 605); ctx.fill();
    ctx.fillStyle = "#b7d5d8";
    ctx.beginPath(); ctx.moveTo(300, 330); ctx.quadraticCurveTo(410, 430, 280, 590); ctx.lineTo(210, 605); ctx.quadraticCurveTo(315, 470, 245, 400); ctx.fill();
    ctx.fillStyle = "#e7c978";
    ctx.beginPath(); ctx.arc(420, 135, 28, 0, Math.PI * 2); ctx.fill();
    for (let index = 0; index < 7; index += 1) {
      ctx.fillStyle = "#46654f";
      const x = 110 + index * 55;
      ctx.fillRect(x, 370 - (index % 3) * 25, 9, 90 + (index % 2) * 18);
      ctx.beginPath(); ctx.ellipse(x + 4, 350 - (index % 3) * 25, 24, 50, 0, 0, Math.PI * 2); ctx.fill();
    }
    ctx.fillStyle = "rgba(116, 91, 52, .45)";
    for (let index = 0; index < 8; index += 1) {
      ctx.beginPath(); ctx.arc(105 + (index * 59) % 420, 130 + (index * 91) % 410, 42, 0, Math.PI * 2); ctx.fill();
    }
    const cellWidth = (width - 130) / 4;
    const cellHeight = (height - 116) / 4;
    const row = Math.floor(this.selectedCell / 4);
    const column = this.selectedCell % 4;
    ctx.strokeStyle = "#b687f0";
    ctx.lineWidth = 6;
    ctx.strokeRect(65 + column * cellWidth, 58 + row * cellHeight, cellWidth, cellHeight);
  }
}

function drawResultCanvas() {
  const canvas = document.querySelector(".result-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const { width, height } = canvas;
  ctx.fillStyle = "#bd9c4f";
  ctx.fillRect(18, 18, width - 36, height - 36);
  ctx.fillStyle = "#f4e3ad";
  ctx.fillRect(30, 30, width - 60, height - 60);
  ctx.fillStyle = "#f6f0df";
  ctx.fillRect(43, 43, width - 86, height - 86);
  ctx.fillStyle = "#d5d6df";
  ctx.beginPath(); ctx.moveTo(43, 250); ctx.lineTo(130, 175); ctx.lineTo(210, 235); ctx.lineTo(300, 165); ctx.lineTo(397, 230); ctx.lineTo(397, 360); ctx.lineTo(43, 360); ctx.fill();
  ctx.fillStyle = "#abc1aa";
  ctx.fillRect(43, 280, 354, 105);
  ctx.fillStyle = "#849d78";
  ctx.beginPath(); ctx.moveTo(43, 360); ctx.quadraticCurveTo(150, 315, 230, 370); ctx.quadraticCurveTo(320, 315, 397, 365); ctx.lineTo(397, 467); ctx.lineTo(43, 467); ctx.fill();
  ctx.fillStyle = "#b7d5d8";
  ctx.beginPath(); ctx.moveTo(220, 285); ctx.quadraticCurveTo(315, 350, 210, 467); ctx.lineTo(150, 467); ctx.quadraticCurveTo(245, 360, 190, 325); ctx.fill();
  ctx.fillStyle = "#e7c978";
  ctx.beginPath(); ctx.arc(290, 105, 21, 0, Math.PI * 2); ctx.fill();
  for (let index = 0; index < 5; index += 1) {
    ctx.fillStyle = "#46654f";
    const x = 80 + index * 58;
    ctx.fillRect(x, 310 - (index % 2) * 20, 7, 70);
    ctx.beginPath(); ctx.ellipse(x + 3, 295 - (index % 2) * 20, 18, 36, 0, 0, Math.PI * 2); ctx.fill();
  }
}

if (document.querySelector("#painting-canvas")) {
  new RestorationUI();
} else {
  drawResultCanvas();
}
