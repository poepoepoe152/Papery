/** Shared tuning values for the office scene, kept in one place so layout and
 * movement code never hardcode magic numbers. */

export const TILE_SIZE = 32;

export const ROOM_COLS = 16;
export const ROOM_ROWS = 12;

export const ROOM_WIDTH = ROOM_COLS * TILE_SIZE;
export const ROOM_HEIGHT = ROOM_ROWS * TILE_SIZE;

export const PLAYER_SPEED = 140;

export const Depth = {
  Floor: 0,
  FloorDecoration: 1,
  Furniture: 2,
  Characters: 3,
  Walls: 4,
  Overlay: 5,
} as const;

export const Direction = {
  Down: "down",
  Up: "up",
  Left: "left",
  Right: "right",
} as const;
export type Direction = (typeof Direction)[keyof typeof Direction];

export const TEXTURE_KEYS = {
  floor: "tex-floor",
  wall: "tex-wall",
  deskTop: "tex-desk-top",
  deskFront: "tex-desk-front",
  chair: "tex-chair",
  plant: "tex-plant",
  rug: "tex-rug",
} as const;

/** Geometry of the character spritesheets in public/assets/characters —
 * see CREDITS.md for provenance. Each sheet is a fixed 7-column x 3-row
 * grid: row 0 faces down, row 1 faces up, row 2 faces left (right reuses
 * the left frames with the sprite horizontally flipped). */
export const CHAR_FRAME_WIDTH = 16;
export const CHAR_FRAME_HEIGHT = 32;
export const CHAR_SHEET_COLS = 7;
export const CHAR_DISPLAY_SCALE = 2;

export const CharacterVariant = {
  Char0: "char_0",
  Char1: "char_1",
  Char2: "char_2",
  Char3: "char_3",
  Char4: "char_4",
  Char5: "char_5",
} as const;
export type CharacterVariant = (typeof CharacterVariant)[keyof typeof CharacterVariant];

export const PLAYER_VARIANT: CharacterVariant = CharacterVariant.Char4;
