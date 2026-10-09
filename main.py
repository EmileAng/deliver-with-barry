import json
import random

import pygame

from map_generator import (
    choose_pizzeria,
    connect_all_zones,
    connect_isolated_houses,
    get_road_neighbors,
    get_road_rotation,
    separate_intersections,
)
from models.house import House
from models.hud import Hud
from models.pizzeria import Pizzeria
from models.player import Player
from models.road import Road
from utils import get_parcels_size


# maximum de pizzas dans l'inventaire
MAX_PIZZAS = 7

# constantes de livraison
MAX_DELIVERIES = 3
FIRST_DELIVERY_DELAY = 20000  # millisecondes, au début de la partie
DELAY_DECREASE = 1000  # millisecondes en moins par livraison réussie
MIN_DELIVERY_DELAY = 10000  # millisecondes, jamais moins
DOUBLE_DELIVERY_CHANCE = 1 / 3  # probabilité que 2 demandes arrivent en même temps

# temps laissé pour livrer une demande : diminue aussi avec les livraisons
FIRST_DELIVERY_DURATION = 20000
DURATION_DECREASE = 500
MIN_DELIVERY_DURATION = 15000

# quand plus aucune maison n'attend de pizza, la prochaine demande arrive au plus tard après ce délai
EMPTY_DELIVERY_DELAY = 3000

# boost : 1 point de score perdu toutes les BOOST_COST_EVERY millisecondes de boost
BOOST_COST_EVERY = 1000

# musique de fond
MUSIC_PATH = "assets/music/barry-theme.mp3"
MUSIC_VOLUME = 0.05  # de 0.0 (muet) à 1.0 (max)

pygame.init()
pygame.font.init()

# lancer la musique de fond une seule fois, en boucle à l'infini (-1)
pygame.mixer.music.load(MUSIC_PATH)
pygame.mixer.music.set_volume(MUSIC_VOLUME)
pygame.mixer.music.play(-1)

# charger les scores sauvegardés (fichier absent ou vide : on part de zéro)
try:
    with open("data.json", "r", encoding="utf-8") as file:
        scores = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    scores = {}

screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Deliver with Barry")

# pouvoir définir les FPS
clock = pygame.time.Clock()

# liste des sprites de maisons
house_sprites = ["assets/houses/small_house.png", "assets/houses/house.png", "assets/houses/big_house.png"]

# charger le joueur
player = Player()

# charger l'image de fond du jeu
background = pygame.image.load('assets/background.jpg')
background = pygame.transform.scale(background, (1280, 720))

# initialiser la matrice : 1 = maison, 0 = route
matrix = []
for row in range(10):
    matrix.append([])
    for column in range(10):
        if random.random() < 0.6:
            matrix[row].append(1)
        else:
            matrix[row].append(0)

# supprimer des maisons jusqu'à ce que toutes les cases vides forment une seule zone
connect_all_zones(matrix)

# casser les boulevards
for y in range(9):
    for x in range(9):
        # si on trouve un énorme carré de routes
        if matrix[y][x] == 0 and matrix[y + 1][x] == 0 and matrix[y][x + 1] == 0 and matrix[y + 1][x + 1] == 0:
            # on force une maison dans le coin supérieur gauche pour séparer les voies
            matrix[y][x] = 1

# le nettoyage peut recouper le réseau : on reconnecte les zones
connect_all_zones(matrix)

# connecter les maisons isolées
connect_isolated_houses(matrix)

# on sépare les T et les + qui se touchent en remplaçant une route en trop par une maison
separate_intersections(matrix)

# une des maisons devient la pizzeria. Elle reste un 1 dans la matrice (c'est un bâtiment)
pizzeria_x, pizzeria_y = choose_pizzeria(matrix)

# choisir le type de chaque route
for y in range(10):
    for x in range(10):
        # si on tombe sur une route vide
        if matrix[y][x] == 0:
            # on regarde les 4 cases autour pour savoir où sont les routes
            up, down, left, right = get_road_neighbors(matrix, x, y)
            roads_around = up + down + left + right

            # on attribue le bon numéro selon le nombre de connexions
            if roads_around == 2 and not (up and down) and not (left and right):
                matrix[y][x] = 5  # virage (2 routes qui ne sont pas en face)
            elif roads_around <= 2:
                matrix[y][x] = 2  # ligne droite (ou cul-de-sac)
            elif roads_around == 3:
                matrix[y][x] = 3  # T
            elif roads_around == 4:
                matrix[y][x] = 4  # croisement

# taille des parcelles
parcel_width, parcel_height = get_parcels_size()

# créer les sprites à partir de la matrice
all_houses = pygame.sprite.Group()
all_roads = pygame.sprite.Group()

for y in range(10):
    for x in range(10):
        cell_value = matrix[y][x]
        pixel_x = x * parcel_width
        pixel_y = y * parcel_height

        if (x, y) == (pizzeria_x, pizzeria_y):
            pizzeria = Pizzeria(pixel_x, pixel_y)

        elif cell_value == 1:
            # choix au hasard de la maison
            house = House(random.choice(house_sprites), pixel_x, pixel_y)
            all_houses.add(house)

        else:
            # sécurité anti-trous : on force tout ce qui n'est pas une maison en ligne droite
            if cell_value not in [2, 3, 4, 5]:
                cell_value = 2
                matrix[y][x] = 2

            # on calcule de combien tourner l'image selon les routes voisines
            rotation = get_road_rotation(matrix, x, y)
            road = Road(pixel_x, pixel_y, cell_value, rotation)
            all_roads.add(road)

# faire apparaître le joueur en dessous de la pizzeria
player.rect.centerx = pizzeria.rect.centerx
player.rect.centery = pizzeria.rect.centery + parcel_height

# bandeau en haut à gauche (PV, pizzas, score)
hud = Hud()

# livraisons
last_delivery_time = pygame.time.get_ticks()
deliveries_done = 0
empty_since = None  # moment où il n'y a plus eu aucune demande (None s'il y en a)

# temps passé en boost (s'additionne d'un appui à l'autre, pour que les petits appuis comptent aussi)
boost_time = 0

# écran de fin
dark_overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
dark_overlay.fill((0, 0, 0, 170))
game_over_font = pygame.font.SysFont('Impact', 120)
game_over_text = game_over_font.render("GAME OVER", True, (255, 255, 255))
score_font = pygame.font.SysFont('Impact', 40)
score_saved = False

# renvoie de combien bouger en x et en y selon les flèches appuyées
def get_movement(keys, boost=False):
    player_speed = 2
    if boost:
        player_speed = 5
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


# détection des collisions avec une maison ou la pizzeria
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


# temps d'attente entre deux demandes, selon le nombre de livraisons déjà faites
def delivery_delay():
    return max(MIN_DELIVERY_DELAY, FIRST_DELIVERY_DELAY - deliveries_done * DELAY_DECREASE)


# temps laissé pour livrer une demande
def delivery_duration():
    return max(MIN_DELIVERY_DURATION, FIRST_DELIVERY_DURATION - deliveries_done * DURATION_DECREASE)


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

    # nouvelle demande quand le temps d'attente est écoulé (ou EMPTY_DELIVERY_DELAY sans aucune demande), s'il y a de la place
    normal_wait_over = now - last_delivery_time >= delivery_delay()
    empty_wait_over = empty_since is not None and now - empty_since >= EMPTY_DELIVERY_DELAY
    if normal_wait_over or empty_wait_over:
        last_delivery_time = now
        # une chance sur 3 que 2 demandes arrivent en même temps (sans dépasser MAX_DELIVERIES)
        new_count = 2 if random.random() < DOUBLE_DELIVERY_CHANCE else 1
        new_count = min(new_count, MAX_DELIVERIES - len(waiting_houses), len(free_houses))
        if new_count > 0:
            for house in random.sample(free_houses, new_count):
                house.ask_delivery(now, delivery_duration())
            empty_since = None


# empêcher que le joueur sorte de l'écran
def player_is_on_screen():
    return screen.get_rect().contains(player.rect)


# sauvegarder le score
def save_score():
    scores["best_score"] = max(scores.get("best_score", 0), player.score)
    scores.setdefault("all_scores", []).append(player.score)
    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(scores, file, indent=4)


# ==========================================
# --- BOUCLE DE JEU ---
# ==========================================

running = True
while running:
    for event in pygame.event.get():
        # détecte la fermeture de la fenêtre
        if event.type == pygame.QUIT:
            running = False

    screen.blit(background, (0, 0))
    all_roads.draw(screen)
    all_houses.draw(screen)
    screen.blit(pizzeria.image, pizzeria.rect)

    game_over = player.lives <= 0

    # boost avec ESPACE : il coûte 1 point de score par seconde
    keys = pygame.key.get_pressed()
    boost = False
    if keys[pygame.K_SPACE] and player.score > 0:
        boost = True
    dx, dy = get_movement(keys, boost)
    if game_over:
        dx, dy = 0, 0

    if boost and (dx != 0 or dy != 0):
        boost_time += clock.get_time()
        while boost_time >= BOOST_COST_EVERY and player.score > 0:
            boost_time -= BOOST_COST_EVERY
            player.score -= 1

    # mouvements : on essaie la diagonale, puis seulement en x, puis seulement en y
    for try_dx, try_dy in [(dx, dy), (dx, 0), (0, dy)]:
        if try_dx == 0 and try_dy == 0:
            continue
        player.last_position()
        player.move(try_dx, try_dy)
        if not player_touches_house() and player_is_on_screen():
            break
        player.go_back()

    # afficher les hitbox (touche H)
    if keys[pygame.K_h]:
        for house in all_houses:
            pygame.draw.rect(screen, (255, 0, 0), house.rect, 2)
        pygame.draw.rect(screen, (255, 165, 0), pizzeria.rect, 2)
        for road in all_roads:
            pygame.draw.rect(screen, (0, 255, 0), road.rect, 2)
        pygame.draw.rect(screen, (0, 0, 255), player.rect, 2)

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
        center_x, center_y = screen.get_rect().center
        screen.blit(game_over_text, game_over_text.get_rect(center=(center_x, center_y - 40)))
        score_text = score_font.render(f"Score : {player.score}", True, (255, 255, 255))
        screen.blit(score_text, score_text.get_rect(center=(center_x, center_y + 50)))
        best_text = score_font.render(f"Meilleur score : {scores['best_score']}", True, (255, 215, 0))
        screen.blit(best_text, best_text.get_rect(center=(center_x, center_y + 100)))

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
