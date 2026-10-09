import pygame
from utils import load_image, define_unit_size
# angle de rotation pour chaque direction (l'image de base regarde vers le haut,
# pygame.transform.rotate tourne dans le sens inverse des aiguilles d'une montre)
DIRECTIONS = {
    'haut': 0,
    'haut_gauche': 45,
    'gauche': 90,
    'bas_gauche': 135,
    'bas': 180,
    'bas_droite': 225,
    'droite': 270,
    'haut_droite': 315,
}

class Player(pygame.sprite.Sprite):

    def __init__(self):
        # charger la super classe "pygame.sprite.Sprite" pour la gestion des collisions
        super().__init__()

        unit_width, unit_height = define_unit_size()
        unit_height = unit_height*5
        unit_width = unit_width*2
        # charger l'image du joueur
        self.image = load_image("assets/player.png",unit_width,unit_height)

        # garder l'image d'origine : on tourne toujours à partir d'elle, jamais à partir d'une image déjà tournée
        self.original_image = self.image
        self.direction = 'haut'

        # position du joueur avec sa hitbox
        self.rect = self.image.get_rect()
        self.rect.x = 640
        self.rect.y = 35

        # inventaire
        self.inventory = []

        # pdv + score
        self.max_lives = 3
        self.lives = 3
        self.score = 0

    # tourner le joueur vers une direction (ne fait rien s'il regarde déjà dans cette direction)
    def look(self, direction):
        if direction == self.direction:
            return
        self.direction = direction

        # on garde le même centre, car l'image tournée n'a pas la même taille (50x70 -> 70x50)
        centre = self.rect.center
        self.image = pygame.transform.rotate(self.original_image, DIRECTIONS[direction])
        self.rect = self.image.get_rect(center=centre)

    
    def last_position(self):
        self.last_rect = self.rect.copy()
        self.last_image = self.image
        self.last_direction = self.direction

    # revenir à la position retenue (position, image et direction, pour que l'image corresponde à la hitbox)
    def go_back(self):
        self.rect = self.last_rect
        self.image = self.last_image
        self.direction = self.last_direction

    # movements : dx et dy peuvent être négatifs (gauche / haut), positifs (droite / bas) ou 0
    # la hitbox (self.rect) bouge sur les deux axes en même temps, donc en diagonale si dx et dy ne sont pas 0
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

        # trouver le nom de la direction : 'haut', 'bas_droite', ...
        vertical = ''
        if dy < 0: vertical = 'haut'
        if dy > 0: vertical = 'bas'
        horizontal = ''
        if dx < 0: horizontal = 'gauche'
        if dx > 0: horizontal = 'droite'

        if vertical and horizontal:
            self.look(vertical + '_' + horizontal)
        elif vertical or horizontal:
            self.look(vertical or horizontal)



