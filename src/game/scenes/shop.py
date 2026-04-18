import math
import pygame


class ShopScene:
    def __init__(self, player):
        self.player = player
        self.font = pygame.font.SysFont(None, 36)

        self.background_color = (20, 20, 30)
        self.text_color = (255, 255, 255)

        # --- LOAD IMAGES ---
        self.fuel_img = pygame.image.load("assets/fuel_button.png").convert_alpha()
        self.speed_img = pygame.image.load("assets/speed_button.png").convert_alpha()

        # Optional resize
        self.fuel_img = pygame.transform.scale(self.fuel_img, (200, 80))
        self.speed_img = pygame.transform.scale(self.speed_img, (200, 80))

        # --- POSITION ---
        self.fuel_rect = self.fuel_img.get_rect(topleft=(300, 200))
        self.speed_rect = self.speed_img.get_rect(topleft=(300, 320))

    # -------- COSTS --------

    def get_fuel_cost(self):
        n = self.player.fuel_upgrade_purchases + 1
        return int(10 * math.exp(0.5 * n))

    def get_speed_cost(self):
        n = self.player.speed_upgrade_purchases + 1
        return int(10 * math.exp(0.5 * n))

    # -------- BUY --------

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

    # -------- INPUT --------

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if self.fuel_rect.collidepoint(event.pos):
                self.buy_fuel_upgrade()

            if self.speed_rect.collidepoint(event.pos):
                self.buy_speed_upgrade()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from .gameplay import GameplayScene
                return GameplayScene(self.player)

    def update(self):
        pass

    # -------- DRAW --------

    def draw(self, screen):
        screen.fill(self.background_color)

        # Draw buttons (images)
        screen.blit(self.fuel_img, self.fuel_rect)
        screen.blit(self.speed_img, self.speed_rect)

        # Info text
        screen.blit(
            self.font.render(f"Coins: {self.player.coins}", True, self.text_color),
            (20, 20)
        )

        screen.blit(
            self.font.render(f"Fuel: {self.player.fuel:.2f}", True, self.text_color),
            (20, 60)
        )

        screen.blit(
            self.font.render(f"Speed: {self.player.speed:.2f}", True, self.text_color),
            (20, 100)
        )

        # Costs under buttons
        screen.blit(
            self.font.render(f"Cost: {self.get_fuel_cost()}", True, self.text_color),
            (self.fuel_rect.x, self.fuel_rect.y - 30)
        )

        screen.blit(
            self.font.render(f"Cost: {self.get_speed_cost()}", True, self.text_color),
            (self.speed_rect.x, self.speed_rect.y - 30)
        )