import pygame


class ParallaxBackground:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.set_names = ["land", "space", "moon", "void"]

        # Per-layer parallax depth
        self.layer_vertical_speeds = [0.08, 0.15, 0.25, 0.4]
        self.layer_horizontal_speeds = [0.6, 1.0, 1.6, 2.4]

        self.backgrounds = {}
        self.x_offsets = {}
        self.y_offsets = {}

        for set_name in self.set_names:
            self.backgrounds[set_name] = []
            self.x_offsets[set_name] = []
            self.y_offsets[set_name] = []

            for i in range(1, 5):
                path = f"assets/backgrounds/{set_name}/{i}.png"
                image = pygame.image.load(path).convert_alpha()
                image = pygame.transform.scale(image, (screen_width, screen_height))

                self.backgrounds[set_name].append(image)
                self.x_offsets[set_name].append(0.0)
                self.y_offsets[set_name].append(0.0)

    def get_current_set_name(self, height_meters):
        if height_meters < 6250:
            return "land"
        elif height_meters < 12500:
            return "space"
        elif height_meters < 18750:
            return "moon"
        else:
            return "void"

    def update(self, upward_speed, height_meters):
        current_set = self.get_current_set_name(height_meters)

        for i, layer in enumerate(self.backgrounds[current_set]):
            image_width = layer.get_width()
            image_height = layer.get_height()

            # Vertical movement: slower
            self.y_offsets[current_set][i] += upward_speed * self.layer_vertical_speeds[i]

            # Horizontal movement: faster constant drift
            self.x_offsets[current_set][i] += self.layer_horizontal_speeds[i]

            if self.x_offsets[current_set][i] >= image_width:
                self.x_offsets[current_set][i] -= image_width

            if self.y_offsets[current_set][i] >= image_height:
                self.y_offsets[current_set][i] -= image_height

    def draw(self, screen, height_meters):
        current_set = self.get_current_set_name(height_meters)

        for i, layer in enumerate(self.backgrounds[current_set]):
            x_offset = self.x_offsets[current_set][i]
            y_offset = self.y_offsets[current_set][i]

            image_width = layer.get_width()
            image_height = layer.get_height()

            # Draw a 2x2 tiled grid so movement on both axes never leaves gaps
            screen.blit(layer, (-x_offset, -y_offset))
            screen.blit(layer, (-x_offset + image_width, -y_offset))
            screen.blit(layer, (-x_offset, -y_offset + image_height))
            screen.blit(layer, (-x_offset + image_width, -y_offset + image_height))