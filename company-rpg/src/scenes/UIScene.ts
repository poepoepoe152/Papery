import Phaser from "phaser";

/**
 * Fixed HUD overlay drawn on top of OfficeScene. It runs as its own Scene
 * (launched from OfficeScene.create) so its camera never scrolls or follows
 * the player - everything added here is already in screen space. Purely
 * decorative for this milestone: no workflow/gameplay logic is wired to it
 * yet, per the "don't implement workflow" scope.
 */
export class UIScene extends Phaser.Scene {
  constructor() {
    super("UIScene");
  }

  create(): void {
    const { width, height } = this.scale;

    this.buildTodaysGoal(16, 16);
    this.buildDayTime(width - 190, 16);
    this.buildCurrency(width - 190, 84);
    this.buildProjectStatus(width - 220, height - 96);
  }

  private panel(x: number, y: number, w: number, h: number): Phaser.GameObjects.Graphics {
    const g = this.add.graphics();
    g.fillStyle(0xf5efdd, 0.92);
    g.fillRoundedRect(x, y, w, h, 6);
    g.lineStyle(2, 0x8a5a34, 1);
    g.strokeRoundedRect(x, y, w, h, 6);
    return g;
  }

  private label(
    x: number,
    y: number,
    text: string,
    opts: Partial<Phaser.Types.GameObjects.Text.TextStyle> = {},
  ): Phaser.GameObjects.Text {
    return this.add.text(x, y, text, {
      fontFamily: "monospace",
      fontSize: "10px",
      color: "#2b2118",
      ...opts,
    });
  }

  private checkbox(x: number, y: number, checked: boolean): void {
    const g = this.add.graphics();
    g.lineStyle(1.5, 0x2b2118, 1);
    g.strokeRect(x, y, 10, 10);
    if (checked) {
      g.fillStyle(0x4f9457, 1);
      g.fillRect(x + 2, y + 2, 6, 6);
    }
  }

  private buildTodaysGoal(x: number, y: number): void {
    const w = 190;
    const h = 96;
    this.panel(x, y, w, h);
    this.label(x + 10, y + 8, "TODAY'S GOAL", { fontStyle: "bold" });

    const items: Array<{ text: string; done: boolean }> = [
      { text: "Ship a new feature", done: false },
      { text: "Review designs", done: false },
      { text: "Answer customer messages", done: true },
    ];

    items.forEach((item, i) => {
      const rowY = y + 30 + i * 20;
      this.checkbox(x + 10, rowY, item.done);
      this.label(x + 26, rowY - 1, item.text, { fontSize: "9px" });
    });
  }

  private buildDayTime(x: number, y: number): void {
    const w = 170;
    const h = 60;
    this.panel(x, y, w, h);

    const sun = this.add.graphics();
    sun.fillStyle(0xf2c14e, 1);
    sun.fillCircle(x + 22, y + 30, 10);
    sun.lineStyle(2, 0xf2c14e, 1);
    for (let i = 0; i < 8; i++) {
      const angle = (i / 8) * Math.PI * 2;
      const x1 = x + 22 + Math.cos(angle) * 14;
      const y1 = y + 30 + Math.sin(angle) * 14;
      const x2 = x + 22 + Math.cos(angle) * 18;
      const y2 = y + 30 + Math.sin(angle) * 18;
      sun.lineBetween(x1, y1, x2, y2);
    }

    this.label(x + 46, y + 12, "Day 1", { fontStyle: "bold" });
    this.label(x + 46, y + 30, "09:30 AM", { fontSize: "9px", color: "#4a4038" });
  }

  private buildCurrency(x: number, y: number): void {
    const w = 170;
    const h = 32;
    this.panel(x, y, w, h);

    const coin = this.add.graphics();
    coin.fillStyle(0xe6c15c, 1);
    coin.fillCircle(x + 20, y + 16, 9);
    coin.lineStyle(1, 0x8a6a3f, 1);
    coin.strokeCircle(x + 20, y + 16, 9);
    this.label(x + 16, y + 10, "G", { fontStyle: "bold", fontSize: "10px" });

    this.label(x + 38, y + 10, "1,000", { fontStyle: "bold", fontSize: "12px" });
  }

  private buildProjectStatus(x: number, y: number): void {
    const w = 204;
    const h = 74;
    this.panel(x, y, w, h);
    this.label(x + 10, y + 8, "PROJECT", { fontStyle: "bold" });
    this.label(x + 10, y + 24, "MVP Launch", { fontSize: "9px", color: "#4a4038" });

    this.label(x + 10, y + 42, "STATUS", { fontStyle: "bold", fontSize: "9px" });

    const barX = x + 10;
    const barY = y + 58;
    const barW = w - 60;
    const barH = 10;
    const percent = 0.35;

    const track = this.add.graphics();
    track.fillStyle(0xd8cfb8, 1);
    track.fillRoundedRect(barX, barY, barW, barH, 3);
    track.fillStyle(0x4f9457, 1);
    track.fillRoundedRect(barX, barY, barW * percent, barH, 3);
    track.lineStyle(1, 0x8a6a3f, 1);
    track.strokeRoundedRect(barX, barY, barW, barH, 3);

    this.label(barX + barW + 8, barY - 1, "35%", { fontSize: "9px" });
  }
}
