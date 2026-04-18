import random
from pathlib import Path

import pygame


ASSET_DIR = Path(__file__).resolve().parents[2] / "assets"
ASTEROID_DIR = ASSET_DIR / "asteroid"

ASTEROID_ASSET_SETS = [
    {
        "base": "asteroid1.png",
        "breaking": [
            "asteroid1_breaking1.png",
            "asteroid1_breaking2.png",
            "asteroid1_breaking3.png",
        ],
    },
    {
        "base": "asteroid2.png",
        "breaking": [
            "asteroid2_breaking1.png",
            "asteroid2_breaking2.png",
        ],
    },
]

FRAME_RATE_SCALE = 60

ASTEROID_MIN_X_SPEED = -1.2
ASTEROID_MAX_X_SPEED = 1.2
ASTEROID_MIN_Y_SPEED = 1.5
ASTEROID_MAX_Y_SPEED = 3.5

ASTEROID_MIN_ROT_SPEED = -90
ASTEROID_MAX_ROT_SPEED = 90

ASTEROID_RADIUS_SCALE = 0.35
BREAK_FRAME_TIME = 0.08

GOLD_DROP_MIN_COUNT = 1
GOLD_DROP_MAX_COUNT = 3

GOLD_MIN_X_SPEED = -1.5
GOLD_MAX_X_SPEED = 1.5
GOLD_MIN_Y_SPEED = -2.5
GOLD_MAX_Y_SPEED = -1.0
GOLD_GRAVITY = 0.12
GOLD_RADIUS = 6

GOLD_MAIN_COLOR = (255, 215, 0)
GOLD_HIGHLIGHT_COLOR = (255, 245, 120)


def load_asteroid_variants():
    variants = []

    for asteroid_set in ASTEROID_ASSET_SETS:
        base_path = ASTEROID_DIR / asteroid_set["base"]
        breaking_paths = asteroid_set["breaking"]

        base_image = pygame.image.load(str(base_path)).convert_alpha()

        breaking_frames = []
        for filename in breaking_paths:
            frame_path = ASTEROID_DIR / filename
            frame_image = pygame.image.load(str(frame_path)).convert_alpha()
            breaking_frames.append(frame_image)

        variants.append(
            {
                "base": base_image,
                "breaking": breaking_frames,
            }
        )

    return variants


class GoldDrop:
    def __init__(self, x, y, amount=1):
        self.x = float(x)
        self.y = float(y)
        self.amount = amount

        self.vx = random.uniform(GOLD_MIN_X_SPEED, GOLD_MAX_X_SPEED)
        self.vy = random.uniform(GOLD_MIN_Y_SPEED, GOLD_MAX_Y_SPEED)
        self.gravity = GOLD_GRAVITY

        self.radius = GOLD_RADIUS
        self.collected = False

    def update(self, dt):
        self.vy += self.gravity
        self.x += self.vx * FRAME_RATE_SCALE * dt
        self.y += self.vy * FRAME_RATE_SCALE * dt

    def draw(self, screen, world_to_screen_y):
        if self.collected:
            return

        screen_x = int(self.x)
        screen_y = int(world_to_screen_y(self.y))
        highlight_radius = max(2, self.radius // 2)

        pygame.draw.circle(screen, GOLD_MAIN_COLOR, (screen_x, screen_y), self.radius)
        pygame.draw.circle(
            screen,
            GOLD_HIGHLIGHT_COLOR,
            (screen_x - 2, screen_y - 2),
            highlight_radius,
        )

    def can_collect(self, player_x, player_y, radius):
        dx = self.x - player_x
        dy = self.y - player_y
        return dx * dx + dy * dy <= radius * radius


class ExplosionAnimation:
    def __init__(self, x, y, frames, frame_time=BREAK_FRAME_TIME):
        self.x = float(x)
        self.y = float(y)
        self.frames = frames
        self.frame_time = frame_time

        self.time_accumulator = 0.0
        self.frame_index = 0
        self.finished = False

    def update(self, dt):
        if self.finished:
            return

        if not self.frames:
            self.finished = True
            return

        self.time_accumulator += dt

        while self.time_accumulator >= self.frame_time and not self.finished:
            self.time_accumulator -= self.frame_time
            self.frame_index += 1

            if self.frame_index >= len(self.frames):
                self.finished = True

    def draw(self, screen, world_to_screen_y):
        if self.finished or not self.frames:
            return

        current_frame = self.frames[self.frame_index]
        screen_x = int(self.x)
        screen_y = int(world_to_screen_y(self.y))
        frame_rect = current_frame.get_rect(center=(screen_x, screen_y))

        screen.blit(current_frame, frame_rect)


class Asteroid:
    def __init__(self, x, y, hp=3, variants=None):
        self.x = float(x)
        self.y = float(y)
        self.hp = hp

        self.vx = random.uniform(ASTEROID_MIN_X_SPEED, ASTEROID_MAX_X_SPEED)
        self.vy = random.uniform(ASTEROID_MIN_Y_SPEED, ASTEROID_MAX_Y_SPEED)

        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(ASTEROID_MIN_ROT_SPEED, ASTEROID_MAX_ROT_SPEED)

        self.alive = True
        self.finished = False
        self.exploding = False
        self.explosion = None
        self.gold_drops = []

        self.variants = variants if variants is not None else load_asteroid_variants()
        self.variant = random.choice(self.variants)

        self.base_image = self.variant["base"]
        self.breaking_frames = self.variant["breaking"]

        largest_dimension = max(self.base_image.get_width(), self.base_image.get_height())
        self.radius = largest_dimension * ASTEROID_RADIUS_SCALE

    def update(self, dt):
        for gold_drop in self.gold_drops:
            gold_drop.update(dt)

        if self.exploding:
            if self.explosion is not None:
                self.explosion.update(dt)
                if self.explosion.finished:
                    self.finished = True
            return

        self.x += self.vx * FRAME_RATE_SCALE * dt
        self.y += self.vy * FRAME_RATE_SCALE * dt
        self.rotation += self.rotation_speed * dt

    def draw(self, screen, world_to_screen_y):
        for gold_drop in self.gold_drops:
            gold_drop.draw(screen, world_to_screen_y)

        if self.exploding:
            if self.explosion is not None:
                self.explosion.draw(screen, world_to_screen_y)
            return

        rotated_image = pygame.transform.rotate(self.base_image, self.rotation)
        screen_x = int(self.x)
        screen_y = int(world_to_screen_y(self.y))
        image_rect = rotated_image.get_rect(center=(screen_x, screen_y))

        screen.blit(rotated_image, image_rect)

    def collides_with_point(self, point_x, point_y, radius=0):
        if not self.alive:
            return False

        dx = self.x - point_x
        dy = self.y - point_y
        collision_radius = self.radius + radius

        return dx * dx + dy * dy <= collision_radius * collision_radius

    def take_damage(self, amount, damage_type="normal"):
        if not self.alive:
            return

        self.hp -= amount

        if self.hp <= 0:
            self.destroy(damage_type)

    def destroy(self, damage_type="normal"):
        if not self.alive:
            return

        self.alive = False
        self.exploding = True
        self.explosion = ExplosionAnimation(self.x, self.y, self.breaking_frames)

        if damage_type == "explosive":
            drop_count = random.randint(GOLD_DROP_MIN_COUNT, GOLD_DROP_MAX_COUNT)
            for _ in range(drop_count):
                self.gold_drops.append(GoldDrop(self.x, self.y, amount=1))

    def collect_gold(self, player_x, player_y, radius=30):
        collected_amount = 0
        remaining_gold_drops = []

        for gold_drop in self.gold_drops:
            if gold_drop.collected:
                continue

            if gold_drop.can_collect(player_x, player_y, radius):
                gold_drop.collected = True
                collected_amount += gold_drop.amount
            else:
                remaining_gold_drops.append(gold_drop)

        self.gold_drops = remaining_gold_drops
        return collected_amount 