from images import load_road_image
from models.parcel import Parcel
from utils import get_parcels_size


# pour chaque type de route : l'image, et les bords où mesurer l'asphalte
# (bord haut/bas pour la route verticale, bord gauche/droite pour la route horizontale)
ROAD_SPRITES = {
    2: ('assets/roads/one_way_road.png', 'top', None),
    3: ('assets/roads/three_way_road.png', 'bottom', 'left'),
    4: ('assets/roads/four_way_road.png', 'top', 'left'),
    5: ('assets/roads/corner_road.png', 'bottom', 'right'),
}


class Road(Parcel):

    def __init__(self, location_x, location_y, road_type, rotation=0):
        super().__init__(None, location_x, location_y)

        parcel_width, parcel_height = get_parcels_size()

        image, edge_x, edge_y = ROAD_SPRITES[road_type]
        self.image = load_road_image(image, parcel_width, parcel_height, rotation, edge_x, edge_y)

        # créer la hitbox de la route à la taille de l'image
        self.rect = self.image.get_rect()

        # placer la route
        self.rect.x = location_x
        self.rect.y = location_y
