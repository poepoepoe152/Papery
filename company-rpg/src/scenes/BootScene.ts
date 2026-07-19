import Phaser from "phaser";
import { CHAR_FRAME_HEIGHT, CHAR_FRAME_WIDTH, CharacterVariant } from "../constants/Constants";
import { generateAllTextures } from "../graphics/TextureFactory";
import { createAnimations } from "../graphics/Animations";

/** Loads the character spritesheets, generates the procedural environment
 * textures/animations, then hands off to the office room. Kept separate
 * from OfficeScene so "asset setup" and "gameplay" don't end up tangled in
 * one file. */
export class BootScene extends Phaser.Scene {
  constructor() {
    super("BootScene");
  }

  preload(): void {
    const loadingText = this.add
      .text(this.scale.width / 2, this.scale.height / 2, "Loading...", {
        fontFamily: "monospace",
        fontSize: "16px",
        color: "#e8d8b8",
      })
      .setOrigin(0.5);
    this.load.on("complete", () => loadingText.destroy());

    for (const variant of Object.values(CharacterVariant)) {
      this.load.spritesheet(variant, `assets/characters/${variant}.png`, {
        frameWidth: CHAR_FRAME_WIDTH,
        frameHeight: CHAR_FRAME_HEIGHT,
      });
    }
  }

  create(): void {
    generateAllTextures(this);
    createAnimations(this, Object.values(CharacterVariant));
    this.scene.start("OfficeScene");
  }
}
