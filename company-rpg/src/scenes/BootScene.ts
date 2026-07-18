import Phaser from "phaser";
import { generateAllTextures } from "../graphics/TextureFactory";
import { createAnimations } from "../graphics/Animations";

/** Generates every texture and animation the game needs up front, then hands
 * off to the office room. Kept separate from OfficeScene so "asset setup"
 * and "gameplay" don't end up tangled in one file. */
export class BootScene extends Phaser.Scene {
  constructor() {
    super("BootScene");
  }

  create(): void {
    generateAllTextures(this);
    createAnimations(this);
    this.scene.start("OfficeScene");
  }
}
