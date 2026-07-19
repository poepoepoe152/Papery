import Phaser from "phaser";
import { CHAR_SHEET_COLS, CharacterVariant, Direction } from "../constants/Constants";

/**
 * Builds idle/walk animations for a character spritesheet (see CREDITS.md).
 * Each sheet is a 7-col x 3-row grid: row 0 faces down, row 1 faces up,
 * row 2 faces left. There is no dedicated right-facing row - callers mirror
 * the left-facing animations with sprite.setFlipX(true) instead.
 */

const ROW = { Down: 0, Up: 1, Left: 2 } as const;

const frame = (row: number, col: number) => row * CHAR_SHEET_COLS + col;

function buildForVariant(scene: Phaser.Scene, variant: CharacterVariant): void {
  const idleFrameRate = 2;
  const walkFrameRate = 8;

  scene.anims.create({
    key: `${variant}-idle-down`,
    frames: scene.anims.generateFrameNumbers(variant, {
      frames: [frame(ROW.Down, 0), frame(ROW.Down, 1)],
    }),
    frameRate: idleFrameRate,
    repeat: -1,
  });
  scene.anims.create({
    key: `${variant}-walk-down`,
    frames: scene.anims.generateFrameNumbers(variant, {
      frames: [frame(ROW.Down, 3), frame(ROW.Down, 4)],
    }),
    frameRate: walkFrameRate,
    repeat: -1,
  });

  scene.anims.create({
    key: `${variant}-idle-up`,
    frames: scene.anims.generateFrameNumbers(variant, {
      frames: [frame(ROW.Up, 0), frame(ROW.Up, 1)],
    }),
    frameRate: idleFrameRate,
    repeat: -1,
  });
  scene.anims.create({
    key: `${variant}-walk-up`,
    frames: scene.anims.generateFrameNumbers(variant, {
      frames: [frame(ROW.Up, 3), frame(ROW.Up, 4)],
    }),
    frameRate: walkFrameRate,
    repeat: -1,
  });

  scene.anims.create({
    key: `${variant}-idle-left`,
    frames: scene.anims.generateFrameNumbers(variant, {
      frames: [frame(ROW.Left, 0), frame(ROW.Left, 1)],
    }),
    frameRate: idleFrameRate,
    repeat: -1,
  });
  scene.anims.create({
    key: `${variant}-walk-left`,
    frames: scene.anims.generateFrameNumbers(variant, {
      frames: [frame(ROW.Left, 2), frame(ROW.Left, 3), frame(ROW.Left, 4), frame(ROW.Left, 5)],
    }),
    frameRate: walkFrameRate,
    repeat: -1,
  });
}

export function createAnimations(scene: Phaser.Scene, variants: CharacterVariant[]): void {
  const unique = [...new Set(variants)];
  for (const variant of unique) {
    buildForVariant(scene, variant);
  }
}

/** The spritesheet has no right-facing row, so Right reuses Left mirrored. */
export function resolveAnim(
  variant: CharacterVariant,
  state: "idle" | "walk",
  facing: Direction,
): { key: string; flipX: boolean } {
  const row = facing === Direction.Right ? Direction.Left : facing;
  return { key: `${variant}-${state}-${row}`, flipX: facing === Direction.Right };
}
