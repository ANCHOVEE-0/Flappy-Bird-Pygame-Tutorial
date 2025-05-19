import pygame, sys, os, random, json
from pygame.locals import *

# initialize pygame
pygame.init()

# clock
FPS = 60
clock = pygame.time.Clock()

# get screen dimensions/aspect ratios
display_info = pygame.display.Info()
display_width = display_info.current_w
display_height = display_info.current_h
aspect_ratio = display_width / display_height

# internal game resolution: display is the "inside" - everything is rendered onto the display, and the display is resized to the size of the pygame window, also resizing everything rendered on it by the same ratios.
display_mode = (int(aspect_ratio * 196), 196)
display = pygame.Surface(display_mode)

# actual pygame window
screen_mode = (int(aspect_ratio * display_height / 2), int(display_height / 2))
screen = pygame.display.set_mode(screen_mode, pygame.RESIZABLE)

# load images from directories
bird_image = pygame.image.load("sprites/bird.png").convert_alpha()
bird_image.set_colorkey((0,0,0))
obstacle_image = pygame.image.load('sprites/obstacle.png').convert_alpha()
obstacle_image.set_colorkey((0,0,0))  # This removes black

# extras - icon and window name
pygame.display.set_icon(bird_image)
pygame.display.set_caption('FLAPPY BIRD')

def check_collision(obj1, obj2):
    return obj1.get_rect().colliderect(obj2.get_rect())

# Player
class Player:
    def __init__(self, game, x, y, width, height):
        self.game = game
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # image
        self.image = bird_image

        # other game variables
        self.downwards = 0
        self.upwards = -3
        self.jumped = False

    def jump(self):
        self.downwards = 0

    def apply_gravity(self):
        self.downwards += 0.2
        # terminal velocity
        self.y += min(self.downwards + self.upwards, 5)

    def movement(self):
        self.apply_gravity()
        
        # top and bottom borders
        self.y = min(display.get_height() - self.height, self.y)
        self.y = max(0, self.y)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def render(self):
        display.blit(self.image, (self.x, self.y))

    def update(self):
        self.movement() 

# obstacle class
class Obstacle:
    def __init__(self, game, x, y, size):
        self.game = game
        self.x = x
        self.y = y
        self.width = size
        self.height = size

        # image
        self.image = obstacle_image

    def movement(self):
        self.x -= 2

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def render(self):
        display.blit(self.image, (self.x, self.y))

    def update(self):
        self.movement()
        
# game class
class Game:
    def __init__(self):
        self.tile_size = 24

        # player and obstacles
        self.player = Player(self,display.get_width()/4,display.get_height()/2,12,12)
        self.obstacles = []
        self.last_time = pygame.time.get_ticks()
        
        # game state variables
        self.game_started = False
        self.game_over = False

        self.retrieve_highscore()

    # score and highscore load
    def retrieve_highscore(self):
        self.score = 0
        if not os.path.exists('highscore.json'):
            with open("highscore.json", "w") as json_file:
                json.dump({'highest': 0}, json_file)
        with open("highscore.json", "r") as f:
            self.loaded_data = json.load(f)
        self.highest_score = self.loaded_data['highest']

    def draw_text(self, text, size, color, center):
        font = pygame.font.Font(None, size)
        render_text = font.render(text, False, color) # False: disables anti-aliasing, sharper pixellated look.
        rect = render_text.get_rect(center=center)
        display.blit(render_text, rect)

    # keybinds
    def keybinds(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_SPACE:
                    if self.game_over == False:
                        self.player.jump()
            if event.type == KEYUP:
                if event.key == K_SPACE:
                    if self.game_started == False:
                        self.game_started = True
                if event.key == K_r:
                    if self.game_over:
                        self.__init__()

    # function to spawn one obstacle
    def spawn_obstacle(self, time):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_time >= time:
            self.score += 1
            random_height = random.randint(0, int(display.get_height() - self.tile_size))
            self.obstacles.append(Obstacle(self, display.get_width(), random_height, self.tile_size))
            self.last_time = current_time  # reset timer

    # obstacle handler 
    def handle_obstacles(self):
        #spawn obstacle every increment 
        self.spawn_obstacle(250)
        # remove obstacles when necessary
        for obstacle in self.obstacles:
            if obstacle.x < -100:
                self.obstacles.remove(obstacle)
        # handle collisions between player and obstacles
        for obstacle in self.obstacles:
            obstacle.update()
            if check_collision(obstacle, self.player):
                self.game_over = True

    # displaying texts
    def display_texts(self):
        self.draw_text("highscore: " + str(self.highest_score), 24, (0,150,255), (75, 15))
        self.draw_text("score: " + str(self.score), 24, (200,0,150), (display.get_width()-50, 15))
        if self.game_started == False:
            self.draw_text("press SPACE to fly", 24, (0,150,0), (display.get_width()/2, display.get_height()/2))

        if self.game_over:
            self.draw_text("GAME OVER", 24, (255,0,0), (display.get_width()/2, display.get_height()/2))
            self.draw_text("press R to retry", 24, (0,150,0), (display.get_width()/2, display.get_height()/2 + 20))

    # mainloop
    def update(self):
        display.fill((150, 200, 255))  # draw on display instead of screen: "reset all" every frame
        self.keybinds()

        # rendering all - separate these from update functions of both player and obstacle because of game over screen
        for obstacle in self.obstacles:
            obstacle.render()
        self.player.render()
        self.display_texts()

        # game state conditions
        if self.game_started:
            if self.game_over == False: # not game over (game started and running)
                self.handle_obstacles()
                self.player.update()
            if self.game_over == True: # game over (death)
                self.player.apply_gravity()
                if self.score > self.highest_score: # comparing highscore to current run's score, and updates if necessary
                    with open("highscore.json", "w") as f:
                        json.dump({"highest": self.score}, f)

# new game        
game = Game()
# game loop
while True:
    game.update()
    
    # scale and blit display onto screen
    scaled = pygame.transform.scale(display, screen.get_size())
    screen.blit(scaled, (0, 0))

    # display all, ticks.
    pygame.display.update()
    clock.tick(FPS)
