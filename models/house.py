from models.parcel import Parcel
from images import load_image
from utils import get_parcels_size

# la demande devient urgente quand il reste ce temps pour livrer (en millisecondes)
# (la durée totale d'une demande est choisie par main.py et diminue avec les livraisons)
URGENT_REMAINING = 10000

# images des bulles, chargées une seule fois pour toutes les maisons
bubble_images = {}

def get_bubble_image(urgent):
    if not bubble_images:
        parcel_width, parcel_height = get_parcels_size()
        # la bulle fait la moitié d'une parcelle
        bubble_images[False] = load_image("assets/bubbles/bubble.png", parcel_width // 2, parcel_height // 2)
        bubble_images[True] = load_image("assets/bubbles/bubble_u.png", parcel_width // 2, parcel_height // 2)
    return bubble_images[urgent]

class House(Parcel):

    def __init__(self, image, location_x, location_y):

        super().__init__(image, location_x, location_y)

        self.delivery_state = False
        # moment (pygame.time.get_ticks) où la demande a commencé
        self.delivery_start = 0
        self.delivery_duration = 0

    def ask_delivery(self, now, duration):
        self.delivery_state = True
        self.delivery_start = now
        self.delivery_duration = duration

    def end_delivery(self):
        self.delivery_state = False

    # moitié du temps écoulé
    def is_urgent(self, now):
        return now - self.delivery_start >= self.delivery_duration - URGENT_REMAINING

    # le temps pour livrer est-il écoulé ?
    def is_expired(self, now):
        return now - self.delivery_start >= self.delivery_duration

    # afficher la bulle au-dessus de la maison si elle attend une livraison
    def draw_bubble(self, screen, now):
        if not self.delivery_state:
            return
        bubble = get_bubble_image(self.is_urgent(now))
        bubble_rect = bubble.get_rect(centerx=self.rect.centerx, bottom=self.rect.centery)
        screen.blit(bubble, bubble_rect)
