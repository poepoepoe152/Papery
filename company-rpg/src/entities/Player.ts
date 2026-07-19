import Phaser from "phaser";
import { CHAR_DISPLAY_SCALE, Depth, Direction, PLAYER_SPEED, PLAYER_VARIANT } from "../constants/Constants";
import { resolveAnim } from "../graphics/Animations";

type WasdKeys = {
  up: Phaser.Input.Keyboard.Key;
  down: Phaser.Input.Keyboard.Key;
  left: Phaser.Input.Keyboard.Key;
  right: Phaser.Input.Keyboard.Key;
};

/** The controllable character. Movement is grid-free (free-walk), driven by
 * WASD input each frame and resolved through Arcade physics for collision. */
export class Player extends Phaser.Physics.Arcade.Sprite {
  private readonly keys: WasdKeys;
  private readonly shadow: Phaser.GameObjects.Image;
  private facing: Direction = Direction.Down;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    super(scene, x, y, PLAYER_VARIANT);

    scene.add.existing(this);
    scene.physics.add.existing(this);

    this.setOrigin(0.5, 1);
    this.setScale(CHAR_DISPLAY_SCALE);
    this.setDepth(Depth.Characters);

    this.shadow = scene.add.image(x, y, "tex-shadow").setDepth(Depth.Characters - 1);

    const body = this.body as Phaser.Physics.Arcade.Body;
    body.setSize(18, 14);
    body.setOffset(7, 48);
    body.setCollideWorldBounds(true);

    const keyboard = scene.input.keyboard;
    if (!keyboard) {
      throw new Error("Keyboard input plugin is unavailable");
    }
    this.keys = {
      up: keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.W),
      down: keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.S),
      left: keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.A),
      right: keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.D),
    };

    const idle = resolveAnim(PLAYER_VARIANT, "idle", this.facing);
    this.setFlipX(idle.flipX);
    this.play(idle.key);
  }

  update(): void {
    const body = this.body as Phaser.Physics.Arcade.Body;
    const { up, down, left, right } = this.keys;

    let vx = 0;
    let vy = 0;
    if (left.isDown) vx -= 1;
    if (right.isDown) vx += 1;
    if (up.isDown) vy -= 1;
    if (down.isDown) vy += 1;

    const isMoving = vx !== 0 || vy !== 0;

    if (isMoving) {
      const length = Math.hypot(vx, vy);
      body.setVelocity((vx / length) * PLAYER_SPEED, (vy / length) * PLAYER_SPEED);

      if (Math.abs(vx) > Math.abs(vy)) {
        this.facing = vx < 0 ? Direction.Left : Direction.Right;
      } else if (vy !== 0) {
        this.facing = vy < 0 ? Direction.Up : Direction.Down;
      }
    } else {
      body.setVelocity(0, 0);
    }

    const { key, flipX } = resolveAnim(PLAYER_VARIANT, isMoving ? "walk" : "idle", this.facing);
    this.setFlipX(flipX);
    if (this.anims.currentAnim?.key !== key) {
      this.play(key, true);
    }

    this.shadow.setPosition(this.x, this.y - 2);
  }
}
