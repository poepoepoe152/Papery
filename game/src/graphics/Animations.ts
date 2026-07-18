import Phaser from "phaser";
import { Direction } from "../constants/Constants";
import { EMPLOYEES } from "../data/EmployeeData";

/**
 * Builds every animation from the single-frame textures produced by
 * TextureFactory. Phaser allows animation frames to reference different
 * texture keys directly, so no spritesheet packing step is needed.
 */
export function createAnimations(scene: Phaser.Scene): void {
  const directions = [Direction.Down, Direction.Up, Direction.Left, Direction.Right];

  for (const facing of directions) {
    scene.anims.create({
      key: `player-idle-${facing}`,
      frames: [
        { key: `player-idle-${facing}-0` },
        { key: `player-idle-${facing}-1` },
      ],
      frameRate: 2,
      repeat: -1,
    });

    scene.anims.create({
      key: `player-walk-${facing}`,
      frames: [
        { key: `player-walk-${facing}-0` },
        { key: `player-walk-${facing}-1` },
      ],
      frameRate: 6,
      repeat: -1,
    });
  }

  for (const employee of EMPLOYEES) {
    scene.anims.create({
      key: `npc-${employee.id}-idle`,
      frames: [
        { key: `npc-${employee.id}-idle-0` },
        { key: `npc-${employee.id}-idle-1` },
      ],
      frameRate: 1.5,
      repeat: -1,
    });
  }
}
