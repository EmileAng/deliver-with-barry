from models.parcel import Parcel
from utils import load_road_image, get_parcels_size

# pour chaque type de route : l'image, et les bords où mesurer l'asphalte
# (bord haut/bas pour la route verticale, bord gauche/droite pour la route horizontale)
ROAD_SPRITES = {
    2: ('assets/roads/one_way_road.png', 'haut', None),
    3: ('assets/roads/three_way_road.png', 'bas', 'gauche'),
    4: ('assets/roads/four_way_road.png', 'haut', 'gauche'),
    5: ('assets/roads/corner_road.png', 'bas', 'droite'),
}

class Road(Parcel):
    def __init__(self, id, image, location_x, location_y, grid_infos, rotation=0):
        super().__init__(id, None, location_x, location_y)

        parcel_width, parcel_height = get_parcels_size()

        image, bord_x, bord_y = ROAD_SPRITES[grid_infos]
        self.image = load_road_image(image, parcel_width, parcel_height, rotation, bord_x, bord_y)

        # créer hitbox batiment + ajustement de sa taille
        self.rect = self.image.get_rect()

        # placer le batiment
        self.rect.x = location_x
        self.rect.y = location_y

