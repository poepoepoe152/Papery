import Phaser from "phaser";
import { TILE_SIZE } from "../constants/Constants";

/**
 * The environment (floor, walls, desks, chairs, plants, rug) is generated at
 * runtime from vector shapes, since no free furniture asset pack was
 * available. Character art is real hand-drawn spritesheets loaded from
 * public/assets/characters — see CREDITS.md and Animations.ts. Every
 * generated texture ends up as a normal key in the texture manager, so the
 * rest of the game never knows the environment art is procedural.
 */

/** Cheap deterministic hash so floor variants look random but are stable
 * across reloads (same col/row always picks the same tile variant). */
export function pickVariant(col: number, row: number, variants: number): number {
  const h = Math.imul(col * 374761393 + row * 668265263, 2654435761) >>> 0;
  return h % variants;
}

function newGraphics(scene: Phaser.Scene): Phaser.GameObjects.Graphics {
  return scene.make.graphics({ x: 0, y: 0 }, false);
}

function generateFloorTextures(scene: Phaser.Scene): void {
  const base = [0xe4d2a7, 0xdfcb9c, 0xe8d6ab];
  for (let variant = 0; variant < base.length; variant++) {
    const g = newGraphics(scene);
    g.fillStyle(base[variant], 1);
    g.fillRect(0, 0, TILE_SIZE, TILE_SIZE);
    g.lineStyle(1, 0xcbb489, 0.6);
    g.strokeRect(0.5, 0.5, TILE_SIZE - 1, TILE_SIZE - 1);
    g.fillStyle(0xcbb489, 0.35);
    g.fillRect(0, 10, TILE_SIZE, 1);
    g.fillRect(0, 21, TILE_SIZE, 1);
    g.generateTexture(`tex-floor-${variant}`, TILE_SIZE, TILE_SIZE);
    g.destroy();
  }
}

function generateWallTexture(scene: Phaser.Scene): void {
  const g = newGraphics(scene);
  g.fillStyle(0x7a6552, 1);
  g.fillRect(0, 0, TILE_SIZE, TILE_SIZE);
  g.lineStyle(1, 0x5c4a3a, 0.8);
  for (let row = 0; row < TILE_SIZE; row += 8) {
    const offset = (row / 8) % 2 === 0 ? 0 : 8;
    g.strokeRect(-offset, row, TILE_SIZE + 16, 8);
  }
  g.fillStyle(0x5c4a3a, 1);
  g.fillRect(0, TILE_SIZE - 3, TILE_SIZE, 3);
  g.generateTexture("tex-wall", TILE_SIZE, TILE_SIZE);
  g.destroy();
}

function generateDeskTexture(scene: Phaser.Scene): void {
  const w = TILE_SIZE * 2;
  const h = Math.floor(TILE_SIZE * 1.4);
  const g = newGraphics(scene);

  // Desktop surface
  g.fillStyle(0x8a5a34, 1);
  g.fillRoundedRect(0, 4, w, h - 12, 4);
  g.lineStyle(1, 0x5c3b1e, 1);
  g.strokeRoundedRect(0, 4, w, h - 12, 4);

  // Front panel (gives the desk depth/height so it reads as furniture)
  g.fillStyle(0x6e4526, 1);
  g.fillRect(2, h - 12, w - 4, 10);

  // Monitor
  g.fillStyle(0x2b2b2b, 1);
  g.fillRoundedRect(w / 2 - 12, h - 30, 24, 16, 2);
  g.fillStyle(0x6cc6e8, 1);
  g.fillRect(w / 2 - 9, h - 27, 18, 10);
  g.fillStyle(0x2b2b2b, 1);
  g.fillRect(w / 2 - 3, h - 14, 6, 4);

  // Keyboard
  g.fillStyle(0xd9d2c4, 1);
  g.fillRect(w / 2 - 10, h - 10, 20, 6);

  g.generateTexture("tex-desk", w, h);
  g.destroy();
}

function generateChairTexture(scene: Phaser.Scene): void {
  const g = newGraphics(scene);
  const w = 22;
  const h = 26;
  g.fillStyle(0x000000, 0.18);
  g.fillEllipse(w / 2, h - 3, 16, 6);
  g.fillStyle(0x4a4038, 1);
  g.fillRoundedRect(2, 2, w - 4, 10, 3);
  g.fillStyle(0x3a3128, 1);
  g.fillRoundedRect(4, 10, w - 8, 12, 3);
  g.generateTexture("tex-chair", w, h);
  g.destroy();
}

function generatePlantTexture(scene: Phaser.Scene): void {
  const g = newGraphics(scene);
  const w = 26;
  const h = 34;
  g.fillStyle(0x000000, 0.2);
  g.fillEllipse(w / 2, h - 3, 18, 6);
  g.fillStyle(0x8a5a34, 1);
  g.fillRoundedRect(5, h - 16, w - 10, 14, 2);
  g.fillStyle(0x3f7d4a, 1);
  g.fillEllipse(w / 2, h - 22, 20, 18);
  g.fillStyle(0x4f9457, 1);
  g.fillEllipse(w / 2 - 5, h - 26, 12, 14);
  g.fillEllipse(w / 2 + 6, h - 24, 12, 12);
  g.generateTexture("tex-plant", w, h);
  g.destroy();
}

function generateRugTexture(scene: Phaser.Scene): void {
  const w = TILE_SIZE * 3;
  const h = TILE_SIZE * 2;
  const g = newGraphics(scene);
  g.fillStyle(0xb2493f, 0.55);
  g.fillRoundedRect(0, 0, w, h, 10);
  g.lineStyle(3, 0x8f382f, 0.55);
  g.strokeRoundedRect(4, 4, w - 8, h - 8, 8);
  g.generateTexture("tex-rug", w, h);
  g.destroy();
}

function generateWhiteboardTexture(scene: Phaser.Scene): void {
  const w = TILE_SIZE * 2;
  const h = Math.floor(TILE_SIZE * 1.1);
  const g = newGraphics(scene);
  g.fillStyle(0x7a5638, 1);
  g.fillRoundedRect(0, 0, w, h, 4);
  g.fillStyle(0xf5f1e6, 1);
  g.fillRoundedRect(4, 4, w - 8, h - 8, 2);
  g.lineStyle(1, 0xd8cfb8, 1);
  g.strokeRoundedRect(4, 4, w - 8, h - 8, 2);
  g.generateTexture("tex-whiteboard", w, h);
  g.destroy();
}

function generateCorkboardTexture(scene: Phaser.Scene): void {
  const w = Math.floor(TILE_SIZE * 1.3);
  const h = Math.floor(TILE_SIZE * 1.1);
  const g = newGraphics(scene);
  g.fillStyle(0x8a6a3f, 1);
  g.fillRoundedRect(0, 0, w, h, 4);
  g.fillStyle(0xc9a06a, 1);
  g.fillRoundedRect(4, 4, w - 8, h - 8, 2);
  const notes = [0xe6c15c, 0xe07a5f, 0x81b29a];
  const positions = [
    [10, 10],
    [w - 26, 8],
    [16, h - 26],
  ];
  for (let i = 0; i < notes.length; i++) {
    g.fillStyle(notes[i], 1);
    g.fillRect(positions[i][0], positions[i][1], 16, 14);
  }
  g.generateTexture("tex-corkboard", w, h);
  g.destroy();
}

function generateWindowTexture(scene: Phaser.Scene): void {
  const w = TILE_SIZE * 2;
  const h = Math.floor(TILE_SIZE * 1.3);
  const g = newGraphics(scene);
  g.fillStyle(0x8a5a34, 1);
  g.fillRoundedRect(0, 0, w, h, 4);
  g.fillStyle(0x8fc7e8, 1);
  g.fillRect(6, 6, w - 12, h - 12);
  g.fillStyle(0xbfe0f2, 1);
  g.fillEllipse(w * 0.3, h * 0.35, 22, 10);
  g.fillEllipse(w * 0.68, h * 0.28, 18, 8);
  g.fillStyle(0x4f9457, 1);
  g.fillTriangle(w * 0.22, h - 8, w * 0.35, h - 30, w * 0.48, h - 8);
  g.fillStyle(0x3f7d4a, 1);
  g.fillTriangle(w * 0.55, h - 8, w * 0.68, h - 24, w * 0.81, h - 8);
  g.lineStyle(3, 0x8a5a34, 1);
  g.lineBetween(w / 2, 6, w / 2, h - 6);
  g.lineBetween(6, h / 2, w - 6, h / 2);
  g.generateTexture("tex-window", w, h);
  g.destroy();
}

function generateBookshelfTexture(scene: Phaser.Scene): void {
  const w = TILE_SIZE * 2;
  const h = TILE_SIZE * 2;
  const g = newGraphics(scene);
  g.fillStyle(0x000000, 0.2);
  g.fillEllipse(w / 2, h - 3, w - 10, 6);
  g.fillStyle(0x6e4526, 1);
  g.fillRoundedRect(0, 0, w, h - 4, 3);
  g.fillStyle(0x4a2f19, 1);
  g.fillRect(4, 4, w - 8, h - 12);

  const bookColors = [0xc44536, 0x4f7cac, 0x81b29a, 0xe6c15c, 0x9a6fb0, 0xe07a5f];
  const shelfYs = [8, h / 2 - 4];
  for (const shelfY of shelfYs) {
    let x = 8;
    let i = 0;
    while (x < w - 12) {
      const bw = 5 + (i % 3);
      g.fillStyle(bookColors[i % bookColors.length], 1);
      g.fillRect(x, shelfY, bw, 24);
      x += bw + 1;
      i++;
    }
    g.fillStyle(0x2f1d0f, 1);
    g.fillRect(4, shelfY + 26, w - 8, 3);
  }
  g.generateTexture("tex-bookshelf", w, h);
  g.destroy();
}

function generateCoffeeStationTexture(scene: Phaser.Scene): void {
  const w = Math.floor(TILE_SIZE * 1.6);
  const h = Math.floor(TILE_SIZE * 1.3);
  const g = newGraphics(scene);
  g.fillStyle(0x000000, 0.2);
  g.fillEllipse(w / 2, h - 3, w - 8, 6);
  g.fillStyle(0x6e4526, 1);
  g.fillRoundedRect(2, h - 20, w - 4, 18, 3);
  g.fillStyle(0x2b2b2b, 1);
  g.fillRoundedRect(8, h - 42, 20, 26, 3);
  g.fillStyle(0x4a4a4a, 1);
  g.fillRect(11, h - 38, 14, 8);
  g.fillStyle(0x2b2b2b, 1);
  g.fillRect(14, h - 30, 8, 10);
  g.fillStyle(0xd9d2c4, 1);
  g.fillRect(w - 20, h - 24, 10, 12);
  g.fillStyle(0x6e4526, 1);
  g.fillRect(w - 18, h - 22, 6, 8);
  g.generateTexture("tex-coffee-station", w, h);
  g.destroy();
}

function generateCouchTexture(scene: Phaser.Scene): void {
  const w = TILE_SIZE * 3;
  const h = Math.floor(TILE_SIZE * 1.4);
  const g = newGraphics(scene);
  g.fillStyle(0x000000, 0.2);
  g.fillEllipse(w / 2, h - 3, w - 12, 8);
  g.fillStyle(0xcfc8ba, 1);
  g.fillRoundedRect(0, 6, w, h - 14, 8);
  g.fillStyle(0xe4ded1, 1);
  g.fillRoundedRect(6, 0, w - 12, h * 0.55, 6);
  const cushionW = (w - 24) / 3;
  for (let i = 0; i < 3; i++) {
    g.fillStyle(0xdcd5c6, 1);
    g.fillRoundedRect(12 + i * (cushionW + 4), h * 0.3, cushionW, h * 0.4, 4);
  }
  g.fillStyle(0xc44536, 1);
  g.fillRoundedRect(14, h * 0.32, 14, 14, 3);
  g.generateTexture("tex-couch", w, h);
  g.destroy();
}

function generateCoffeeTableTexture(scene: Phaser.Scene): void {
  const w = Math.floor(TILE_SIZE * 1.6);
  const h = Math.floor(TILE_SIZE * 0.9);
  const g = newGraphics(scene);
  g.fillStyle(0x000000, 0.2);
  g.fillEllipse(w / 2, h - 2, w - 8, 6);
  g.fillStyle(0x8a5a34, 1);
  g.fillRoundedRect(0, 0, w, h - 8, 4);
  g.lineStyle(1, 0x5c3b1e, 1);
  g.strokeRoundedRect(0, 0, w, h - 8, 4);
  g.fillStyle(0x6e4526, 1);
  g.fillRect(4, h - 8, 4, 8);
  g.fillRect(w - 8, h - 8, 4, 8);
  g.fillStyle(0xd9d2c4, 1);
  g.fillRect(w / 2 - 8, 4, 12, 8);
  g.generateTexture("tex-coffee-table", w, h);
  g.destroy();
}

function generateSecondRugTexture(scene: Phaser.Scene): void {
  const w = TILE_SIZE * 3;
  const h = TILE_SIZE * 2;
  const g = newGraphics(scene);
  g.fillStyle(0x5c7a8a, 0.5);
  g.fillRoundedRect(0, 0, w, h, 10);
  g.lineStyle(3, 0x466170, 0.5);
  g.strokeRoundedRect(4, 4, w - 8, h - 8, 8);
  g.generateTexture("tex-rug-2", w, h);
  g.destroy();
}

function generatePetBedTexture(scene: Phaser.Scene): void {
  const w = 36;
  const h = 28;
  const g = newGraphics(scene);
  g.fillStyle(0x000000, 0.2);
  g.fillEllipse(w / 2, h - 3, w - 6, 6);
  g.fillStyle(0x8a5a34, 1);
  g.fillEllipse(w / 2, h / 2, w, h - 6);
  g.fillStyle(0xc9a06a, 1);
  g.fillEllipse(w / 2, h / 2, w - 10, h - 14);
  g.generateTexture("tex-pet-bed", w, h);
  g.destroy();
}

function generatePetTexture(scene: Phaser.Scene): void {
  const g = newGraphics(scene);
  const w = 20;
  const h = 14;
  g.fillStyle(0xd68a3c, 1);
  g.fillEllipse(w / 2, h / 2 + 1, w - 2, h - 4);
  g.fillStyle(0xb8712c, 1);
  g.fillEllipse(w * 0.28, h * 0.4, 6, 4);
  g.fillStyle(0x3a2a1e, 1);
  g.fillTriangle(w * 0.15, h * 0.25, w * 0.05, h * 0.02, w * 0.3, h * 0.15);
  g.generateTexture("tex-pet", w, h);
  g.destroy();
}

function generateFramedPhotoTexture(scene: Phaser.Scene): void {
  const w = 26;
  const h = 22;
  const g = newGraphics(scene);
  g.fillStyle(0x6e4526, 1);
  g.fillRoundedRect(0, 0, w, h, 2);
  g.fillStyle(0xdce6ef, 1);
  g.fillRect(3, 3, w - 6, h - 6);
  g.fillStyle(0xa9c2d9, 1);
  g.fillRect(3, h - 9, w - 6, 6);
  g.fillStyle(0xe6c15c, 1);
  g.fillCircle(w - 8, 8, 3);
  g.generateTexture("tex-photo", w, h);
  g.destroy();
}

function generateShadowTexture(scene: Phaser.Scene): void {
  const g = newGraphics(scene);
  g.fillStyle(0x000000, 0.28);
  g.fillEllipse(10, 5, 20, 8);
  g.generateTexture("tex-shadow", 20, 10);
  g.destroy();
}

export function generateAllTextures(scene: Phaser.Scene): void {
  generateFloorTextures(scene);
  generateWallTexture(scene);
  generateDeskTexture(scene);
  generateChairTexture(scene);
  generatePlantTexture(scene);
  generateRugTexture(scene);
  generateSecondRugTexture(scene);
  generateWhiteboardTexture(scene);
  generateCorkboardTexture(scene);
  generateWindowTexture(scene);
  generateBookshelfTexture(scene);
  generateCoffeeStationTexture(scene);
  generateCouchTexture(scene);
  generateCoffeeTableTexture(scene);
  generatePetBedTexture(scene);
  generatePetTexture(scene);
  generateFramedPhotoTexture(scene);
  generateShadowTexture(scene);
}
