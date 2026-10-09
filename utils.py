import pygame
import random

def load_image(image, parcel_width, parcel_height):
    # taille du batiment = 1/10 du plateau
        if image != None:
                image = pygame.image.load(image).convert_alpha()
                image = pygame.transform.scale(image,(parcel_width,parcel_height))
        return image




# part de la tuile occupée par l'asphalte : la même pour toutes les routes, pour que les bords se raccordent
ROAD_WIDTH_RATIO = 0.72
# images de routes déjà préparées, pour ne pas les recharger à chaque case
road_images_cache = {}

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
# bord_x : bord où mesurer la route verticale ('haut' ou 'bas')
# bord_y : bord où mesurer la route horizontale ('gauche' ou 'droite'), None s'il n'y en a pas
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

# savoir s'il y a une route (tout sauf une maison) en haut, en bas, à gauche et à droite d'une case
def get_road_neighbors(matrix, x, y):
        haut = y > 0 and matrix[y-1][x] != 1
        bas = y < 9 and matrix[y+1][x] != 1
        gauche = x > 0 and matrix[y][x-1] != 1
        droite = x < 9 and matrix[y][x+1] != 1
        return haut, bas, gauche, droite

# angle (sens inverse des aiguilles d'une montre, comme pygame.transform.rotate) à appliquer à l'image d'une route
def get_road_rotation(matrix, x, y):
        haut, bas, gauche, droite = get_road_neighbors(matrix, x, y)
        valeur_case = matrix[y][x]

        # virage : l'image de base relie la droite et le bas
        if valeur_case == 5:
                if droite and bas: return 0
                if haut and droite: return 90
                if haut and gauche: return 180
                return 270 # bas et gauche

        # T : l'image de base relie gauche, droite et bas (il manque le haut)
        if valeur_case == 3:
                if not haut: return 0
                if not gauche: return 90
                if not bas: return 180
                return 270 # il manque la droite

        # ligne droite : l'image de base est verticale
        if valeur_case == 2:
                horizontale = (gauche and droite and not (haut and bas)) or (not haut and not bas)
                if horizontale: return 90

        return 0

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
        
# vérifier si toutes les cases "routes" sont connectées 
def roads_are_connected(matrix):
        # cases déjà visitées
        known_parcels = set()
        # vérifier si il y a plusieurs zones (non connectées)
        all_zones =[]

        # chercher zone vide
        for column in range(10):
                for line in range(10):
                        if matrix[column][line] == 0 and (line, column) not in known_parcels :
                            current_zone = []
                            to_visit = [(line, column)]
                            # tant que chaque case de la zone n'est pas visité
                            while len(to_visit) > 0:
                                   # on check et prend les dernieres valeurs de la liite
                                   current_x, current_y = to_visit.pop(0) 

                                   if (current_x, current_y) not in known_parcels:
                                          known_parcels.add((current_x,current_y))
                                          current_zone.append((current_x, current_y))
                                          #vérifier tous les voisins en X
                                          neighbors = [(current_x, current_y-1), (current_x, current_y+1),(current_x-1, current_y),(current_x+1, current_y)]

                                          for neighbor_x, neighbor_y in neighbors:
                                                 # vérifier si le voisin est sur la map (0 à 9)
                                                 if 0 <= neighbor_x <10  and 0 <= neighbor_y < 10 :
                                                    # si c'est une route
                                                    if matrix[neighbor_y][neighbor_x] == 0 and (neighbor_x,neighbor_y) not in known_parcels:
                                                           to_visit.append((neighbor_x,neighbor_y))
                            # quand la liste d'attente est vide j'ajoute la zone                               
                            all_zones.append(current_zone)
        return all_zones


# supprimer des maisons jusqu'à ce que toutes les cases vides (0) forment une seule zone
def connect_all_zones(matrix):
        all_zones = roads_are_connected(matrix)

        # aucune case vide : on en crée une au hasard pour démarrer le réseau
        if len(all_zones) == 0:
                matrix[random.randint(0, 9)][random.randint(0, 9)] = 0
                all_zones = roads_are_connected(matrix)

        while len(all_zones) > 1:
                zone_A = all_zones[0]

                # chercher la case de zone A et la case d'une autre zone les plus proches
                meilleure_distance = 999
                xa, ya, xb, yb = None, None, None, None
                for zone_B in all_zones[1:]:
                        for (x1, y1) in zone_A:
                                for (x2, y2) in zone_B:
                                        distance = abs(x1 - x2) + abs(y1 - y2)
                                        if distance < meilleure_distance:
                                                meilleure_distance = distance
                                                xa, ya, xb, yb = x1, y1, x2, y2

                # creuser un chemin de A vers B en détruisant les maisons sur le passage
                # (pas plus de 3 pas tout droit pour éviter les longues lignes droites)
                direction_precedente = None # True pour X, False pour Y
                compteur_ligne_droite = 0
                while xa != xb or ya != yb:
                        if xa != xb and ya != yb:
                                if compteur_ligne_droite >= 3:
                                        bouger_en_x = not direction_precedente
                                else:
                                        bouger_en_x = random.choice([True, False])
                        else:
                                bouger_en_x = xa != xb

                        if bouger_en_x:
                                xa += 1 if xa < xb else -1
                        else:
                                ya += 1 if ya < yb else -1

                        if direction_precedente == bouger_en_x:
                                compteur_ligne_droite += 1
                        else:
                                compteur_ligne_droite = 1
                                direction_precedente = bouger_en_x

                        matrix[ya][xa] = 0

                # le chemin a pu toucher d'autres zones au passage : on recalcule
                all_zones = roads_are_connected(matrix)

        return all_zones


# une case est un croisement (T ou +) si c'est une route avec au moins 3 routes autour
def is_intersection(matrix, x, y):
        return matrix[y][x] != 1 and sum(get_road_neighbors(matrix, x, y)) >= 3

# éviter deux croisements collés : on met une maison sur une des routes en trop,
# seulement si toutes les routes restent connectées (sinon on laisse les deux croisements)
def separate_intersections(matrix):
        paires_impossibles = set()
        modifie = True
        while modifie:
                modifie = False
                for y in range(10):
                        for x in range(10):
                                if not is_intersection(matrix, x, y):
                                        continue
                                for vx, vy in [(x+1, y), (x, y+1)]:
                                        if vx > 9 or vy > 9 or not is_intersection(matrix, vx, vy):
                                                continue
                                        if ((x, y), (vx, vy)) in paires_impossibles:
                                                continue

                                        # routes candidates : les voisins des deux croisements, sauf les croisements eux-mêmes
                                        candidats = []
                                        for cx, cy in [(x, y), (vx, vy)]:
                                                for nx, ny in [(cx, cy-1), (cx, cy+1), (cx-1, cy), (cx+1, cy)]:
                                                        if 0 <= nx < 10 and 0 <= ny < 10 and matrix[ny][nx] != 1 and (nx, ny) not in [(x, y), (vx, vy)]:
                                                                candidats.append((nx, ny))
                                        random.shuffle(candidats)

                                        separe = False
                                        for nx, ny in candidats:
                                                ancienne_valeur = matrix[ny][nx]
                                                matrix[ny][nx] = 1
                                                # on garde la maison seulement si les routes restent connectées
                                                # et qu'aucune maison autour ne se retrouve sans route
                                                if len(roads_are_connected(matrix)) == 1 and not houses_around_are_isolated(matrix, nx, ny):
                                                        separe = True
                                                        break
                                                matrix[ny][nx] = ancienne_valeur

                                        if separe:
                                                modifie = True
                                        else:
                                                paires_impossibles.add(((x, y), (vx, vy)))


# une maison est isolée si elle n'a aucune route en haut, en bas, à gauche ou à droite
def house_is_isolated(matrix, x, y):
        return matrix[y][x] == 1 and not any(get_road_neighbors(matrix, x, y))

# vérifier si la case (x, y) ou une de ses voisines est une maison isolée
def houses_around_are_isolated(matrix, x, y):
        for cx, cy in [(x, y), (x, y-1), (x, y+1), (x-1, y), (x+1, y)]:
                if 0 <= cx < 10 and 0 <= cy < 10 and house_is_isolated(matrix, cx, cy):
                        return True
        return False

# donner une route à chaque maison isolée, en détruisant une maison voisine
# (on préfère une voisine qui touche déjà une route : la nouvelle route est alors directement reliée au réseau)
def connect_isolated_houses(matrix):
        isolee_trouvee = True
        while isolee_trouvee:
                isolee_trouvee = False
                for y in range(10):
                        for x in range(10):
                                if not house_is_isolated(matrix, x, y):
                                        continue
                                isolee_trouvee = True

                                voisines = [(nx, ny) for nx, ny in [(x, y-1), (x, y+1), (x-1, y), (x+1, y)] if 0 <= nx < 10 and 0 <= ny < 10]
                                bien_placees = [(nx, ny) for nx, ny in voisines if any(get_road_neighbors(matrix, nx, ny))]
                                nx, ny = random.choice(bien_placees or voisines)
                                matrix[ny][nx] = 0

                # les nouvelles routes peuvent être séparées du réseau : on les relie
                connect_all_zones(matrix)


# choisir la maison qui sera la pizzeria : il faut une route juste en dessous (y+1) pour que le joueur y démarre
def choose_pizzeria(matrix):
        candidates = [(x, y) for y in range(9) for x in range(10) if matrix[y][x] == 1 and matrix[y+1][x] != 1]

        # aucune maison n'a de route en dessous (très rare) : on en crée une sous une maison au hasard
        if len(candidates) == 0:
                maisons = [(x, y) for y in range(9) for x in range(10) if matrix[y][x] == 1]
                x, y = random.choice(maisons)
                matrix[y+1][x] = 0
                connect_all_zones(matrix)
                return x, y

        return random.choice(candidates)
