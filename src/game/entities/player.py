import pygame

class Player:
    def __init__(self, x, y, size=40, speed=5, color=(0, 200, 255)):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.color = color   
        self.launched = False  # ← game/ship state
        self.has_drill = False
        self.drill_image = pygame.image.load("assets/drill.png").convert_alpha()
        self.drill_image = pygame.transform.scale(self.drill_image, (24, 24))

        
    # drill logic start
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def get_drill_rect(self):
        if not self.has_drill:
            return None

        drill_x = self.x + (self.size // 2) - 12
        drill_y = self.y - 20
        return pygame.Rect(drill_x, drill_y, 24, 24)
    # drill logic end

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
