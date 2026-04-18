"""
game.py — entry point and scene orchestration for the pygame mini-game.

Starts in the shop; press SPACE / ENTER / P / ESC to fly. During flight,
ESC returns to the shop. Coins earned from altitude are shared across scenes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

# Ensure `src` is importable when running this file directly
_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from game.entities.player import Player
from game.scenes.gameplay import FPS, GameplayScene, H, W
from game.scenes.shop import ShopScene


class Game:
    """Owns the window, shared :class:`Player`, and active scene."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Launch to Space — Shop & Fly")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()

        self.player = Player(x=0.0, y=0.0)
        self.scene: ShopScene | GameplayScene = ShopScene(self.player)

    def _goto_shop(self):
        self.scene = ShopScene(self.player)

    def _goto_gameplay(self):
        self.scene = GameplayScene(self.screen, shared_player=self.player)

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                next_scene = None
                if isinstance(self.scene, ShopScene):
                    next_scene = self.scene.handle_event(event)
                elif isinstance(self.scene, GameplayScene):
                    next_scene = self.scene.handle_event(event)

                if next_scene == "gameplay":
                    self._goto_gameplay()
                elif next_scene == "shop":
                    self._goto_shop()

            self.scene.update(dt)
            if isinstance(self.scene, GameplayScene):
                self.scene.draw()
            else:
                self.scene.draw(self.screen)
            pygame.display.flip()


def main():
    Game().run()


if __name__ == "__main__":
    main()
