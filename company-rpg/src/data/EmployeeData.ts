import { CharacterVariant, Direction } from "../constants/Constants";

export type Role = "Founder" | "Developer" | "Designer" | "Marketing";

export interface EmployeeConfig {
  id: string;
  name: string;
  role: Role;
  /** Which character spritesheet this employee uses (see CREDITS.md). */
  variant: CharacterVariant;
  /** Desk position in tile coordinates. */
  deskTile: { col: number; row: number };
  /** Which way the employee faces while seated at their desk. */
  facing: Direction;
}

export const EMPLOYEES: EmployeeConfig[] = [
  {
    id: "founder",
    name: "Ava",
    role: "Founder",
    variant: CharacterVariant.Char5,
    deskTile: { col: 3, row: 3 },
    facing: Direction.Down,
  },
  {
    id: "developer",
    name: "Ren",
    role: "Developer",
    variant: CharacterVariant.Char0,
    deskTile: { col: 12, row: 3 },
    facing: Direction.Down,
  },
  {
    id: "designer",
    name: "Sol",
    role: "Designer",
    variant: CharacterVariant.Char1,
    deskTile: { col: 3, row: 8 },
    facing: Direction.Down,
  },
  {
    id: "marketing",
    name: "Kai",
    role: "Marketing",
    variant: CharacterVariant.Char2,
    deskTile: { col: 12, row: 8 },
    facing: Direction.Down,
  },
];
