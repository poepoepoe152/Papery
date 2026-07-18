import { Direction } from "../constants/Constants";

export type Role = "Founder" | "Developer" | "Designer" | "Marketing";

export interface EmployeeConfig {
  id: string;
  name: string;
  role: Role;
  /** Body color for the generated sprite, one per role. */
  color: number;
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
    color: 0xd94f4f,
    deskTile: { col: 3, row: 3 },
    facing: Direction.Down,
  },
  {
    id: "developer",
    name: "Ren",
    role: "Developer",
    color: 0x4f8fd9,
    deskTile: { col: 12, row: 3 },
    facing: Direction.Down,
  },
  {
    id: "designer",
    name: "Sol",
    role: "Designer",
    color: 0x9a4fd9,
    deskTile: { col: 3, row: 8 },
    facing: Direction.Down,
  },
  {
    id: "marketing",
    name: "Kai",
    role: "Marketing",
    color: 0x4fd98f,
    deskTile: { col: 12, row: 8 },
    facing: Direction.Down,
  },
];
