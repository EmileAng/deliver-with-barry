import pygame

from images import load_image
from utils import get_parcels_size


# les bâtiments ont en commun une position et ont besoin d'une image
class Parcel(pygame.sprite.Sprite):

    def __init__(self, image, location_x, location_y):
        super().__init__()

        parcel_width, parcel_height = get_parcels_size()
        if image is not None:
            # convertir l'image aux proportions de l'écran
            self.image = load_image(image, parcel_width, parcel_height)

            # créer la hitbox du bâtiment à la taille de l'image
            self.rect = self.image.get_rect()

            # placer le bâtiment
            self.rect.x = location_x
            self.rect.y = location_y
