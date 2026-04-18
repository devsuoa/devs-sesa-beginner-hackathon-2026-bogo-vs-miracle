import random
import pygame

class GoldDrop(pygame.sprite.Sprite):
    def __init__(self, pos, image, amount=1):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=pos)
        self.amount = amount

        self.velocity = pygame.Vector2(
            random.uniform(-1.5, 1.5),
            random.uniform(-2.5, -1.0)
        )
        self.gravity = 0.12

    def update(self):
        self.velocity.y += self.gravity
        self.rect.x += int(self.velocity.x)
        self.rect.y += int(self.velocity.y)


class ExplosionAnimation(pygame.sprite.Sprite):
    def __init__(self, pos, frames, frame_duration=4):
        super().__init__()
        self.frames = frames
        self.frame_duration = frame_duration
        self.frame_index = 0
        self.timer = 0

        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)

    def update(self):
        self.timer += 1

        if self.timer >= self.frame_duration:
            self.timer = 0
            self.frame_index += 1

            if self.frame_index >= len(self.frames):
                self.kill()
                return

            center = self.rect.center
            self.image = self.frames[self.frame_index]
            self.rect = self.image.get_rect(center=center)


class Asteroid(pygame.sprite.Sprite):
    def __init__(
        self,
        pos,
        asteroid_images,
        explosion_frames,
        gold_image,
        all_sprites_group,
        gold_group,
        effect_group,
        velocity=(0, 3),
        hp=3,
        gold_drop_range=(1, 3)
    ):
        super().__init__()

        # Random asteroid appearance
        self.base_image = random.choice(asteroid_images)
        self.image = self.base_image
        self.rect = self.image.get_rect(center=pos)

        self.position = pygame.Vector2(self.rect.center)
        self.velocity = pygame.Vector2(velocity)

        self.hp = hp
        self.gold_drop_range = gold_drop_range

        self.explosion_frames = explosion_frames
        self.gold_image = gold_image

        self.all_sprites_group = all_sprites_group
        self.gold_group = gold_group
        self.effect_group = effect_group

        # Optional rotation for nicer asteroid movement
        self.rotation = random.randint(0, 359)
        self.rotation_speed = random.uniform(-2.0, 2.0)

    def update(self):
        # Movement
        self.position += self.velocity
        self.rect.center = (round(self.position.x), round(self.position.y))

        # Rotation
        self.rotation += self.rotation_speed
        center = self.rect.center
        self.image = pygame.transform.rotate(self.base_image, self.rotation)
        self.rect = self.image.get_rect(center=center)

        # Remove if off-screen enough
        screen = pygame.display.get_surface()
        if screen:
            w, h = screen.get_size()
            if self.rect.top > h + 100 or self.rect.right < -100 or self.rect.left > w + 100:
                self.kill()

    def take_damage(self, amount, damage_type="normal"):
        """
        damage_type can be:
        - 'normal'
        - 'laser'
        - 'explosive'
        """
        self.hp -= amount

        if self.hp <= 0:
            self.destroy(damage_type)

    def destroy(self, damage_type):
        # Play destroy animation
        explosion = ExplosionAnimation(self.rect.center, self.explosion_frames)
        self.effect_group.add(explosion)
        self.all_sprites_group.add(explosion)

        # Drop gold only if destroyed by explosives
        if damage_type == "explosive":
            gold_count = random.randint(*self.gold_drop_range)
            for _ in range(gold_count):
                gold = GoldDrop(self.rect.center, self.gold_image, amount=1)
                self.gold_group.add(gold)
                self.all_sprites_group.add(gold)

        self.kill()