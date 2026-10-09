import pygame


# chargement des images du jeu (sprites, routes recadrées)

# part de la tuile occupée par l'asphalte : la même pour toutes les routes, pour que les bords se raccordent
ROAD_WIDTH_RATIO = 0.72
# images de routes déjà préparées, pour ne pas les recharger à chaque case
road_images_cache = {}

def load_image(image, parcel_width, parcel_height):
    # taille du batiment = 1/10 du plateau
        if image != None:
                image = pygame.image.load(image).convert_alpha()
                image = pygame.transform.scale(image,(parcel_width,parcel_height))
        return image

# trouver où commence et où finit l'asphalte (gris foncé) sur une ligne de pixels
# (les petits trous comme les pointillés blancs sont ignorés)
def find_asphalt(pixels):
        asphalte = [i for i, (r, g, b, a) in enumerate(pixels) if a > 200 and 60 < r < 120 and abs(r-g) < 12 and abs(g-b) < 12]
        morceaux = [[asphalte[0], asphalte[0]]]
        for i in asphalte[1:]:
                if i - morceaux[-1][1] <= 10:
                        morceaux[-1][1] = i
                else:
                        morceaux.append([i, i])
        debut, fin = max(morceaux, key=lambda m: m[1] - m[0])
        return debut, fin + 1

# charger une route en la recadrant pour que l'asphalte soit centré et ait toujours la même largeur
def load_road_image(image, parcel_width, parcel_height, rotation, bord_x, bord_y):
        cle = (image, parcel_width, parcel_height, rotation)
        if cle in road_images_cache:
                return road_images_cache[cle]

        source = pygame.image.load(image).convert_alpha()
        w, h = source.get_size()

        # route verticale : centre et largeur de l'asphalte, mesurés à 4 px du bord
        ligne = 4 if bord_x == 'haut' else h - 5
        debut, fin = find_asphalt([tuple(source.get_at((x, ligne))) for x in range(w)])
        centre_x = (debut + fin) / 2
        cote = (fin - debut) / ROAD_WIDTH_RATIO

        # route horizontale : même chose sur le bord gauche ou droit (sinon on centre simplement)
        if bord_y != None:
                colonne = 4 if bord_y == 'gauche' else w - 5
                debut, fin = find_asphalt([tuple(source.get_at((colonne, y))) for y in range(h)])
                centre_y = (debut + fin) / 2
        else:
                centre_y = h / 2

        # découper un carré centré sur la route
        carre = pygame.Surface((round(cote), round(cote)), pygame.SRCALPHA)
        carre.blit(source, (round(cote / 2 - centre_x), round(cote / 2 - centre_y)))

        # tourner le carré (un carré tourné reste un carré) puis l'adapter à la parcelle
        carre = pygame.transform.rotate(carre, rotation)
        resultat = pygame.transform.smoothscale(carre, (parcel_width, parcel_height))

        road_images_cache[cle] = resultat
        return resultat
