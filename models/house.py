from models.parcel import Parcel
from utils import load_image, get_parcels_size
import random

# durée max d'une demande de livraison, et moment où elle devient urgente (en millisecondes)
DELIVERY_DURATION = 20000
URGENT_AFTER = 10000

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

    def __init__(self, id, image, location_x, location_y):

        super().__init__(id, image, location_x, location_y)

        self.spawn = random.choices([True, False], weights=[80,20])[0]
        self.delivery_state = False
        # moment (pygame.time.get_ticks) où la demande a commencé
        self.delivery_start = 0

    # la maison demande une pizza
    def ask_delivery(self, now):
        self.delivery_state = True
        self.delivery_start = now

    # la pizza a été livrée (ou la demande a expiré)
    def end_delivery(self):
        self.delivery_state = False

    # plus que 10 secondes pour livrer ?
    def is_urgent(self, now):
        return now - self.delivery_start >= URGENT_AFTER

    # les 20 secondes sont-elles écoulées ?
    def is_expired(self, now):
        return now - self.delivery_start >= DELIVERY_DURATION

    # afficher la bulle au-dessus de la maison si elle attend une livraison
    def draw_bubble(self, screen, now):
        if not self.delivery_state:
            return
        bubble = get_bubble_image(self.is_urgent(now))
        # bulle centrée en haut de la maison
        bubble_rect = bubble.get_rect(centerx=self.rect.centerx, bottom=self.rect.centery)
        screen.blit(bubble, bubble_rect)
