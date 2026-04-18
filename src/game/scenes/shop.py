import math
import os
from pathlib import Path

import pygame


_REPO_ROOT = Path(__file__).resolve().parents[3]
_ASSETS = _REPO_ROOT / "assets"


def _load_scaled_button(name: str, size: tuple[int, int]) -> pygame.Surface:
    path = _ASSETS / name
    try:
        img = pygame.image.load(os.fsdecode(path)).convert_alpha()
        return pygame.transform.scale(img, size)
    except (pygame.error, FileNotFoundError, OSError):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((60, 120, 200, 230))
        pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 2)
        return surf


class ShopScene:
    def __init__(self, player):
        self.player = player
        self.font = pygame.font.SysFont(None, 36)

        self.background_color = (20, 20, 30)
        self.text_color = (255, 255, 255)

        self.fuel_img = _load_scaled_button("fuel_button.png", (200, 80))
        self.speed_img = _load_scaled_button("speed_button.png", (200, 80))

        self.fuel_rect = self.fuel_img.get_rect(topleft=(300, 200))
        self.speed_rect = self.speed_img.get_rect(topleft=(300, 320))

    def get_fuel_cost(self):
        n = self.player.fuel_upgrade_purchases + 1
        if n == 1:
            return 25
        return int(25 + ((n - 1) ** 2) * 15)

    def get_speed_cost(self):
        n = self.player.speed_upgrade_purchases + 1
        if n == 1:
            return 25
        return int(25 + ((n - 1) ** 2) * 15)

    def buy_fuel_upgrade(self):
        cost = self.get_fuel_cost()
        if self.player.coins >= cost:
            self.player.coins -= cost
            self.player.fuel *= 1.1
            self.player.fuel_upgrade_purchases += 1

    def buy_speed_upgrade(self):
        cost = self.get_speed_cost()
        if self.player.coins >= cost:
            self.player.coins -= cost
            self.player.speed *= 1.1
            self.player.speed_upgrade_purchases += 1

    def handle_event(self, event):
        """Returns ``\"gameplay\"`` when leaving the shop."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.fuel_rect.collidepoint(event.pos):
                self.buy_fuel_upgrade()
            if self.speed_rect.collidepoint(event.pos):
                self.buy_speed_upgrade()

        if event.type == pygame.KEYDOWN:
            if event.key in (
                pygame.K_ESCAPE,
                pygame.K_RETURN,
                pygame.K_SPACE,
                pygame.K_p,
                pygame.K_TAB,
            ):
                return "gameplay"

        return None

    def update(self, dt: float):
        pass

    def draw(self, screen):
        screen.fill(self.background_color)

        screen.blit(self.fuel_img, self.fuel_rect)
        screen.blit(self.speed_img, self.speed_rect)

        screen.blit(
            self.font.render(f"Coins: {self.player.coins}", True, self.text_color),
            (20, 20),
        )

        screen.blit(
            self.font.render(f"Fuel cap: {self.player.fuel:.2f}", True, self.text_color),
            (20, 60),
        )

        screen.blit(
            self.font.render(f"Speed: {self.player.speed:.2f}", True, self.text_color),
            (20, 100),
        )

        screen.blit(
            self.font.render(f"Cost: {self.get_fuel_cost()}", True, self.text_color),
            (self.fuel_rect.x, self.fuel_rect.y - 30),
        )

        screen.blit(
            self.font.render(f"Cost: {self.get_speed_cost()}", True, self.text_color),
            (self.speed_rect.x, self.speed_rect.y - 30),
        )

        hint = pygame.font.SysFont(None, 24).render(
            "TAB / SPACE / ENTER / P / ESC — Launch   |   Click buttons to upgrade",
            True,
            (180, 180, 200),
        )
        screen.blit(hint, (20, 420))
