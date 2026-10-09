import pygame
from images import load_image
from utils import get_parcels_size


# les buildings ont en commun une position et ont besoin d'une image
class Parcel(pygame.sprite.Sprite):
    
    def __init__(self, image, location_x, location_y):
        super().__init__()

        parcel_width, parcel_height = get_parcels_size()
        if image != None:
            
            # convertir l'image aux proportions de l'écran
            self.image = load_image(image, parcel_width, parcel_height)

            # créer hitbox batiment + ajustement de sa taille
            self.rect = self.image.get_rect()

            # placer le batiment
            self.rect.x = location_x
            self.rect.y = location_y
        
        
        