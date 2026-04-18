import random
import pygame
import os

COLLECT_RADIUS = 100
ALT_MIN = 200
COIN_VALUE = 10
COIN_SIZE = 50
SPAWN_AHEAD = 1000
SPAWN_RATE = 0.1
INITIAL_COINS = 5
ANIMATION_SPEED = 0.3

_coin_frames = []


def _load_frames():
    global _coin_frames
    if _coin_frames:
        return
    frame_files = ["coin1.png", "coin2.png"]
    for f in frame_files:
        path = os.path.join(os.path.dirname(__file__), "../../assets/coin", f)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            _coin_frames.append(pygame.transform.smoothscale(img, (COIN_SIZE, COIN_SIZE)))
    return _coin_frames


def _w2sy(world_y, cam, ground_sy, rocket_target_sy=None):
    """World Y (up = positive) → screen Y."""
    return ground_sy - (world_y - cam)


class Coin:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.collected = False
        self.anim_timer = 0.0
        self.frame = 0


    def check_collect(self, rocket_x: float, rocket_y: float):
        if self.collected:
            return False
        dx = self.x - rocket_x
        dy = self.y - rocket_y
        if (dx * dx + dy * dy) <= COLLECT_RADIUS * COLLECT_RADIUS:
            self.collected = True
            return True
        return False
    

    def update(self, dt: float):
        if not self.collected:
            self.anim_timer += dt
            if self.anim_timer >= ANIMATION_SPEED:
                self.anim_timer = 0.0
                self.frame = (self.frame + 1) % len(_coin_frames)


    def draw(self, screen: pygame.Surface, cam: float, ground_sy: int):
        if self.collected:
            return
        _load_frames()
        sx = int(self.x)
        sy = int(_w2sy(self.y, cam, ground_sy))
        if sy < -COIN_SIZE or sy > screen.get_height() + COIN_SIZE:
            return
        if _coin_frames:
            srf = _coin_frames[self.frame]
        screen.blit(srf, srf.get_rect(center = (sx, sy)))


class CoinManager:
    def __init__(self, shared_player = None, screen_w: int = 900, ground_sy: int = 500):
        self.shared = shared_player
        self.screen_w = screen_w
        self.ground_sy = ground_sy
        self.coins: list[Coin] = []
        self._prespawn()
    

    def _prespawn(self):
        for i in range(INITIAL_COINS):
            wx = random.randint(40, self.screen_w - 40)
            wy = random.uniform(150, SPAWN_AHEAD)
            self.coins.append(Coin(float(wx), wy))


    def update(self, rocket, dt: float):
        collected_this_frame = 0
        for coin in self.coins:
            coin.update(dt)
            if coin.check_collect(rocket.x, rocket.y):
                collected_this_frame += 1
                if self.shared is not None:
                    self.shared.coins += COIN_VALUE
        if random.random() < SPAWN_RATE:
            wx = random.randint(40, self.screen_w - 40)
            wy = rocket.y + SPAWN_AHEAD + random.uniform(0, 400)
            self.coins.append(Coin(float(wx), wy))
        
        self.coins = [c for c in self.coins if not c.collected]
        return collected_this_frame
    

    def reset(self):
        self.coins = []
        self._prespawn()

    
    def draw(self, screen: pygame.Surface, cam: float):
        for coin in self.coins:
            coin.draw(screen, cam, self.ground_sy)