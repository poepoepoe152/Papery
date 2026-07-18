import Phaser from "phaser";
import { Depth } from "../constants/Constants";
import type { EmployeeConfig } from "../data/EmployeeData";

/** A seated employee. NPCs don't move in this milestone - workflow/AI comes
 * later - so they only need an idle animation and a name/role label. Desk
 * collision (set up in OfficeScene) already keeps the player from walking
 * into the seat, so the NPC itself carries no physics body. */
export class NPC extends Phaser.GameObjects.Container {
  constructor(scene: Phaser.Scene, x: number, y: number, employee: EmployeeConfig) {
    super(scene, x, y);
    scene.add.existing(this);
    this.setDepth(Depth.Characters);

    const sprite = scene.add.sprite(0, 0, `npc-${employee.id}-idle-0`);
    sprite.setOrigin(0.5, 0.92);
    sprite.play(`npc-${employee.id}-idle`);

    const label = scene.add.text(0, -34, `${employee.name}\n${employee.role}`, {
      fontFamily: "monospace",
      fontSize: "10px",
      color: "#ffffff",
      align: "center",
      backgroundColor: "#00000088",
      padding: { x: 4, y: 2 },
    });
    label.setOrigin(0.5, 1);

    this.add([sprite, label]);
  }
}
