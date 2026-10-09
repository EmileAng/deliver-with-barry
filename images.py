import pygame


# chargement des images du jeu (sprites, routes recadrées)

# part de la tuile occupée par l'asphalte : la même pour toutes les routes, pour que les bords se raccordent
ROAD_WIDTH_RATIO = 0.72

# images de routes déjà préparées, pour ne pas les recharger à chaque case
road_images_cache = {}


# charger une image à la taille d'une parcelle
def load_image(image, parcel_width, parcel_height):
    if image is not None:
        image = pygame.image.load(image).convert_alpha()
        image = pygame.transform.scale(image, (parcel_width, parcel_height))
    return image


# trouver où commence et où finit l'asphalte (gris foncé) sur une ligne de pixels
# (les petits trous comme les pointillés blancs sont ignorés)
def find_asphalt(pixels):
    asphalt = [i for i, (r, g, b, a) in enumerate(pixels)
               if a > 200 and 60 < r < 120 and abs(r - g) < 12 and abs(g - b) < 12]
    segments = [[asphalt[0], asphalt[0]]]
    for i in asphalt[1:]:
        if i - segments[-1][1] <= 10:
            segments[-1][1] = i
        else:
            segments.append([i, i])
    start, end = max(segments, key=lambda segment: segment[1] - segment[0])
    return start, end + 1


# charger une route en la recadrant pour que l'asphalte soit centré et ait toujours la même largeur
# edge_x : bord où mesurer la route verticale ('top' ou 'bottom')
# edge_y : bord où mesurer la route horizontale ('left' ou 'right'), None s'il n'y en a pas
def load_road_image(image, parcel_width, parcel_height, rotation, edge_x, edge_y):
    cache_key = (image, parcel_width, parcel_height, rotation)
    if cache_key in road_images_cache:
        return road_images_cache[cache_key]

    source = pygame.image.load(image).convert_alpha()
    width, height = source.get_size()

    # route verticale : centre et largeur de l'asphalte, mesurés à 4 px du bord
    row = 4 if edge_x == 'top' else height - 5
    start, end = find_asphalt([tuple(source.get_at((x, row))) for x in range(width)])
    center_x = (start + end) / 2
    side = (end - start) / ROAD_WIDTH_RATIO

    # route horizontale : même chose sur le bord gauche ou droit (sinon on centre simplement)
    if edge_y is not None:
        column = 4 if edge_y == 'left' else width - 5
        start, end = find_asphalt([tuple(source.get_at((column, y))) for y in range(height)])
        center_y = (start + end) / 2
    else:
        center_y = height / 2

    # découper un carré centré sur la route
    square = pygame.Surface((round(side), round(side)), pygame.SRCALPHA)
    square.blit(source, (round(side / 2 - center_x), round(side / 2 - center_y)))

    # tourner le carré (un carré tourné reste un carré) puis l'adapter à la parcelle
    square = pygame.transform.rotate(square, rotation)
    result = pygame.transform.smoothscale(square, (parcel_width, parcel_height))

    road_images_cache[cache_key] = result
    return result
