import pygame
from models.player import Player
from models.house import House
from models.road import Road
from models.pizzeria import PlayerBase
from models.hud import Hud
from utils import get_parcels_size
from map_generator import connect_all_zones, get_road_neighbors, get_road_rotation, separate_intersections, connect_isolated_houses, choose_pizzeria
import random
import json


# maximum de pizza dans l'inventaire
MAX_PIZZAS = 7

# constantes de livraison
MAX_DELIVERIES = 3
FIRST_DELIVERY_DELAY = 20000 # millisecondes, au début de la partie
DELAY_DECREASE = 1000 # millisecondes en moins par livraison réussie
MIN_DELIVERY_DELAY = 10000 # millisecondes, jamais moins

# temps laissé pour livrer une demande : diminue aussi avec les livraisons
FIRST_DELIVERY_DURATION = 20000 
DURATION_DECREASE = 500 
MIN_DELIVERY_DURATION = 15000

# quand plus aucune maison n'attend de pizza, la prochaine demande arrive au plus tard après ce délai
EMPTY_DELIVERY_DELAY = 3000 

# boost : 1 point de score perdu toutes les BOOST_COST_EVERY millisecondes de boost
BOOST_COST_EVERY = 1000 

pygame.init()

# créer la police
pygame.font.init()
custom_font = pygame.font.SysFont('Impact', 30)

# charger les scores sauvegardés ou créer un fichier
try:
    with open("data.json", "r", encoding="utf-8") as file :
        scores = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    scores = {}

screen = pygame.display.set_mode((1280,720))
pygame.display.set_caption("Deliver with Barry")

# pouvoir définir les FPS
clock = pygame.time.Clock() 

# liste sprites batiments
houses_sprites = ["assets/houses/small_house.png", "assets/houses/house.png", "assets/houses/big_house.png"]

# charger joueur
player = Player()

# charger l'image de fond du jeu
background = pygame.image.load('assets/background.jpg')
background = pygame.transform.scale(background, (1280,720))

# calculer le nombre de batiment max à mettre sur la largeur
screen_width = screen.get_width()
screen_height = screen.get_height()

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

# Supprimer des maisons jusqu'à ce que toutes les cases vides forment une seule zone
all_zones = connect_all_zones(matrix)

# Casser les boulevards 
for y in range(9):
    for x in range(9):
        # Si on trouve un énorme carré de routes
        if matrix[y][x] == 0 and matrix[y+1][x] == 0 and matrix[y][x+1] == 0 and matrix[y+1][x+1] == 0:
            # On force une maison dans le coin supérieur gauche pour séparer les voies
            matrix[y][x] = 1

# Le nettoyage peut recouper le réseau : on reconnecte les zones
all_zones = connect_all_zones(matrix)

# Connecter les maisons isolées
connect_isolated_houses(matrix)
    
# On sépare les T et les + qui se touchent en remplaçant une route en trop par une maison
separate_intersections(matrix)

# Une des maisons devient la pizzeria. Elle reste un 1 dans la matrice (c'est un bâtiment)
pizzeria_x, pizzeria_y = choose_pizzeria(matrix)

# mettre les routes
for y in range(10):
    for x in range(10):
        # Si on tombe sur une route vide
        if matrix[y][x] == 0:
            # On regarde les 4 cases autour pour savoir où sont les routes
            haut, bas, gauche, droite = get_road_neighbors(matrix, x, y)
            routes_autour = haut + bas + gauche + droite

            # On attribue le bon numéro selon le nombre de connexions
            if routes_autour == 2 and not (haut and bas) and not (gauche and droite):
                matrix[y][x] = 5 # Virage (2 routes qui ne sont pas en face)
            elif routes_autour <= 2:
                matrix[y][x] = 2 
            elif routes_autour == 3:
                matrix[y][x] = 3 
            elif routes_autour == 4:
                matrix[y][x] = 4 

# taille des parcelles
parcel_width, parcel_height = get_parcels_size()

# afficher les assets par rapport à la matrice
all_houses.empty()
all_roads.empty()   

for y in range(10):
    for x in range(10):
        valeur_case = matrix[y][x]
        pixel_x = x * parcel_width
        pixel_y = y * parcel_height

        # pizzeria
        if (x, y) == (pizzeria_x, pizzeria_y):
            pizzeria = PlayerBase(pixel_x, pixel_y)

        elif valeur_case == 1:
            # choix random de la maison
            maison = House(random.choice(houses_sprites), pixel_x, pixel_y)
            all_houses.add(maison)
            
        elif valeur_case != 1:
            # Sécurité anti-trous : on force tout ce qui n'est pas une maison en ligne droite
            if valeur_case not in [2, 3, 4, 5]:
                valeur_case = 2
                matrix[y][x] = 2

            # On calcule de combien tourner l'image selon les routes voisines
            rotation = get_road_rotation(matrix, x, y)
            route = Road(pixel_x, pixel_y, valeur_case, rotation)
            all_roads.add(route)

# faire apparaître le joueur en dessous de la pizzeria
player.rect.centerx = pizzeria.rect.centerx
player.rect.centery = pizzeria.rect.centery + parcel_height

def keyboard(boost=False):
    player_speed = 2
    if boost == True :
        player_speed = 5
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
# bandeau en haut à gauche (PV, pizzas, score)
hud = Hud()

# detection collision maison/pizzeria
def player_touches_house():
    global deliveries_done
    if player.rect.colliderect(pizzeria.rect):
        if len(player.inventory) < MAX_PIZZAS:
            player.inventory.append(1)
        return True
    for house in all_houses:
        if player.rect.colliderect(house.rect):
            # livrer une pizza si la maison en attend une et que le joueur en a
            if house.delivery_state and len(player.inventory) > 0:
                player.inventory.pop()
                house.end_delivery()
                player.score += random.randint(1, 4)
                deliveries_done += 1
            return True
    return False

last_delivery_time = pygame.time.get_ticks()
deliveries_done = 0

# temps d'attente entre deux demandes, selon le nombre de livraisons déjà faites
def delivery_delay():
    return max(MIN_DELIVERY_DELAY, FIRST_DELIVERY_DELAY - deliveries_done * DELAY_DECREASE)

# temps laissé pour livrer une demande
def delivery_duration():
    return max(MIN_DELIVERY_DURATION, FIRST_DELIVERY_DURATION - deliveries_done * DURATION_DECREASE)

# quand plus aucune maison n'attend de pizza, la prochaine demande arrive au plus tard EMPTY_DELIVERY_DELAY après
empty_since = None 

def update_deliveries():
    global last_delivery_time, empty_since
    now = pygame.time.get_ticks()

    # les demandes dont le temps est écoulé sont ratées : le joueur perd un PV
    for house in all_houses:
        if house.delivery_state and house.is_expired(now):
            house.end_delivery()
            player.lives = max(0, player.lives - 1)

    waiting_houses = [house for house in all_houses if house.delivery_state]
    free_houses = [house for house in all_houses if not house.delivery_state]

    # retenir depuis quand plus aucune maison n'attend
    if len(waiting_houses) > 0:
        empty_since = None
    elif empty_since is None:
        empty_since = now

    # nouvelle demande quand le temps d'attente est écoulé (ou 3 secondes sans aucune demande), s'il y a de la place
    normal_wait_over = now - last_delivery_time >= delivery_delay()
    empty_wait_over = empty_since is not None and now - empty_since >= EMPTY_DELIVERY_DELAY
    if normal_wait_over or empty_wait_over:
        last_delivery_time = now
        if len(waiting_houses) < MAX_DELIVERIES and len(free_houses) > 0:
            random.choice(free_houses).ask_delivery(now, delivery_duration())
            empty_since = None

# temps passé en boost (s'additionne d'un appui à l'autre, pour que les petits appuis comptent aussi)
boost_time = 0

# empêcher que le joueur sorte de l'écran
def player_is_on_screen():
    return screen.get_rect().contains(player.rect)

# --- GAME OVER ---
dark_overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
dark_overlay.fill((0, 0, 0, 170))
game_over_font = pygame.font.SysFont('Impact', 120)
game_over_text = game_over_font.render("GAME OVER", True, (255, 255, 255))
score_font = pygame.font.SysFont('Impact', 40)

score_saved = False

# sauvegarder du score
def save_score():
    scores["best_score"] = max(scores.get("best_score", 0), player.score)
    scores.setdefault("all_scores", []).append(player.score)
    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(scores, file, indent=4)

while running :
    for event in pygame.event.get():
        # détecte la fermeture de page
        if event.type == pygame.QUIT: 
            running = False

    screen.blit(background, (0,0))
    all_roads.draw(screen)
    all_houses.draw(screen)
    screen.blit(pizzeria.image, pizzeria.rect)

    game_over = player.lives <= 0

    # boost avec ESPACE : il coûte 1 point de score par seconde
    key = pygame.key.get_pressed()
    boost = False
    if key[pygame.K_SPACE] and player.score > 0:
        boost = True
    dx, dy = keyboard(boost)
    if game_over:
        dx, dy = 0, 0

    if boost and (dx != 0 or dy != 0):
        boost_time += clock.get_time() 
        while boost_time >= BOOST_COST_EVERY and player.score > 0:
            boost_time -= BOOST_COST_EVERY
            player.score -= 1

    # mouvements
    for essai_dx, essai_dy in [(dx, dy), (dx, 0), (0, dy)]:
        if essai_dx == 0 and essai_dy == 0:
            continue
        player.last_position()
        player.move(essai_dx, essai_dy)
        if not player_touches_house() and player_is_on_screen():
            break 
        player.go_back()

        # afficher les hitbox
    if key[pygame.K_h]:
        for house in all_houses:
            pygame.draw.rect(screen,(255,0,0), house.rect, 2)
        pygame.draw.rect(screen,(255,165,0), pizzeria.rect, 2)
        for road in all_roads:
            pygame.draw.rect(screen,(0,255,0), road.rect,2)
        pygame.draw.rect(screen, (0,0,255), player.rect, 2)

    screen.blit(player.image, player.rect)

    if not game_over:
        update_deliveries()
    now = pygame.time.get_ticks()
    for house in all_houses:
        house.draw_bubble(screen, now)

    # bandeau PV / pizzas / score, dessiné en dernier pour être par-dessus tout
    hud.draw(screen, player, MAX_PIZZAS, all_houses)

    # écran de fin
    if game_over:
        if not score_saved:
            save_score()
            score_saved = True

        screen.blit(dark_overlay, (0, 0))
        centre_x, centre_y = screen.get_rect().center
        screen.blit(game_over_text, game_over_text.get_rect(center=(centre_x, centre_y - 40)))
        score_text = score_font.render(f"Score : {player.score}", True, (255, 255, 255))
        screen.blit(score_text, score_text.get_rect(center=(centre_x, centre_y + 50)))
        best_text = score_font.render(f"Meilleur score : {scores['best_score']}", True, (255, 215, 0))
        screen.blit(best_text, best_text.get_rect(center=(centre_x, centre_y + 100)))

    pygame.display.flip()

    clock.tick(60)
pygame.quit()