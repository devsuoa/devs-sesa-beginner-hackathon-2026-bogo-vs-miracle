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

TIERS = [
    {"pickaxe_required": 0, "coin_reward": 50,  "asset_set": "t1"},
    {"pickaxe_required": 1, "coin_reward": 75, "asset_set": "t2"},
    {"pickaxe_required": 2, "coin_reward": 150, "asset_set": "t3"},
    {"pickaxe_required": 3, "coin_reward": 500, "asset_set": "t4"},
]

TIER_ASSET_SETS = {
    "t1": {
        "bases": ["t1/asteroid1.png", "t1/asteroid2.png"],
        "breaking": [
            "t1/asteroid1_breaking1.png",
            "t1/asteroid1_breaking2.png",
            "t1/asteroid1_breaking3.png",
            "t1/asteroid2_breaking1.png",
            "t1/asteroid2_breaking2.png",
        ],
    },
    "t2": {
        "bases": ["t2/asteroid1.png", "t2/asteroid2.png"],
        "breaking": [
            "t2/asteroid1_breaking1.png",
            "t2/asteroid1_breaking2.png",
            "t2/asteroid1_breaking3.png",
            "t2/asteroid2_breaking1.png",
            "t2/asteroid2_breaking2.png",
        ],
    },
    "t3": {
        "bases": ["t3/asteroid1.png", "t3/asteroid2.png"],
        "breaking": [
            "t3/asteroid1_breaking1.png",
            "t3/asteroid1_breaking2.png",
            "t3/asteroid1_breaking3.png",
            "t3/asteroid2_breaking1.png",
            "t3/asteroid2_breaking2.png",
        ],
    },
    "t4": {
        "bases": ["t4/asteroid1.png", "t4/asteroid2.png"],
        "breaking": [
            "t4/asteroid1_breaking1.png",
            "t4/asteroid1_breaking2.png",
            "t4/asteroid1_breaking3.png",
            "t4/asteroid2_breaking1.png",
            "t4/asteroid2_breaking2.png",
        ],
    },
}



_loaded_variants = {}
 
def _load_tier_assets(asset_set: str) -> dict:
    if asset_set in _loaded_variants:
        return _loaded_variants[asset_set]
    spec = TIER_ASSET_SETS[asset_set]
    base_images = [
        pygame.image.load(str(ASTEROID_DIR / f)).convert_alpha()
        for f in spec["bases"]
    ]
    breaking_frames = [
        pygame.image.load(str(ASTEROID_DIR / f)).convert_alpha()
        for f in spec["breaking"]
    ]
    result = {"bases": base_images, "breaking": breaking_frames}
    _loaded_variants[asset_set] = result
    return result


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
        screen.blit(current_frame, current_frame.get_rect(center=(screen_x, screen_y)))


class Asteroid:
    def __init__(self, x, y, tier: int = 0):
        self.tier = max(0, min(tier, len(TIERS) - 1))
        tier_data = TIERS[self.tier]
 
        self.x = float(x)
        self.y = float(y)
        self.coin_reward = tier_data["coin_reward"]
        self.pickaxe_required = tier_data["pickaxe_required"]
 
        self.vx = random.uniform(ASTEROID_MIN_X_SPEED, ASTEROID_MAX_X_SPEED)
        self.vy = random.uniform(ASTEROID_MIN_Y_SPEED, ASTEROID_MAX_Y_SPEED)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(ASTEROID_MIN_ROT_SPEED, ASTEROID_MAX_ROT_SPEED)
 
        self.alive = True
        self.finished = False
        self.exploding = False
        self.explosion = None
 
        assets = _load_tier_assets(tier_data["asset_set"])
        self.base_image = random.choice(assets["bases"])  # pick one of the two sprites
        self.breaking_frames = assets["breaking"]
 
        largest_dimension = max(self.base_image.get_width(), self.base_image.get_height())
        self.radius = largest_dimension * ASTEROID_RADIUS_SCALE
 
    def can_be_broken_by(self, pickaxe_level: int) -> bool:
        return pickaxe_level >= self.pickaxe_required
 
    def update(self, dt):
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
        if self.exploding:
            if self.explosion is not None:
                self.explosion.draw(screen, world_to_screen_y)
            return
 
        rotated_image = pygame.transform.rotate(self.base_image, self.rotation)
        screen_x = int(self.x)
        screen_y = int(world_to_screen_y(self.y))
        rect = rotated_image.get_rect(center=(screen_x, screen_y))
        screen.blit(rotated_image, rect)
 
        
    def collides_with_point(self, point_x, point_y, radius=0):
        if not self.alive:
            return False
        dx = self.x - point_x
        dy = self.y - point_y
        return dx * dx + dy * dy <= (self.radius + radius) ** 2
 
    def try_break(self, pickaxe_level: int = 0):
        """Try to break the asteroid. Returns coin reward if successful, else 0."""
        if not self.alive:
            return 0
        if not self.can_be_broken_by(pickaxe_level):
            return 0
        self.destroy()
        return self.coin_reward
 
    def destroy(self):
        if not self.alive:
            return
        self.alive = False
        self.exploding = True
        self.explosion = ExplosionAnimation(self.x, self.y, self.breaking_frames)