from models.parcel import Parcel

# la pizzeria : la base du joueur, d'où partent les livraisons
class PlayerBase (Parcel):
    def __init__(self, id, location_x, location_y):
        # Parcel s'occupe de charger l'image à la taille d'une parcelle et de la placer
        super().__init__(id, 'assets/houses/pizzeria.png', location_x, location_y)


