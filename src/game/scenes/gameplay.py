"""
scenes/gameplay.py  —  Learn-to-Fly style launch game

Controls
  AIM   : LEFT / RIGHT  →  adjust launch angle
           SPACE or UP   →  launch!
  FLY   : SPACE or UP   →  thrust (burns fuel)
           LEFT / RIGHT  →  steer rocket
  DONE  : R or SPACE    →  try again
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from game.scenes.background_manager import ParallaxBackground
import pygame
import math
import random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from entities.player import Player

from entities.asteroid import Asteroid
from entities.coin import CoinManager

# ─── window / timing ──────────────────────────────────────────────────────────
W, H = 900, 600
FPS  = 60

# ─── physics ──────────────────────────────────────────────────────────────────
GRAVITY    = 260.0   # px/s²  downward
THRUST     = 320.0   # px/s²  along rocket heading
STEER_SPD  = 88.0    # °/s    in-flight rotation
AIM_SPD    = 100.0   # °/s    pre-launch aiming
MAX_ANGLE  = 72.0    # max lean from vertical (degrees)
LAUNCH_SPD = 90.0    # initial burst speed on launch (px/s)

MAX_FUEL   = 100.0
BURN_RATE  = 28.0    # fuel/s while thrusting

SPACE_ALT = 7500    # altitude (px) that counts as "space"
# Early finish (skip waiting for ground): peak must reach this altitude, then you
# must descend at least MIN_DROP_FROM_PEAK px from that apex — so you fall a bit first.
SKIP_FALL_MIN_ALT = 5000
MIN_DROP_FROM_PEAK = 1000

# screen-y of ground surface when camera is at rest
GROUND_SY        = H - 100
# screen-y to keep rocket at when camera scrolls
ROCKET_TARGET_SY = int(H * 0.7)

# asteroid timings
ASTEROID_SPAWN_TIMER = 0.0
ASTEROID_SPAWN_DELAY = 1.5

# ─── colours ──────────────────────────────────────────────────────────────────
WHITE  = (255, 255, 255)
BLACK  = (  0,   0,   0)
RED    = (220,  50,  30)
ORANGE = (255, 140,   0)
YELLOW = (255, 230,  50)
GREEN  = ( 50, 160,  50)
DKGRN  = ( 20,  80,  20)
SILVER = (200, 210, 215)
DKSLV  = (130, 140, 150)
LBLUE  = (160, 215, 255)




# ─── helpers ──────────────────────────────────────────────────────────────────
def lerp(a, b, t):
    return a + (b - a) * t





def w2sy(world_y, cam):
    """Convert world Y (up = positive) to screen Y."""
    return GROUND_SY - (world_y - cam)


def cam_from_rocket(wy):
    """Camera value: world_y at GROUND_SY position. Clamped so ground stays on screen."""
    return max(0.0, wy - (GROUND_SY - ROCKET_TARGET_SY))


# ─── Star ─────────────────────────────────────────────────────────────────────
class Star:
    def __init__(self):
        self.wx = random.randint(0, W)
        self.wy = random.randint(600, 14000)
        self.br = random.randint(110, 255)
        self.r  = random.choice([1, 1, 1, 2])

        self.background = ParallaxBackground(900, 600)
        self.height_meters = 0
        self.upward_speed = 0

    def draw(self, screen, cam, alpha):
        sy = int(w2sy(self.wy, cam))
        if -4 <= sy <= H + 4:
            c = int(self.br * alpha)
            pygame.draw.circle(screen, (c, c, c), (self.wx, sy), self.r)



# ─── Rocket sprite ────────────────────────────────────────────────────────────
import os as _os
_ASSET_PATH = _os.path.join(_os.path.dirname(__file__), "../../assets/cat1.png")

_cat_raw   = None   # original loaded image
_cat_cache = {}     # angle (int degrees) → rotated surface

def _get_cat(angle: float) -> pygame.Surface:
    global _cat_raw
    if _cat_raw is None:
        _cat_raw = pygame.image.load(_ASSET_PATH).convert_alpha()

    key = int(angle)
    if key not in _cat_cache:
        _cat_cache[key] = pygame.transform.rotate(_cat_raw, -angle)

    return _cat_cache[key]


# ─── Rocket (extends Player with physics) ─────────────────────────────────────
class Rocket(Player):
    def __init__(self, shared_player=None):
        self._shared = shared_player
        spd = shared_player.speed if shared_player is not None else 5.0
        super().__init__(x=float(W // 2), y=0.0, speed=spd)
        self._init_physics()

    def _init_physics(self):
        self.vx            = 0.0
        self.vy            = 0.0
        self.angle         = 0.0      # degrees from vertical; + = lean right
        cap = self._shared.fuel if self._shared is not None else MAX_FUEL
        self.max_fuel      = max(float(cap), 1.0)
        self.fuel          = self.max_fuel
        self.max_altitude  = 0.0
        self.reached_space = False
        self.thrusting     = False

    def reset(self):
        # Sync stats from shop progression
        if self._shared is not None:
            self.speed = self._shared.speed
            cap = max(float(self._shared.fuel), 1.0)
            self.max_fuel = cap
        self.x    = float(W // 2)
        self.y    = 0.0
        self.vx   = 0.0
        self.vy   = 0.0
        self.angle = 0.0
        self.fuel  = self.max_fuel
        self.max_altitude  = 0.0
        self.reached_space = False
        self.thrusting     = False

    def update(self, dt: float, keys, state: str) -> bool:
        """Tick physics. Returns True when rocket lands back on the ground."""
        if state == "aiming":
            if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
                self.angle = max(-MAX_ANGLE, self.angle - AIM_SPD * dt)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.angle = min( MAX_ANGLE, self.angle + AIM_SPD * dt)
            self.thrusting = False
            return False

        # --- flying ---
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            self.angle = max(-MAX_ANGLE, self.angle - STEER_SPD * dt)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle = min( MAX_ANGLE, self.angle + STEER_SPD * dt)

        # thrust is always on while fuel remains — player only steers
        self.thrusting = self.fuel > 0
        fuel_before = self.fuel

        if self.thrusting:
            rad           = math.radians(self.angle)
            thrust_scaled = THRUST * (self.speed / 5.0)  # speed=5 is baseline
            self.vx += math.sin(rad) * thrust_scaled * dt
            
            self.vy += math.cos(rad) * thrust_scaled * dt
            self.fuel = max(0.0, self.fuel - BURN_RATE * dt)

        # Single frame: fuel just ran out — drop vertical momentum (no upward coast)
        if fuel_before > 0 and self.fuel <= 0:
            self.vy = 0.0

        # fall faster with no fuel (dead weight)
        effective_gravity = GRAVITY * (2.2 if self.fuel <= 0 else 1.0)
        self.vy -= effective_gravity * dt
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.x   = max(0.0, min(float(W), self.x))
        if self.x in (0.0, float(W)):
            self.vx = 0.0

        if self.y > self.max_altitude:
            self.max_altitude = self.y
            if self.max_altitude >= SPACE_ALT:
                self.reached_space = True

        if self.y <= 0.0:
            self.y = self.vx = self.vy = 0.0
            return True

        return False

    def draw(self, screen, cam):
        sx  = int(self.x)
        sy  = int(w2sy(self.y, cam))
        srf = _get_cat(self.angle)
        rect = srf.get_rect(center=(sx, sy))
        screen.blit(srf, rect)


# ─── GameplayScene ────────────────────────────────────────────────────────────
class GameplayScene:

    def __init__(self, screen=None, shared_player=None):
        if screen is None:
            pygame.init()
            screen = pygame.display.set_mode((W, H))
            pygame.display.set_caption("Launch to Space")
        self.screen = screen
        self.clock  = pygame.time.Clock()

        self.font_lg = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_md = pygame.font.SysFont("Arial", 22)
        self.font_sm = pygame.font.SysFont("Arial", 15)

        self.stars  = [Star()  for _ in range(320)]


        self.shared = shared_player
        self.rocket = Rocket(shared_player)
        self.state = "aiming"    # "aiming" | "flying" | "done"
        self.cam = 0.0
        self._ended_on_descent = False

        self.asteroids = []
        self.asteroid_spawn_timer = ASTEROID_SPAWN_TIMER
        self.asteroid_spawn_delay = ASTEROID_SPAWN_DELAY

        self.coin_manager = CoinManager(self.shared, screen_w = W, ground_sy = GROUND_SY)

        self.background = ParallaxBackground(W, H)
        self.height_meters = 0.0
        self.upward_speed = 0.0


    # ── reset ──────────────────────────────────────────────────────────────
    def reset(self):
        self.rocket.reset()
        self.state = "aiming"
        self.cam = 0.0
        self._ended_on_descent = False
        self.coin_manager.reset()

        self.asteroids = []
        self.asteroid_spawn_timer = ASTEROID_SPAWN_TIMER

    # ── events ─────────────────────────────────────────────────────────────
    def handle_event(self, event):
        """Returns ``\"shop\"`` when switching to the shop (blocked while flying)."""
        if event.type == pygame.KEYDOWN:
            # Shop / flight toggle — only while aiming or on the results screen, not mid-flight
            if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                if self.state != "flying":
                    return "shop"
                return None
            if self.state == "aiming":
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self._launch()
            if self.state == "done":
                if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                    self.reset()
                    self.coin_manager.reset()
        return None

    def _launch(self):
        rad = math.radians(self.rocket.angle)
        self.rocket.vx = math.sin(rad) * LAUNCH_SPD
        self.rocket.vy = math.cos(rad) * LAUNCH_SPD
        self.state = "flying"

    def _spawn_asteroid(self):
        spawn_x = random.randint(60, W - 60)
        spawn_y = self.rocket.y + random.randint(500, 1400)

        asteroid = Asteroid(
            x = spawn_x,
            y = spawn_y,              
            hp = 3
        )
        self.asteroids.append(asteroid)

    # ── update ─────────────────────────────────────────────────────────────
    def update(self, dt: float):
        keys = pygame.key.get_pressed()

        if self.state in ("aiming", "flying"):
            landed = self.rocket.update(dt, keys, self.state)

            if self.state == "flying":
                self.asteroid_spawn_timer += dt
                if self.asteroid_spawn_timer >= self.asteroid_spawn_delay:
                    self.asteroid_spawn_timer = 0.0
                    self._spawn_asteroid()

                for asteroid in self.asteroids:
                    asteroid.update(dt)

                    # simple rocket collision
                    if asteroid.alive and asteroid.collides_with_point(self.rocket.x, self.rocket.y, radius=20):
                        asteroid.take_damage(999, "explosive")

                    # collect gold
                    earned_gold = asteroid.collect_gold(self.rocket.x, self.rocket.y, radius=30)
                    if self.shared is not None:
                        self.shared.coins += earned_gold

                self.asteroids = [a for a in self.asteroids if not a.finished]

                self.coin_manager.update(self.rocket)

                drop_from_peak = self.rocket.max_altitude - self.rocket.y
                skip_long_fall = (
                    self.rocket.max_altitude >= SKIP_FALL_MIN_ALT
                    and self.rocket.vy < 0
                    and drop_from_peak >= MIN_DROP_FROM_PEAK
                )

                if landed or skip_long_fall:
                    self._ended_on_descent = bool(skip_long_fall and not landed)
                    self.state = "done"
                    earned = int(self.rocket.max_altitude / 25)
                    if self.shared is not None:
                        self.shared.coins += earned

        self.cam = cam_from_rocket(self.rocket.y)
        # BACKGROUND SCROLLING PARALLAX
        if self.state == "flying":
            self.upward_speed = max(0.0, self.rocket.vy)
            self.height_meters = self.rocket.y
        else:
            self.upward_speed = 0.0

        self.background.update(self.upward_speed, 0.003 * self.rocket.vx, 0.005 * self.rocket.vy, self.height_meters)

    # ── draw ───────────────────────────────────────────────────────────────
    def draw(self):
        self.screen.fill((0, 0, 0))
        alt = self.rocket.y
        self.background.draw(self.screen, self.height_meters)


        # stars fade in above 1500 m
        star_alpha = max(0.0, min(1.0, (alt - 1500) / 2500))
        if star_alpha > 0.01:
            for s in self.stars:
                s.draw(self.screen, self.cam, star_alpha)



        # asteroids                   
        for asteroid in self.asteroids:
            asteroid.draw(self.screen, lambda wy: w2sy(wy, self.cam))


        # space boundary
        ssy = int(w2sy(SPACE_ALT, self.cam))
        if -2 <= ssy <= H:
            for x in range(0, W, 14):
                pygame.draw.line(self.screen, (100, 100, 210), (x, ssy), (x + 7, ssy), 1)
            lbl = self.font_sm.render("── SPACE ──", True, (140, 140, 230))
            self.screen.blit(lbl, (W - lbl.get_width() - 12, ssy + 4))

        # trajectory dots (aiming only)
        if self.state == "aiming":
            self._draw_trajectory()

        self.coin_manager.draw(self.screen, self.cam)

        # rocket
        self.rocket.draw(self.screen, self.cam)

        self._draw_hud()

        if self.state == "done":
            self._draw_results()

        
        pygame.display.flip()


    def _draw_trajectory(self):
        r   = self.rocket
        rad = math.radians(r.angle)
        vx0 = math.sin(rad) * LAUNCH_SPD
        vy0 = math.cos(rad) * LAUNCH_SPD
        prev = None
        for i in range(1, 30):
            t  = i * 0.28
            ty = r.y + vy0 * t - 0.5 * GRAVITY * t * t
            if ty < 0:
                break
            tx = r.x + vx0 * t
            sx = int(tx)
            sy = int(w2sy(ty, self.cam))
            fade = max(0.0, 1.0 - i / 30)
            col  = (int(255 * fade), int(225 * fade), 0)
            size = max(1, 3 - i // 10)
            pygame.draw.circle(self.screen, col, (sx, sy), size)
            if prev:
                pygame.draw.line(self.screen,
                                 (int(200*fade), int(175*fade), 0), prev, (sx, sy), 1)
            prev = (sx, sy)

        # arrow tip + angle label
        tip_x = int(r.x + math.sin(rad) * 78)
        tip_y = int(w2sy(r.y, self.cam) - math.cos(rad) * 78)
        pygame.draw.circle(self.screen, YELLOW, (tip_x, tip_y), 5)
        side = "R" if r.angle > 0.5 else ("L" if r.angle < -0.5 else "")
        lbl  = self.font_sm.render(f"{abs(int(r.angle))}°{side}", True, YELLOW)
        self.screen.blit(lbl, (tip_x + 8, tip_y - 10))

    def _draw_hud(self):
        r = self.rocket

        # fuel bar
        bx, by, bw, bh = 18, 18, 170, 20
        pygame.draw.rect(self.screen, (40, 40, 55), (bx, by, bw, bh), border_radius=5)
        denom = max(r.max_fuel, 1.0)
        fw   = int(bw * r.fuel / denom)
        fcol = GREEN if r.fuel > 35 else (ORANGE if r.fuel > 12 else RED)
        if fw > 0:
            pygame.draw.rect(self.screen, fcol, (bx, by, fw, bh), border_radius=5)
        pygame.draw.rect(self.screen, WHITE, (bx, by, bw, bh), 2, border_radius=5)
        self.screen.blit(self.font_sm.render(f"FUEL  {int(r.fuel)}", True, WHITE),
                         (bx + 5, by + 3))

        self.screen.blit(self.font_md.render(f"ALT  {int(r.y):,} m",            True, WHITE),
                         (18, 46))
        self.screen.blit(self.font_sm.render(f"MAX  {int(r.max_altitude):,} m", True, (170, 215, 255)),
                         (18, 74))

        if self.state == "aiming":
            h = self.font_sm.render(
                "← →  Aim      SPACE  Launch      TAB / ESC — Shop",
                True,
                YELLOW,
            )
            self.screen.blit(h, (W // 2 - h.get_width() // 2, H - 34))
        elif self.state == "flying":
            h = self.font_sm.render("← →  Steer", True, (200, 200, 200))
            self.screen.blit(h, (W // 2 - h.get_width() // 2, H - 34))

        if r.reached_space:
            badge = self.font_md.render("★  IN SPACE  ★", True, YELLOW)
            self.screen.blit(badge, (W - badge.get_width() - 14, 18))

        if self.state == "flying" and r.fuel <= 0:
            nf = self.font_md.render("NO FUEL", True, RED)
            self.screen.blit(nf, (W - nf.get_width() - 14, 50))

        # money display (top right)
        bal = self.shared.coins if self.shared is not None else 0
        mt = self.font_md.render(f"$ {bal:,}", True, (80, 220, 120))
        self.screen.blit(mt, (W - mt.get_width() - 14, H - 36))

    def _draw_results(self):
        r   = self.rocket
        pct = int(r.max_altitude / SPACE_ALT * 100)

        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 168))
        self.screen.blit(ov, (0, 0))

        rows = []
        if self._ended_on_descent:
            rows.append(
                (
                    "RUN COMPLETE  —  high descent (skipped long fall)",
                    (180, 235, 255),
                    self.font_lg,
                )
            )
        elif r.reached_space:
            rows.append(("YOU REACHED SPACE!", (255, 240, 50), self.font_lg))
        else:
            rows.append(("BACK ON THE GROUND", WHITE, self.font_lg))

        rows.append((f"Max altitude:  {int(r.max_altitude):,} m", (180, 230, 255), self.font_md))

        if r.reached_space:
            rows.append(("Orbit achieved!  🚀", YELLOW, self.font_md))
        else:
            msg = (
                "Nearly there!"  if pct > 80 else
                "So close!"      if pct > 60 else
                "Getting there!" if pct > 40 else
                "Keep trying!"   if pct > 20 else
                "Off the ground!"
            )
            rows.append((f"{pct}%  of the way to space  —  {msg}", (180, 180, 180), self.font_sm))

        earned = int(r.max_altitude / 25)
        total_coins = self.shared.coins if self.shared is not None else earned
        rows.append((f"Earned:  ${earned:,}      Total:  ${total_coins:,}", (80, 220, 120), self.font_md))
        rows.append(("", None, None))
        rows.append(("SPACE or R  —  Try Again", (150, 220, 150), self.font_sm))
        rows.append(("TAB / ESC  —  Shop", (160, 180, 210), self.font_sm))

        total_h = sum(f.get_height() + 8 for _, _, f in rows if f) + 16
        y = H // 2 - total_h // 2
        for text, color, font in rows:
            if font is None:
                y += 14
                continue
            s = font.render(text, True, color)
            self.screen.blit(s, (W // 2 - s.get_width() // 2, y))
            y += s.get_height() + 8

    # ── main loop ──────────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                self.handle_event(event)
            self.update(dt)
            self.draw()


# run standalone
if __name__ == "__main__":
    pygame.init()
    GameplayScene().run()
