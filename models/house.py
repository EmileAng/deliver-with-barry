from models.parcel import Parcel
import random

class House(Parcel):

    def __init__(self, id, image, location_x, location_y):
        
        super().__init__(id, image, location_x, location_y)

        self.spawn = random.choices([True, False], weights=[80,20])[0]
        self.delivery_state = False

