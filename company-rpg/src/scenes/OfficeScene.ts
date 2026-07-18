import Phaser from "phaser";
import {
  Depth,
  ROOM_COLS,
  ROOM_HEIGHT,
  ROOM_ROWS,
  ROOM_WIDTH,
  TILE_SIZE,
} from "../constants/Constants";
import { EMPLOYEES } from "../data/EmployeeData";
import { pickVariant } from "../graphics/TextureFactory";
import { Player } from "../entities/Player";
import { NPC } from "../entities/NPC";

const tileCenter = (col: number, row: number) => ({
  x: col * TILE_SIZE + TILE_SIZE / 2,
  y: row * TILE_SIZE + TILE_SIZE / 2,
});

/** The single startup office room: floor/walls, four desks with seated
 * employees, and the player-controlled character. */
export class OfficeScene extends Phaser.Scene {
  private player!: Player;

  constructor() {
    super("OfficeScene");
  }

  create(): void {
    this.physics.world.setBounds(0, 0, ROOM_WIDTH, ROOM_HEIGHT);

    this.buildFloor();
    const walls = this.buildWalls();
    this.buildRug();
    const desks = this.buildDesksAndChairs();
    const plants = this.buildPlants();
    this.buildEmployees();

    this.player = new Player(this, ROOM_WIDTH / 2, ROOM_HEIGHT / 2);

    this.physics.add.collider(this.player, walls);
    this.physics.add.collider(this.player, desks);
    this.physics.add.collider(this.player, plants);

    this.cameras.main.setBounds(0, 0, ROOM_WIDTH, ROOM_HEIGHT);
    this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
    this.cameras.main.setZoom(2);
    this.cameras.main.roundPixels = true;
  }

  update(): void {
    this.player.update();
  }

  private buildFloor(): void {
    for (let row = 0; row < ROOM_ROWS; row++) {
      for (let col = 0; col < ROOM_COLS; col++) {
        const variant = pickVariant(col, row, 3);
        this.add
          .image(col * TILE_SIZE, row * TILE_SIZE, `tex-floor-${variant}`)
          .setOrigin(0, 0)
          .setDepth(Depth.Floor);
      }
    }
  }

  private buildWalls(): Phaser.Physics.Arcade.StaticGroup {
    const walls = this.physics.add.staticGroup();

    for (let row = 0; row < ROOM_ROWS; row++) {
      for (let col = 0; col < ROOM_COLS; col++) {
        const isPerimeter =
          row === 0 || row === ROOM_ROWS - 1 || col === 0 || col === ROOM_COLS - 1;
        if (!isPerimeter) continue;

        const { x, y } = tileCenter(col, row);
        const wall = walls.create(x, y, "tex-wall") as Phaser.Physics.Arcade.Sprite;
        wall.setDepth(Depth.Walls);
      }
    }

    return walls;
  }

  private buildRug(): void {
    const { x, y } = tileCenter(EMPLOYEES[0].deskTile.col, EMPLOYEES[0].deskTile.row + 1);
    this.add.image(x, y + TILE_SIZE / 2, "tex-rug").setDepth(Depth.FloorDecoration);
  }

  private buildDesksAndChairs(): Phaser.Physics.Arcade.StaticGroup {
    const desks = this.physics.add.staticGroup();

    for (const employee of EMPLOYEES) {
      const { col, row } = employee.deskTile;
      const { x } = tileCenter(col, row);
      const deskBottomY = row * TILE_SIZE + TILE_SIZE;

      const desk = desks.create(x, deskBottomY, "tex-desk") as Phaser.Physics.Arcade.Sprite;
      desk.setOrigin(0.5, 1);
      desk.setDepth(Depth.Furniture);
      const body = desk.body as Phaser.Physics.Arcade.StaticBody;
      body.setSize(desk.width - 8, 18);
      body.setOffset(4, desk.height - 18);
      body.updateFromGameObject();

      this.add
        .image(x, row * TILE_SIZE + TILE_SIZE * 0.75, "tex-chair")
        .setDepth(Depth.Furniture);
    }

    return desks;
  }

  private buildPlants(): Phaser.Physics.Arcade.StaticGroup {
    const plants = this.physics.add.staticGroup();
    const spots: Array<{ col: number; row: number }> = [
      { col: 1, row: 1 },
      { col: ROOM_COLS - 2, row: ROOM_ROWS - 2 },
    ];

    for (const spot of spots) {
      const { x } = tileCenter(spot.col, spot.row);
      const bottomY = spot.row * TILE_SIZE + TILE_SIZE;
      const plant = plants.create(x, bottomY, "tex-plant") as Phaser.Physics.Arcade.Sprite;
      plant.setOrigin(0.5, 1);
      plant.setDepth(Depth.Furniture);
      const body = plant.body as Phaser.Physics.Arcade.StaticBody;
      body.setSize(plant.width - 8, 10);
      body.setOffset(4, plant.height - 12);
      body.updateFromGameObject();
    }

    return plants;
  }

  private buildEmployees(): void {
    for (const employee of EMPLOYEES) {
      const { col, row } = employee.deskTile;
      const { x, y } = tileCenter(col, row);
      new NPC(this, x, y, employee);
    }
  }
}
