import Phaser from "phaser";
import { gameConfig } from "./config/GameConfig";

const game = new Phaser.Game(gameConfig);

// Handy for debugging from the browser console; harmless in production.
declare global {
  interface Window {
    game: Phaser.Game;
  }
}
window.game = game;
