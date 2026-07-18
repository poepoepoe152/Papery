import Phaser from "phaser";
import { Direction, TILE_SIZE } from "../constants/Constants";
import { EMPLOYEES } from "../data/EmployeeData";

/**
 * All game art is generated at runtime from vector shapes instead of loaded
 * image files, since no external asset pipeline exists for this milestone.
 * Every texture ends up as a normal key in the texture manager, so the rest
 * of the game (scenes, entities) never knows the art is procedural.
 */

const SKIN_TONE = 0xf2c9a1;
const OUTLINE = 0x2b2118;

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

interface CharacterFrameOptions {
  key: string;
  bodyColor: number;
  facing: Direction;
  bobPx: number;
  footSpreadPx: number;
  seated: boolean;
}

const CHAR_W = 32;
const CHAR_H = 40;

function drawCharacterFrame(g: Phaser.GameObjects.Graphics, opts: CharacterFrameOptions): void {
  const { bodyColor, facing, bobPx, footSpreadPx, seated } = opts;
  const cx = CHAR_W / 2;
  const bodyTop = (seated ? 16 : 14) + bobPx;
  const bodyBottom = 34 + (seated ? -2 : 0);
  const bodyH = bodyBottom - bodyTop;
  const headCy = bodyTop - 4;

  // Shadow anchored to the floor regardless of bob so the character never
  // looks like it floats.
  g.fillStyle(0x000000, 0.22);
  g.fillEllipse(cx, 37, 16, 5);

  // Feet peek out below the body only while standing/walking.
  if (!seated) {
    g.fillStyle(0x3a2f26, 1);
    g.fillEllipse(cx - 5 - footSpreadPx, 33, 6, 4);
    g.fillEllipse(cx + 5 + footSpreadPx, 33, 6, 4);
  }

  // Body
  g.fillStyle(bodyColor, 1);
  g.fillRoundedRect(cx - 9, bodyTop, 18, bodyH, 6);
  g.lineStyle(1, OUTLINE, 0.4);
  g.strokeRoundedRect(cx - 9, bodyTop, 18, bodyH, 6);

  // Arms (small side stripes, mostly decorative)
  g.fillStyle(bodyColor, 1);
  g.fillRoundedRect(cx - 12, bodyTop + 3, 4, bodyH - 8, 2);
  g.fillRoundedRect(cx + 8, bodyTop + 3, 4, bodyH - 8, 2);

  // Head
  g.fillStyle(SKIN_TONE, 1);
  g.fillCircle(cx, headCy, 7);
  g.lineStyle(1, OUTLINE, 0.35);
  g.strokeCircle(cx, headCy, 7);

  // Simple hair cap so the back-of-head (facing up) reads differently
  // from the face (facing down).
  g.fillStyle(0x3a2a1e, 1);
  g.fillEllipse(cx, headCy - 4, 13, 8);

  // Face features, placed according to facing direction.
  g.fillStyle(OUTLINE, 0.85);
  if (facing === Direction.Down) {
    g.fillCircle(cx - 3, headCy + 1, 1.2);
    g.fillCircle(cx + 3, headCy + 1, 1.2);
  } else if (facing === Direction.Left) {
    g.fillCircle(cx - 4, headCy + 1, 1.2);
  } else if (facing === Direction.Right) {
    g.fillCircle(cx + 4, headCy + 1, 1.2);
  }
  // Direction.Up shows only the hair/back of the head - no face drawn.
}

function generateCharacterTextures(scene: Phaser.Scene): void {
  const directions = [Direction.Down, Direction.Up, Direction.Left, Direction.Right];
  const g = newGraphics(scene);

  const playerColor = 0xe8b23a;
  for (const facing of directions) {
    for (let frame = 0; frame < 2; frame++) {
      g.clear();
      drawCharacterFrame(g, {
        key: "",
        bodyColor: playerColor,
        facing,
        bobPx: frame === 1 ? -1 : 0,
        footSpreadPx: 0,
        seated: false,
      });
      g.generateTexture(`player-idle-${facing}-${frame}`, CHAR_W, CHAR_H);

      g.clear();
      drawCharacterFrame(g, {
        key: "",
        bodyColor: playerColor,
        facing,
        bobPx: frame === 1 ? -1 : 0,
        footSpreadPx: frame === 1 ? 3 : -3,
        seated: false,
      });
      g.generateTexture(`player-walk-${facing}-${frame}`, CHAR_W, CHAR_H);
    }
  }

  for (const employee of EMPLOYEES) {
    for (let frame = 0; frame < 2; frame++) {
      g.clear();
      drawCharacterFrame(g, {
        key: "",
        bodyColor: employee.color,
        facing: employee.facing,
        bobPx: frame === 1 ? -1 : 0,
        footSpreadPx: 0,
        seated: true,
      });
      g.generateTexture(`npc-${employee.id}-idle-${frame}`, CHAR_W, CHAR_H);
    }
  }

  g.destroy();
}

export function generateAllTextures(scene: Phaser.Scene): void {
  generateFloorTextures(scene);
  generateWallTexture(scene);
  generateDeskTexture(scene);
  generateChairTexture(scene);
  generatePlantTexture(scene);
  generateRugTexture(scene);
  generateCharacterTextures(scene);
}

export const CHARACTER_SIZE = { width: CHAR_W, height: CHAR_H };
