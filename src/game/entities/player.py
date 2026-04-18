import pygame
import sys



# Key input (continuous)
keys = pygame.key.get_pressed()

if keys[pygame.K_w]:
    player_y -= player_speed
if keys[pygame.K_s]:
    player_y += player_speed
if keys[pygame.K_a]:
    player_x -= player_speed
if keys[pygame.K_d]:
    player_x += player_speed/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"


pygame.draw.rect(screen, (0, 200, 255), (player_x, player_y, player_size, player_size))