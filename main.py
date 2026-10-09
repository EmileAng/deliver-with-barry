import pygame
from models.player import Player
from models.house import House
from models.road import Road
from models.pizzeria import PlayerBase
from utils import connect_all_zones, get_parcels_size, get_road_neighbors, get_road_rotation, separate_intersections, connect_isolated_houses, choose_pizzeria
import random

# charger les composants à l'intérieur (collisions, décors, sprites)
pygame.init()

# initialiser et créer une police
pygame.font.init()
custom_font = pygame.font.SysFont('Impact', 30)

screen = pygame.display.set_mode((1280,720))
pygame.display.set_caption("Mon jeu")
clock = pygame.time.Clock() # définir les FPS
# charger sprite batiment
houses_sprites = ["assets/houses/small_house.png", "assets/houses/house.png", "assets/houses/big_house.png"]
#house_test = Building(1, house_sprite, 50,50)
# charger joueur
player = Player()

# charger l'image de fond du jeu
background = pygame.image.load('assets/background.jpg')
background = pygame.transform.scale(background, (1280,720))

# calculer le nombre de batiment max à mettre sur la largeur
screen_width = screen.get_width()
screen_height = screen.get_height()

# parcel width et height = 10/100 unités
parcel_location_x = 0
parcel_location_y = 0
# initialiser matrice
matrix=[]
all_houses = pygame.sprite.Group()
all_roads = pygame.sprite.Group()

running = True
for line in range(10): 
        matrix.append([])
        for column in range(10):
            if random.random() < 0.6:
                matrix[line].append(1)
            else:
                matrix[line].append(0)
            


'''all_zones = roads_are_connected(matrix)
if len(all_zones) == 1:
     print('tout est relié')
else : 
     print(f"aie, il y a {len(all_zones)} morceaux de route séparés")'''

# Supprimer des maisons jusqu'à ce que toutes les cases vides forment une seule zone
all_zones = connect_all_zones(matrix)

# ==========================================
# --- PASSAGE DE NETTOYAGE DE LA VILLE ---
# ==========================================

# Règle 2 : Casser les boulevards (pas de blocs 2x2 de routes)
# On scanne la carte par carrés de 2x2
for y in range(9):
    for x in range(9):
        # Si on trouve un énorme carré de routes
        if matrix[y][x] == 0 and matrix[y+1][x] == 0 and matrix[y][x+1] == 0 and matrix[y+1][x+1] == 0:
            # On force une maison dans le coin supérieur gauche pour séparer les voies
            matrix[y][x] = 1

# Le nettoyage peut recouper le réseau : on reconnecte les zones
all_zones = connect_all_zones(matrix)

# Connecter les maisons isolées
# (on le fait APRÈS la règle 2, car la règle 2 pose des maisons qui peuvent enfermer leurs voisines)
connect_isolated_houses(matrix)
    
# --- ANTI-CROISEMENTS COLLÉS ---
# On sépare les T et les + qui se touchent en remplaçant une route en trop par une maison
# (le tiling d'après se base sur les vrais voisins, donc l'image correspond toujours aux routes)
separate_intersections(matrix)

# --- PIZZERIA ---
# Une des maisons devient la pizzeria. Elle reste un 1 dans la matrice (c'est un bâtiment),
# on retient juste sa position. Il y a forcément une route juste en dessous.
pizzeria_x, pizzeria_y = choose_pizzeria(matrix)

# TILING
for y in range(10):
    for x in range(10):
        
        # Si on tombe sur une route brute
        if matrix[y][x] == 0:
            # On regarde les 4 cases autour pour savoir où sont les routes
            haut, bas, gauche, droite = get_road_neighbors(matrix, x, y)
            routes_autour = haut + bas + gauche + droite

            # On attribue le bon numéro selon le nombre de connexions
            if routes_autour == 2 and not (haut and bas) and not (gauche and droite):
                matrix[y][x] = 5 # Virage (2 routes qui ne sont pas en face)
            elif routes_autour <= 2:
                matrix[y][x] = 2 # Ligne droite (ou cul-de-sac)
            elif routes_autour == 3:
                matrix[y][x] = 3 # T
            elif routes_autour == 4:
                matrix[y][x] = 4 # X

# On récupère la taille dynamique de tes parcelles
parcel_width, parcel_height = get_parcels_size()


all_houses.empty()
all_roads.empty()   
# On parcourt la matrice ligne par ligne (y) et colonne par colonne (x)
for y in range(10):
    for x in range(10):
        valeur_case = matrix[y][x]
        
        # Calcul des vraies coordonnées en pixels sur l'écran
        pixel_x = x * parcel_width
        pixel_y = y * parcel_height
        
        # Création d'un ID unique pour la parcelle (utile pour le debug)
        parcel_id = f"{x}_{y}"
        
        if (x, y) == (pizzeria_x, pizzeria_y):
            # C'est la pizzeria
            pizzeria = PlayerBase(parcel_id, pixel_x, pixel_y)

        elif valeur_case == 1:
            # C'est une maison : petite, normale ou grande, au hasard
            maison = House(parcel_id, random.choice(houses_sprites), pixel_x, pixel_y)
            all_houses.add(maison)
            
        elif valeur_case != 1:
            # Sécurité anti-trous : on force tout ce qui n'est pas une maison en ligne droite
            if valeur_case not in [2, 3, 4, 5]:
                valeur_case = 2
                matrix[y][x] = 2

            # On calcule de combien tourner l'image selon les routes voisines
            rotation = get_road_rotation(matrix, x, y)
            route = Road(parcel_id, None, pixel_x, pixel_y, valeur_case, rotation)
            all_roads.add(route)

# faire apparaître le joueur au milieu de la route juste en dessous de la pizzeria (y+1)
player.rect.centerx = pizzeria.rect.centerx
player.rect.centery = pizzeria.rect.centery + parcel_height

# déplacements : renvoie de combien bouger en x et en y selon les flèches appuyées
# (deux flèches en même temps = diagonale, deux flèches opposées s'annulent)
player_speed = 2
def keyboard():
    keys = pygame.key.get_pressed()
    dx = 0
    dy = 0
    if keys[pygame.K_RIGHT]:
        dx += player_speed
    if keys[pygame.K_LEFT]:
        dx -= player_speed
    if keys[pygame.K_DOWN]:
        dy += player_speed
    if keys[pygame.K_UP]:
        dy -= player_speed
    return dx, dy

# le joueur touche-t-il une maison (ou la pizzeria) ?
def player_touches_house():
    if player.rect.colliderect(pizzeria.rect):
        return True
    for house in all_houses:
        if player.rect.colliderect(house.rect):
            return True
    return False

# le joueur est-il entièrement dans l'écran ? (contains : toute la hitbox doit être à l'intérieur)
def player_is_on_screen():
    return screen.get_rect().contains(player.rect)


while running :
    for event in pygame.event.get():
        # détecte la fermeture de page
        if event.type == pygame.QUIT: 
            running = False

    screen.blit(background, (0,0))
    all_roads.draw(screen)
    all_houses.draw(screen)
    screen.blit(pizzeria.image, pizzeria.rect)
    # bouger le joueur, sans jamais entrer dans une maison ni sortir de l'écran
    dx, dy = keyboard()
    # on essaie d'abord le vrai mouvement (diagonale comprise), puis seulement en x, puis seulement en y :
    # en diagonale contre une maison, le joueur glisse le long du mur au lieu de rester bloqué
    for essai_dx, essai_dy in [(dx, dy), (dx, 0), (0, dy)]:
        if essai_dx == 0 and essai_dy == 0:
            continue
        # retenir la position AVANT de bouger, puis bouger
        player.last_position()
        player.move(essai_dx, essai_dy)
        if not player_touches_house() and player_is_on_screen():
            break # ce mouvement est possible, on le garde
        player.go_back()

    #afficher les hitbox
    for house in all_houses:
        pygame.draw.rect(screen,(255,0,0), house.rect, 2)
    pygame.draw.rect(screen,(255,165,0), pizzeria.rect, 2)
    for road in all_roads:
        pygame.draw.rect(screen,(0,255,0), road.rect,2)

    # afficher la hitbox du joueur
    pygame.draw.rect(screen, (0,0,255), player.rect, 2)

    screen.blit(player.image, player.rect)

    #screen.blit(house_test.image, house_test.rect)
    pygame.display.flip()

    clock.tick(60)
print(all_zones)
print(matrix)
pygame.quit()