import pygame


# tailles à l'écran : une unité = 1/100 de l'écran, une parcelle = 10 unités
def get_parcels_size():
    unit_width, unit_height = define_unit_size()

    parcel_width = int(unit_width * 10)
    parcel_height = int(unit_height * 10)

    return parcel_width, parcel_height


def define_unit_size():
    # récupérer la taille de l'écran
    screen = pygame.display.get_surface()
    screen_width = screen.get_width()
    screen_height = screen.get_height()

    # normaliser en unités
    unit_width = screen_width / 100
    unit_height = screen_height / 100

    return unit_width, unit_height
