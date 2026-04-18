import pygame

class Player:
    def __init__(self, x, y, size=40, speed=5, color=(0, 200, 255)):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.color = color   
        self.launched = False  # ← game/ship state

    def launch(self):
        if not self.launched:
            self.launched = True
            print("Launch initiated")  # optional debug

    def handle_input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE]:
            self.launch()
        if keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_d]:
            self.x += self.speed

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            self.color,
            (self.x, self.y, self.size, self.size)
        )
