import os
from pathlib import Path

import pygame


_THIS_DIR = Path(__file__).resolve().parent
_SRC_ROOT = _THIS_DIR.parents[1]   # src/game/scenes -> src
_ASSETS = _SRC_ROOT / "assets"


def _load_scaled_button(name: str, size: tuple[int, int]) -> pygame.Surface:
    path = _ASSETS / name
    try:
        print(f"Loading image: {path}")
        img = pygame.image.load(os.fsdecode(path)).convert_alpha()
        return pygame.transform.scale(img, size)
    except (pygame.error, FileNotFoundError, OSError) as e:
        print(f"Failed to load image: {path} | Error: {e}")
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((60, 120, 200, 230))
        pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 2)
        return surf


class ShopScene:
    def __init__(self, player):
        self.player = player
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)

        self.background_color = (20, 20, 30)
        self.text_color = (255, 255, 255)
        self.button_size = (200, 80)

        if not hasattr(self.player, "pickaxe_upgrades"):
            self.player.pickaxe_upgrade = 0
        if not hasattr(self.player, "fuel_upgrade_purchases"):
            self.player.fuel_upgrade_purchases = 0
        if not hasattr(self.player, "speed_upgrade_purchases"):
            self.player.speed_upgrade_purchases = 0

        self.fuel_imgs = [
            _load_scaled_button("button/fuel1.PNG", self.button_size),  # unpressed
            _load_scaled_button("button/fuel2.PNG", self.button_size),  # pressed
        ]

        self.speed_imgs = [
            _load_scaled_button("button/speed1.PNG", self.button_size),  # unpressed
            _load_scaled_button("button/speed2.PNG", self.button_size),  # pressed
        ]

        self.pickaxe_imgs = [
            _load_scaled_button("button/pickaxe1.PNG", self.button_size),
            _load_scaled_button("button/pickaxe2.PNG", self.button_size),
            _load_scaled_button("button/pickaxe3.PNG", self.button_size),
            _load_scaled_button("button/pickaxe4.PNG", self.button_size),
        ]

        self.fuel_pressed = False
        self.speed_pressed = False

        self.fuel_rect = self.fuel_imgs[0].get_rect(topleft=(300, 200))
        self.speed_rect = self.speed_imgs[0].get_rect(topleft=(300, 320))
        self.pickaxe_rect = self.pickaxe_imgs[0].get_rect(topleft=(300, 440))

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

    def get_pickaxe_cost(self):
        if self.player.pickaxe_upgrade >= 3:
            return None
        return 100 + (self.player.pickaxe_upgrade * 10)

    def get_pickaxe_image(self):
        index = min(self.player.pickaxe_upgrade, 3)
        return self.pickaxe_imgs[index]

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

    def buy_pickaxe_upgrade(self):
        if self.player.pickaxe_upgrade >= 3:
            return

        cost = self.get_pickaxe_cost()
        if cost is not None and self.player.coins >= cost:
            self.player.coins -= cost
            self.player.pickaxe_upgrade += 1

    def handle_event(self, event):
        """Returns 'gameplay' when leaving the shop."""

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.fuel_rect.collidepoint(event.pos):
                self.fuel_pressed = True
                self.buy_fuel_upgrade()

            if self.speed_rect.collidepoint(event.pos):
                self.speed_pressed = True
                self.buy_speed_upgrade()

            if self.pickaxe_rect.collidepoint(event.pos):
                self.buy_pickaxe_upgrade()

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.fuel_pressed = False
            self.speed_pressed = False

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

        fuel_img = self.fuel_imgs[1] if self.fuel_pressed else self.fuel_imgs[0]
        speed_img = self.speed_imgs[1] if self.speed_pressed else self.speed_imgs[0]

        screen.blit(fuel_img, self.fuel_rect)
        screen.blit(speed_img, self.speed_rect)
        screen.blit(self.get_pickaxe_image(), self.pickaxe_rect)

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
            self.font.render(
                f"Pickaxe level: {self.player.pickaxe_upgrade}/3",
                True,
                self.text_color,
            ),
            (20, 140),
        )

        screen.blit(
            self.font.render(f"Cost: {self.get_fuel_cost()}", True, self.text_color),
            (self.fuel_rect.x, self.fuel_rect.y - 30),
        )

        screen.blit(
            self.font.render(f"Cost: {self.get_speed_cost()}", True, self.text_color),
            (self.speed_rect.x, self.speed_rect.y - 30),
        )

        pickaxe_cost = self.get_pickaxe_cost()
        pickaxe_cost_text = "MAXED" if pickaxe_cost is None else f"Cost: {pickaxe_cost}"
        screen.blit(
            self.font.render(pickaxe_cost_text, True, self.text_color),
            (self.pickaxe_rect.x, self.pickaxe_rect.y - 30),
        )

        hint = self.small_font.render(
            "TAB / SPACE / ENTER / P / ESC - Launch   |   Hold left click to press button",
            True,
            (180, 180, 200),
        )
        screen.blit(hint, (20, 560))