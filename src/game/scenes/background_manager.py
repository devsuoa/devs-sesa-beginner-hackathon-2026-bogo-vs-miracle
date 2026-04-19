import os
import pygame


class ParallaxBackground:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.set_names = ["land", "moon"]

        # Number of layers in each background set
        self.layer_counts = {
            "land": 4,
            "moon": 6,
        }

        # Speeds for each set must match the number of layers in that set
        self.layer_vertical_speeds = {
            "land": [0.08, 0.15, 0.25, 0.4],
            "moon": [0.03, 0.06, 0.1, 0.16, 0.24, 0.35],
        }

        self.layer_horizontal_speeds = {
            "land": [0.05, 0.1, 0.2, 0.35],
            "moon": [0.02, 0.04, 0.08, 0.14, 0.22, 0.32],
        }

        self.backgrounds = {}
        self.x_offsets = {}
        self.y_offsets = {}

        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.normpath(
            os.path.join(base_dir, "../../assets/backgrounds")
        )

        for set_name in self.set_names:
            self.backgrounds[set_name] = []
            self.x_offsets[set_name] = []
            self.y_offsets[set_name] = []

            layer_count = self.layer_counts[set_name]

            for i in range(1, layer_count + 1):
                path = os.path.join(assets_dir, set_name, f"{i}.png")
                image = pygame.image.load(path).convert_alpha()
                image = pygame.transform.scale(image, (screen_width, screen_height))

                self.backgrounds[set_name].append(image)
                self.x_offsets[set_name].append(0.0)
                self.y_offsets[set_name].append(0.0)

    def get_current_set_name(self, height_meters):
        # add other heights in the future when we add background arts
        if height_meters < 12500:
            return "land"
        return "moon"

    def update(self, upward_speed, player_dx, player_dy, height_meters):
        current_set = self.get_current_set_name(height_meters)
        vertical_speeds = self.layer_vertical_speeds[current_set]
        horizontal_speeds = self.layer_horizontal_speeds[current_set]

        for i, layer in enumerate(self.backgrounds[current_set]):
            image_width = layer.get_width()
            image_height = layer.get_height()

            # Vertical movement: slower
            self.y_offsets[current_set][i] -= player_dy * vertical_speeds[i]

            # Horizontal movement
            self.x_offsets[current_set][i] += player_dx * horizontal_speeds[i]

            # Wrap horizontally
            self.x_offsets[current_set][i] %= image_width


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