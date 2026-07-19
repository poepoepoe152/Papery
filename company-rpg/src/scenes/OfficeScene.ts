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
    this.buildWallDecor();
    const loungeFurniture = this.buildLounge();
    this.buildPetCorner();
    this.buildCoffeeStation();
    this.buildEmployees();

    this.player = new Player(this, ROOM_WIDTH / 2, ROOM_HEIGHT / 2);

    this.physics.add.collider(this.player, walls);
    this.physics.add.collider(this.player, desks);
    this.physics.add.collider(this.player, plants);
    this.physics.add.collider(this.player, loungeFurniture);

    this.cameras.main.setBounds(0, 0, ROOM_WIDTH, ROOM_HEIGHT);
    this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
    this.cameras.main.setZoom(2);
    this.cameras.main.roundPixels = true;

    this.scene.launch("UIScene");
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
      { col: ROOM_COLS - 2, row: 1 },
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

  /** Wall-mounted decoration along the back wall: photo, whiteboard,
   * corkboard, window, bookshelf. These are flat/thin, so they intentionally
   * carry no collision body - depth sorting alone makes the player render
   * in front of them when walking past, which reads correctly. */
  private buildWallDecor(): void {
    const wallDecorY = TILE_SIZE; // hang from the row0/row1 seam

    this.add.image(140, wallDecorY, "tex-photo").setDepth(Depth.Furniture);

    const whiteboardX = 196;
    this.add
      .image(whiteboardX, wallDecorY, "tex-whiteboard")
      .setOrigin(0.5, 0)
      .setDepth(Depth.Furniture);
    this.add
      .text(whiteboardX, wallDecorY + 14, "COMPANY MISSION", {
        fontFamily: "monospace",
        fontSize: "6px",
        color: "#2b2118",
        fontStyle: "bold",
        align: "center",
      })
      .setOrigin(0.5, 0)
      .setDepth(Depth.Overlay);
    this.add
      .text(whiteboardX, wallDecorY + 26, "small team\nbig impact", {
        fontFamily: "monospace",
        fontSize: "7px",
        color: "#4a4038",
        align: "center",
      })
      .setOrigin(0.5, 0)
      .setDepth(Depth.Overlay);

    this.add
      .image(258, wallDecorY, "tex-corkboard")
      .setOrigin(0.5, 0)
      .setDepth(Depth.Furniture);

    this.add
      .image(322, wallDecorY, "tex-window")
      .setOrigin(0.5, 0)
      .setDepth(Depth.Furniture);

    this.add
      .image(390, wallDecorY, "tex-bookshelf")
      .setOrigin(0.5, 0)
      .setDepth(Depth.Furniture);
  }

  /** Couch, coffee table and rug in the open floor between the two bottom
   * desks, backed onto the south wall - a small break area away from the
   * desks. The couch is bulky enough to collide with. */
  private buildLounge(): Phaser.Physics.Arcade.StaticGroup {
    const centerX = tileCenter(7.5, 0).x;

    const rug = tileCenter(7.5, 9.5);
    this.add.image(rug.x, rug.y, "tex-rug-2").setDepth(Depth.FloorDecoration);

    this.add.image(centerX, 290, "tex-coffee-table").setDepth(Depth.Furniture);

    const furniture = this.physics.add.staticGroup();
    const couch = furniture.create(
      centerX,
      ROOM_ROWS * TILE_SIZE - TILE_SIZE,
      "tex-couch",
    ) as Phaser.Physics.Arcade.Sprite;
    couch.setOrigin(0.5, 1);
    couch.setDepth(Depth.Furniture);
    const body = couch.body as Phaser.Physics.Arcade.StaticBody;
    body.setSize(couch.width - 12, 16);
    body.setOffset(6, couch.height - 16);
    body.updateFromGameObject();

    return furniture;
  }

  /** A sleeping office pet, tucked in the opposite corner from the lounge. */
  private buildPetCorner(): void {
    const spot = tileCenter(13, 9.5);
    this.add.image(spot.x, spot.y, "tex-pet-bed").setDepth(Depth.Furniture);
    const pet = this.add.image(spot.x, spot.y - 2, "tex-pet").setDepth(Depth.Furniture + 0.1);

    this.tweens.add({
      targets: pet,
      scaleY: 0.9,
      duration: 1400,
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut",
    });
  }

  /** A small coffee counter against the right-hand wall. */
  private buildCoffeeStation(): void {
    const { x } = tileCenter(13.5, 5);
    const bottomY = 6 * TILE_SIZE;
    this.add
      .image(x, bottomY, "tex-coffee-station")
      .setOrigin(0.5, 1)
      .setDepth(Depth.Furniture);
  }

  private buildEmployees(): void {
    for (const employee of EMPLOYEES) {
      const { col, row } = employee.deskTile;
      const { x, y } = tileCenter(col, row);
      new NPC(this, x, y, employee);
    }
  }
}
