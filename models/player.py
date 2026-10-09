import pygame

from images import load_image
from utils import define_unit_size


# angle de rotation pour chaque direction (l'image de base regarde vers le haut,
# pygame.transform.rotate tourne dans le sens inverse des aiguilles d'une montre)
DIRECTIONS = {
    'up': 0,
    'up_left': 45,
    'left': 90,
    'down_left': 135,
    'down': 180,
    'down_right': 225,
    'right': 270,
    'up_right': 315,
}


class Player(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()

        unit_width, unit_height = define_unit_size()
        unit_height = unit_height * 5
        unit_width = unit_width * 2
        # charger l'image du joueur
        self.image = load_image("assets/player.png", unit_width, unit_height)

        # garder l'image d'origine : on tourne toujours à partir d'elle
        self.original_image = self.image
        self.direction = 'up'

        # position du joueur avec sa hitbox
        self.rect = self.image.get_rect()
        self.rect.x = 640
        self.rect.y = 35

        # inventaire
        self.inventory = []

        # PV + score
        self.max_lives = 3
        self.lives = 3
        self.score = 0

    # tourner le joueur vers une direction
    def look(self, direction):
        if direction == self.direction:
            return
        self.direction = direction

        # on garde le même centre, car l'image tournée n'a pas la même taille
        center = self.rect.center
        self.image = pygame.transform.rotate(self.original_image, DIRECTIONS[direction])
        self.rect = self.image.get_rect(center=center)

    # retenir la position avant de bouger (pour pouvoir revenir en arrière en cas de collision)
    def last_position(self):
        self.last_rect = self.rect.copy()
        self.last_image = self.image
        self.last_direction = self.direction

    # revenir à la position retenue
    def go_back(self):
        self.rect = self.last_rect
        self.image = self.last_image
        self.direction = self.last_direction

    # déplacements
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

        vertical = ''
        if dy < 0:
            vertical = 'up'
        if dy > 0:
            vertical = 'down'
        horizontal = ''
        if dx < 0:
            horizontal = 'left'
        if dx > 0:
            horizontal = 'right'

        if vertical and horizontal:
            self.look(vertical + '_' + horizontal)
        elif vertical or horizontal:
            self.look(vertical or horizontal)
