import Phaser from "phaser";
import { CHAR_DISPLAY_SCALE, Depth } from "../constants/Constants";
import type { EmployeeConfig } from "../data/EmployeeData";
import { resolveAnim } from "../graphics/Animations";

/** A seated employee. NPCs don't move in this milestone - workflow/AI comes
 * later - so they only need an idle animation and a name/role label. Desk
 * collision (set up in OfficeScene) already keeps the player from walking
 * into the seat, so the NPC itself carries no physics body. */
export class NPC extends Phaser.GameObjects.Container {
  constructor(scene: Phaser.Scene, x: number, y: number, employee: EmployeeConfig) {
    super(scene, x, y);
    scene.add.existing(this);
    this.setDepth(Depth.Characters);

    const shadow = scene.add.image(0, -2, "tex-shadow");

    const { key, flipX } = resolveAnim(employee.variant, "idle", employee.facing);
    const sprite = scene.add.sprite(0, 0, employee.variant);
    sprite.setOrigin(0.5, 1);
    sprite.setScale(CHAR_DISPLAY_SCALE);
    sprite.setFlipX(flipX);
    sprite.play(key);

    const label = scene.add.text(0, -64, `${employee.name}\n${employee.role}`, {
      fontFamily: "monospace",
      fontSize: "10px",
      color: "#ffffff",
      align: "center",
      backgroundColor: "#00000088",
      padding: { x: 4, y: 2 },
    });
    label.setOrigin(0.5, 1);

    this.add([shadow, sprite, label]);
  }
}
