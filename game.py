import pygame
from pygame.locals import *
import pickle
from os import path

pygame.init()

clock = pygame.time.Clock()
fps = 60

# Seteo de pantalla
screen_width = 700
screen_height = 700
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Platformer")

# Definir variables de juego
tile_size = 35
game_over = 0
main_menu = True
level = 1
max_levels = 3

# Carga de imagenes
sun_img = pygame.image.load("./img/sun.png")
bg_img = pygame.image.load("./img/sky.png")
restart_img = pygame.image.load("./img/restart_btn.png")
start_img = pygame.image.load("./img/start_btn.png")
exit_img = pygame.image.load("./img/exit_btn.png")

#Resetar nivel
def reset_level(level):
    player.reset(100, screen_height - 130) 
    blob_group.empty()
    lava_group.empty()
    exit_group.empty()

    #Cargar niveles 
    if path.exists(f'level{level}_data'):
        pickle_in = open(f'level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)
    world = World(world_data)

    return world

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False
        # obtener posicion del mouse
        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if (
                pygame.mouse.get_pressed()[0] == 1 and self.clicked == False
            ):  # click izquierdo
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:  # Mouse sin click
            self.clicked = False

        screen.blit(self.image, self.rect)

        return action


class Player:
    def __init__(self, x, y):
        self.reset(x, y)

    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 5  # Realentizar caminata

        if game_over == 0:
            # obtener tecla presionada
            key = pygame.key.get_pressed()
            # Salto
            if key[pygame.K_SPACE] and self.jumped == False and self.in_air == False:
                self.vel_y = -15
                self.jumped = True
            if key[pygame.K_SPACE] == False:
                self.jumped = False
            # Movimiento izquierda
            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            # Movimiento derecha
            if key[pygame.K_RIGHT]:
                dx += 5
                self.counter += 1
                self.direction = 1
            # Parar animacion
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # Animaciones de movimiento derecha
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # Gravedad de salto
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            # Deteccion de Colision
            self.in_air = True

            for tile in world.tile_list:
                # Colision horizontal
                if tile[1].colliderect(
                    self.rect.x + dx, self.rect.y, self.width, self.height
                ):
                    dx = 0
                # Colision vertical
                if tile[1].colliderect(
                    self.rect.x, self.rect.y + dy, self.width, self.height
                ):
                    # Chequear si esta debajo de bloque
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    # Chequear si esta encima de bloque
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False  # Salto solo posible encima de bloque

            # Deteccion colision con enemigos
            if pygame.sprite.spritecollide(self, blob_group, False):
                game_over = -1
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
            #Colision con Puerta Salida
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1


            # Actualizar posicion de personaje
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            if self.rect.y > 200:
                self.rect.y -= 5

        # Establecer personaje en pantalla
        screen.blit(self.image, self.rect)

        return game_over

    def reset(self, x, y):
        # Valores iniciales de juego
        self.images_right = []  # Array movimiento de derecha
        self.images_left = []  # Array movimiento de izquierda

        self.index = 0
        self.counter = 0
        # Obtener imagenes personaje
        for num in range(1, 5):
            img_right = pygame.image.load(f"./img/guy{num}.png")
            img_right = pygame.transform.scale(img_right, (30, 60))
            img_left = pygame.transform.flip(img_right, True, False)  # Invertir imagen
            self.images_right.append(img_right)  # Añadir imagen a array
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load("./img/ghost.png")
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True


class World:
    def __init__(self, data):
        self.tile_list = []
        # Establecer bordes de tierra y pasto en screen
        dirt_img = pygame.image.load("./img/dirt.png")
        grass_img = pygame.image.load("./img/grass.png")

        row_count = 0  # Recorrer grilla
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:  # Tierra
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:  # Pasto
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:  # Enemigos
                    blob = Enemy(col_count * tile_size, row_count * tile_size + 5)
                    blob_group.add(blob)  # Agregar enemigo a lista de enemigos
                if tile == 6:
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img_blob = pygame.image.load("./img/blob.png")
        self.image = pygame.transform.scale(img_blob, (tile_size, tile_size))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 30:
            self.move_direction *= -1
            self.move_counter *= -1


class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img_lava = pygame.image.load("./img/lava.png")
        self.image = pygame.transform.scale(img_lava, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img_exit = pygame.image.load("./img/exit.png")
        self.image = pygame.transform.scale(img_exit, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# Posicionar elementos
player = Player(100, screen_height - 130)
blob_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()


#Cargar niveles 
if path.exists(f'level{level}_data'):
    pickle_in = open(f'level{level}_data', 'rb')
    world_data = pickle.load(pickle_in)
world = World(world_data)

# botones
restart_button = Button(screen_width // 2 - 50, screen_height // 2 + 100, restart_img)
start_button = Button(screen_width // 2 - 250, screen_height // 2 - 50, start_img)
exit_button = Button(screen_width // 2 + 50, screen_height // 2 - 50, exit_img)


# Mantener abierta la pantalla
run = True
while run:
    # Actualizar pantalla
    clock.tick(fps)

    screen.blit(bg_img, (0, 0))
    screen.blit(sun_img, (100, 100))

    if main_menu == True:
        if exit_button.draw():
            run = False
        if start_button.draw():
            main_menu = False
    else:
        world.draw()
        #Nivel inicial
        if game_over == 0:  
            blob_group.update()

        blob_group.draw(screen)
        lava_group.draw(screen)
        exit_group.draw(screen)

        game_over = player.update(game_over)

        # Reseteo de nivel por game over
        if game_over == -1:
            if restart_button.draw():
                world_data = []
                world = reset_level(level)
                game_over = 0

        #Siguiente nivel
        if game_over == 1: 
            level += 1
            if level <= max_levels:
                print(f"nivel{level}")
                #Resetar para nuevo nivel
                world_data = []
                world = reset_level(level)
                game_over = 0
            else:
                #resetear juego
                print("juego termiando")
                if restart_button.draw():
                    level = 1
                    world_data = []
                    world = reset_level(level)
                    game_over = 0


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()
pygame.quit() #Cerrar juego
