import pygame
from models.player import Player
from models.house import House
from models.road import Road
from models.pizzeria import PlayerBase
from models.hud import Hud
from utils import connect_all_zones, get_parcels_size, get_road_neighbors, get_road_rotation, separate_intersections, connect_isolated_houses, choose_pizzeria
import random
import json

# charger les composants à l'intérieur (collisions, décors, sprites)
pygame.init()

# initialiser et créer une police
pygame.font.init()
custom_font = pygame.font.SysFont('Impact', 30)

# charger les scores sauvegardés (une seule fois, avant la boucle)
# si le fichier n'existe pas ou est vide, on part de zéro
try:
    with open("data.json", "r", encoding="utf-8") as file :
        scores = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    scores = {}

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
connect_isolated_houses(matrix)
    
# --- ANTI-CROISEMENTS COLLÉS ---
# On sépare les T et les + qui se touchent en remplaçant une route en trop par une maison
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

# nombre maximum de pizzas que le joueur peut transporter
MAX_PIZZAS = 7

# bandeau en haut à gauche (PV, pizzas, score)
hud = Hud()

# le joueur touche-t-il une maison (ou la pizzeria) ?
def player_touches_house():
    global deliveries_done
    if player.rect.colliderect(pizzeria.rect):
        if len(player.inventory) < MAX_PIZZAS:
            player.inventory.append(1)
        return True
    for house in all_houses:
        if player.rect.colliderect(house.rect):
            # livrer une pizza si la maison en attend une et que le joueur en a
            # (chaque livraison rapporte entre 1 et 4 points)
            if house.delivery_state and len(player.inventory) > 0:
                player.inventory.pop()
                house.end_delivery()
                player.score += random.randint(1, 4)
                deliveries_done += 1
            return True
    return False

# --- LIVRAISONS ---
# une maison demande une pizza à intervalle régulier (3 demandes en même temps au maximum)
# plus le joueur a livré de pizzas, plus les demandes arrivent vite, sans descendre sous 10 secondes
MAX_DELIVERIES = 3
FIRST_DELIVERY_DELAY = 20000 # millisecondes, au début de la partie
DELAY_DECREASE = 1000 # millisecondes en moins par livraison réussie
MIN_DELIVERY_DELAY = 10000 # millisecondes, jamais moins
last_delivery_time = pygame.time.get_ticks()
deliveries_done = 0

# temps d'attente entre deux demandes, selon le nombre de livraisons déjà faites
def delivery_delay():
    return max(MIN_DELIVERY_DELAY, FIRST_DELIVERY_DELAY - deliveries_done * DELAY_DECREASE)

# temps laissé pour livrer une demande : diminue aussi avec les livraisons, sans descendre sous 15 secondes
FIRST_DELIVERY_DURATION = 20000 # millisecondes, au début de la partie
DURATION_DECREASE = 500 # millisecondes en moins par livraison réussie
MIN_DELIVERY_DURATION = 15000 # millisecondes, jamais moins

def delivery_duration():
    return max(MIN_DELIVERY_DURATION, FIRST_DELIVERY_DURATION - deliveries_done * DURATION_DECREASE)

# quand plus aucune maison n'attend de pizza, la prochaine demande arrive au plus tard 3 secondes après
EMPTY_DELIVERY_DELAY = 3000 # millisecondes
empty_since = None # moment où il n'y a plus eu aucune demande (None s'il y en a)

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

# boost : 1 point de score perdu par seconde de boost
# (le temps de boost s'additionne d'un appui à l'autre, pour que les petits appuis comptent aussi)
BOOST_COST_EVERY = 1000 # millisecondes
boost_time = 0

# le joueur est-il entièrement dans l'écran ? (contains : toute la hitbox doit être à l'intérieur)
def player_is_on_screen():
    return screen.get_rect().contains(player.rect)

# --- GAME OVER ---
# voile noir semi-transparent posé sur tout l'écran, et le texte en gros
dark_overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
dark_overlay.fill((0, 0, 0, 170))
game_over_font = pygame.font.SysFont('Impact', 120)
game_over_text = game_over_font.render("GAME OVER", True, (255, 255, 255))
score_font = pygame.font.SysFont('Impact', 40)

# le score n'est sauvegardé qu'une fois, au moment de la défaite (pas à chaque image)
score_saved = False

# sauvegarder le score de la partie et mettre à jour le meilleur score dans data.json
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

    # plus de PV : la partie est finie, le joueur ne peut plus bouger
    game_over = player.lives <= 0

    # bouger le joueur, sans jamais entrer dans une maison ni sortir de l'écran

    # boost avec ESPACE : il coûte 1 point de score par seconde, donc impossible sans score
    key = pygame.key.get_pressed()
    boost = False
    if key[pygame.K_SPACE] and player.score > 0:
        boost = True
    dx, dy = keyboard(boost)
    if game_over:
        dx, dy = 0, 0

    # on ne paie que si on roule vraiment en boost (pas si on reste sur place)
    if boost and (dx != 0 or dy != 0):
        boost_time += clock.get_time() # millisecondes depuis l'image précédente
        while boost_time >= BOOST_COST_EVERY and player.score > 0:
            boost_time -= BOOST_COST_EVERY
            player.score -= 1

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

    if key[pygame.K_h]:
        #afficher les hitbox
        for house in all_houses:
            pygame.draw.rect(screen,(255,0,0), house.rect, 2)
        pygame.draw.rect(screen,(255,165,0), pizzeria.rect, 2)
        for road in all_roads:
            pygame.draw.rect(screen,(0,255,0), road.rect,2)
        pygame.draw.rect(screen, (0,0,255), player.rect, 2)

    screen.blit(player.image, player.rect)

    # demandes de livraison : apparition, expiration et bulles (plus rien n'apparaît après la défaite)
    if not game_over:
        update_deliveries()
    now = pygame.time.get_ticks()
    for house in all_houses:
        house.draw_bubble(screen, now)

    # bandeau PV / pizzas / score, dessiné en dernier pour être par-dessus tout
    hud.draw(screen, player, MAX_PIZZAS, all_houses)

    # écran de fin : on assombrit tout et on écrit GAME OVER au milieu, avec le score et le meilleur score
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

    #screen.blit(house_test.image, house_test.rect)
    pygame.display.flip()

    clock.tick(60)
print(f"inventaire joueur :{player.inventory}")
print(f"toutes les zones {all_zones}")
print(f"matrice {matrix}")
pygame.quit()