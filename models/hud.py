import pygame

# taille des icônes et espacements du bandeau 
ICON_SIZE = 28
PADDING = 8 
GAP = 6 
SPACING = 18 
MARGIN = 10 

# opacité du bandeau : normale, et quand il cache le joueur ou une maison qui attend une pizza
NORMAL_ALPHA = 255
HIDDEN_ALPHA = 60

# charger une icône en gardant ses proportions (son plus grand côté fait ICON_SIZE)
def load_icon(path):
    image = pygame.image.load(path).convert_alpha()
    width, height = image.get_size()
    scale = ICON_SIZE / max(width, height)
    return pygame.transform.smoothscale(image, (round(width * scale), round(height * scale)))

# le bandeau en haut à gauche : PV, pizzas transportées et score
class Hud:
    def __init__(self):
        self.heart = load_icon("assets/hud/heart.png")
        # coeur perdu : le même, presque transparent
        self.lost_heart = self.heart.copy()
        self.lost_heart.set_alpha(70)
        self.pizza = load_icon("assets/hud/pizzas.png")
        self.money = load_icon("assets/hud/score.png")
        self.font = pygame.font.SysFont('Impact', 22)

    def draw(self, screen, player, max_pizzas, all_houses):
        # chaque groupe est une liste d'images posées côte à côte
        hearts = [self.heart if i < player.lives else self.lost_heart for i in range(player.max_lives)]
        pizzas = [self.pizza, self.font.render(f"{len(player.inventory)}/{max_pizzas}", True, (255, 255, 255))]
        score = [self.money, self.font.render(str(player.score), True, (255, 255, 255))]
        groups = [hearts, pizzas, score]

        # calculer la taille du bandeau
        width = PADDING * 2 + SPACING * (len(groups) - 1)
        for group in groups:
            width += sum(image.get_width() for image in group) + GAP * (len(group) - 1)
        height = ICON_SIZE + PADDING * 2

        # fond noir semi-transparent aux coins arrondis
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 140), panel.get_rect(), border_radius=10)

        # poser les images, centrées verticalement
        x = PADDING
        for group in groups:
            for image in group:
                panel.blit(image, (x, (height - image.get_height()) // 2))
                x += image.get_width() + GAP
            x += SPACING - GAP

        # si le bandeau cache le joueur ou une maison qui attend une pizza, on le rend presque transparent
        panel_rect = panel.get_rect(topleft=(MARGIN, MARGIN))
        hides_something = panel_rect.colliderect(player.rect) or any(
            house.delivery_state and panel_rect.colliderect(house.rect) for house in all_houses)
        panel.set_alpha(HIDDEN_ALPHA if hides_something else NORMAL_ALPHA)

        screen.blit(panel, panel_rect)
