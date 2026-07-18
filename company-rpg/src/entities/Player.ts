import Phaser from "phaser";
import { Direction, PLAYER_SPEED } from "../constants/Constants";

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
  private facing: Direction = Direction.Down;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    super(scene, x, y, "player-idle-down-0");

    scene.add.existing(this);
    scene.physics.add.existing(this);

    this.setOrigin(0.5, 0.92);
    this.setDepth(3);

    const body = this.body as Phaser.Physics.Arcade.Body;
    body.setSize(16, 10);
    body.setOffset(8, 28);
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

    this.play(`player-idle-${this.facing}`);
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

    const animKey = `player-${isMoving ? "walk" : "idle"}-${this.facing}`;
    if (this.anims.currentAnim?.key !== animKey) {
      this.play(animKey, true);
    }
  }
}
