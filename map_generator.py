import random


# génération de la ville : la matrice 10x10 (1 = maison, autre = route)


# savoir s'il y a une route (tout sauf une maison) en haut, en bas, à gauche et à droite d'une case
def get_road_neighbors(matrix, x, y):
    up = y > 0 and matrix[y - 1][x] != 1
    down = y < 9 and matrix[y + 1][x] != 1
    left = x > 0 and matrix[y][x - 1] != 1
    right = x < 9 and matrix[y][x + 1] != 1
    return up, down, left, right


# aligner le sprite dans le bon sens
def get_road_rotation(matrix, x, y):
    up, down, left, right = get_road_neighbors(matrix, x, y)
    cell_value = matrix[y][x]

    # virage
    if cell_value == 5:
        if right and down:
            return 0
        if up and right:
            return 90
        if up and left:
            return 180
        return 270  # bas et gauche

    # T
    if cell_value == 3:
        if not up:
            return 0
        if not left:
            return 90
        if not down:
            return 180
        return 270  # il manque la droite

    # ligne droite
    if cell_value == 2:
        horizontal = (left and right and not (up and down)) or (not up and not down)
        if horizontal:
            return 90

    return 0


# vérifier si toutes les cases "routes" sont connectées
def roads_are_connected(matrix):
    known_parcels = set()
    # vérifier s'il y a plusieurs zones (non connectées)
    all_zones = []
    # chercher une zone vide
    for y in range(10):
        for x in range(10):
            if matrix[y][x] == 0 and (x, y) not in known_parcels:
                current_zone = []
                to_visit = [(x, y)]
                # tant que chaque case de la zone n'est pas visitée
                while len(to_visit) > 0:
                    # on prend la première case de la liste d'attente
                    current_x, current_y = to_visit.pop(0)

                    if (current_x, current_y) not in known_parcels:
                        known_parcels.add((current_x, current_y))
                        current_zone.append((current_x, current_y))
                        # vérifier les 4 voisins
                        neighbors = [(current_x, current_y - 1), (current_x, current_y + 1),
                                     (current_x - 1, current_y), (current_x + 1, current_y)]

                        for neighbor_x, neighbor_y in neighbors:
                            # vérifier si le voisin est sur la map (0 à 9)
                            if 0 <= neighbor_x < 10 and 0 <= neighbor_y < 10:
                                # si c'est une route
                                if matrix[neighbor_y][neighbor_x] == 0 and (neighbor_x, neighbor_y) not in known_parcels:
                                    to_visit.append((neighbor_x, neighbor_y))
                # quand la liste d'attente est vide, on ajoute la zone
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
        zone_a = all_zones[0]

        # chercher la case de la zone A et la case d'une autre zone les plus proches
        best_distance = 999
        xa, ya, xb, yb = None, None, None, None
        for zone_b in all_zones[1:]:
            for (x1, y1) in zone_a:
                for (x2, y2) in zone_b:
                    distance = abs(x1 - x2) + abs(y1 - y2)
                    if distance < best_distance:
                        best_distance = distance
                        xa, ya, xb, yb = x1, y1, x2, y2

        # creuser un chemin de A vers B en détruisant les maisons sur le passage
        # (pas plus de 3 pas tout droit pour éviter les longues lignes droites)
        previous_direction = None  # True pour X, False pour Y
        straight_count = 0
        while xa != xb or ya != yb:
            if xa != xb and ya != yb:
                if straight_count >= 3:
                    move_on_x = not previous_direction
                else:
                    move_on_x = random.choice([True, False])
            else:
                move_on_x = xa != xb

            if move_on_x:
                xa += 1 if xa < xb else -1
            else:
                ya += 1 if ya < yb else -1

            if previous_direction == move_on_x:
                straight_count += 1
            else:
                straight_count = 1
                previous_direction = move_on_x

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
    impossible_pairs = set()
    changed = True
    while changed:
        changed = False
        for y in range(10):
            for x in range(10):
                if not is_intersection(matrix, x, y):
                    continue
                for other_x, other_y in [(x + 1, y), (x, y + 1)]:
                    if other_x > 9 or other_y > 9 or not is_intersection(matrix, other_x, other_y):
                        continue
                    if ((x, y), (other_x, other_y)) in impossible_pairs:
                        continue
                    # routes candidates : les voisins des deux croisements, sauf les croisements eux-mêmes
                    candidates = []
                    for cx, cy in [(x, y), (other_x, other_y)]:
                        for nx, ny in [(cx, cy - 1), (cx, cy + 1), (cx - 1, cy), (cx + 1, cy)]:
                            if (0 <= nx < 10 and 0 <= ny < 10 and matrix[ny][nx] != 1
                                    and (nx, ny) not in [(x, y), (other_x, other_y)]):
                                candidates.append((nx, ny))
                    random.shuffle(candidates)
                    separated = False
                    for nx, ny in candidates:
                        old_value = matrix[ny][nx]
                        matrix[ny][nx] = 1
                        # on garde la maison seulement si les routes restent connectées
                        # et qu'aucune maison autour ne se retrouve sans route
                        if len(roads_are_connected(matrix)) == 1 and not houses_around_are_isolated(matrix, nx, ny):
                            separated = True
                            break
                        matrix[ny][nx] = old_value

                    if separated:
                        changed = True
                    else:
                        impossible_pairs.add(((x, y), (other_x, other_y)))


# une maison est isolée si elle n'a aucune route en haut, en bas, à gauche ou à droite
def house_is_isolated(matrix, x, y):
    return matrix[y][x] == 1 and not any(get_road_neighbors(matrix, x, y))


# vérifier si la case (x, y) ou une de ses voisines est une maison isolée
def houses_around_are_isolated(matrix, x, y):
    for cx, cy in [(x, y), (x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]:
        if 0 <= cx < 10 and 0 <= cy < 10 and house_is_isolated(matrix, cx, cy):
            return True
    return False


# donner une route à chaque maison isolée, en détruisant une maison voisine
def connect_isolated_houses(matrix):
    isolated_found = True
    while isolated_found:
        isolated_found = False
        for y in range(10):
            for x in range(10):
                if not house_is_isolated(matrix, x, y):
                    continue
                isolated_found = True

                neighbors = [(nx, ny) for nx, ny in [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
                             if 0 <= nx < 10 and 0 <= ny < 10]
                well_placed = [(nx, ny) for nx, ny in neighbors if any(get_road_neighbors(matrix, nx, ny))]
                nx, ny = random.choice(well_placed or neighbors)
                matrix[ny][nx] = 0

        # les nouvelles routes peuvent être séparées du réseau : on les relie
        connect_all_zones(matrix)


# choisir la maison qui sera la pizzeria
def choose_pizzeria(matrix):
    candidates = [(x, y) for y in range(9) for x in range(10)
                  if matrix[y][x] == 1 and matrix[y + 1][x] != 1]

    # aucune maison n'a de route en dessous (très rare) : on en crée une sous une maison au hasard
    if len(candidates) == 0:
        houses = [(x, y) for y in range(9) for x in range(10) if matrix[y][x] == 1]
        x, y = random.choice(houses)
        matrix[y + 1][x] = 0
        connect_all_zones(matrix)
        return x, y
    return random.choice(candidates)
