import random
import pygame
import os

COLLECT_RADIUS = 100
ALT_MIN = 200
COIN_VALUE = 10
COIN_SIZE = 100
SPAWN_AHEAD = 1000
SPAWN_RATE = 0.1
INITIAL_COINS = 5
COIN_SCREEN_TIME = 1

_ASSET_PATH = os.path.join(os.path.dirname(__file__), "../../assets/coin1.png")
_coin_sprite = None


def _load_sprite():
    global _coin_sprite
    if _coin_sprite is not None:
        return _coin_sprite
    if os.path.exists(_ASSET_PATH):
        img = pygame.image.load(_ASSET_PATH).convert_alpha()
        _coin_sprite = pygame.transform.smoothscale(img, (COIN_SIZE, COIN_SIZE))
    return _coin_sprite


def _w2sy(world_y, cam, ground_sy, rocket_target_sy=None):
    """World Y (up = positive) → screen Y."""
    return ground_sy - (world_y - cam)


class Coin:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.collected = False


    def check_collect(self, rocket_x: float, rocket_y: float):
        if self.collected:
            return False
        dx = self.x - rocket_x
        dy = self.y - rocket_y
        if (dx * dx + dy * dy) <= COLLECT_RADIUS * COLLECT_RADIUS:
            self.collected = True
            return True
        return False


    def draw(self, screen: pygame.Surface, cam: float, ground_sy: int):
        if self.collected:
            return
        sx = int(self.x)
        sy = int(_w2sy(self.x, cam, ground_sy))
        if self.collected:
            return
        sx = int(self.x)
        sy = int(_w2sy(self.y, cam, ground_sy))
        if sy < -COIN_SIZE or sy > screen.get_height() + COIN_SIZE:
            return
        srf = _load_sprite()
        rect = srf.get_rect(center = (sx, sy))
        screen.blit(srf, rect)


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


    def update(self, rocket):
        collected_this_frame = 0
        for coin in self.coins:
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