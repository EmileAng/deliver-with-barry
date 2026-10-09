from models.parcel import Parcel


# la pizzeria
class Pizzeria(Parcel):

    def __init__(self, location_x, location_y):
        super().__init__('assets/houses/pizzeria.png', location_x, location_y)
