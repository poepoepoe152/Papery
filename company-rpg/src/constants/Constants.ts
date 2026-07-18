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
