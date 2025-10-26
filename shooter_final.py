from pygame import *
from random import randint
from time import time as timer  # import the timing function so that the interpreter doesn’t need to look for this function in the pygame module time, give it a different name ourselves
import math
# loading font functions separately
font.init()
font1 = font.SysFont('impact',67)
font2 = font.SysFont('courier',40)

font3 = font.SysFont('impact',150)

win = font3.render('YOU WIN!', True, (255, 190, 20))
lose = font3.render('YOU LOSE!', True, (180, 0, 0))

my_path = ''
# backgournd music
mixer.init()
mixer.music.load('Mando.ogg')
mixer.music.set_volume(0.5)  # set the volume to 20%
mixer.music.play()
fire_sound = mixer.Sound('fire.ogg')
bomb_sound = mixer.Sound('bomb.ogg')

# we need the following images:
img_back = "galaxy.jpg"  # game background
img_bullet = "bullet.png"  # bullet
img_hero = "rocket.png"  # hero
img_enemy = "ufo.png"  # enemy
img_ast = "asteroid.png"  # asteroid
img_bomb = "bomb.png"
img_explosion = "explosion.png"

score = 0  # ships destroyed
goal = 67  # how many ships need to be shot down to win
lost = 0  # ships missed
max_lost = 30  # lose if you miss that many
life = 10  # life points

# parent class for other sprites
class GameSprite(sprite.Sprite):
    # class constructor
    def __init__(self, player_image, player_x, player_y, size_x, size_y, player_speed):
        # Call for the class (Sprite) constructor:
        sprite.Sprite.__init__(self)

        # every sprite must store the image property
        self.image = transform.scale(image.load(player_image), (size_x, size_y))
        self.speed = player_speed

        # every sprite must have the rect property – the rectangle it is fitted in
        self.rect = self.image.get_rect()
        self.rect.x = player_x
        self.rect.y = player_y

    # method drawing the character on the window
    def reset(self):
        window.blit(self.image, (self.rect.x, self.rect.y))

# main player class
class Player(GameSprite):
    # method to control the sprite with arrow keys
    def update(self):
        keys = key.get_pressed()
        if keys[K_a] and self.rect.x > 5 or keys[K_LEFT] and self.rect.x > 5:
            self.rect.x -= self.speed
        if keys[K_d] and self.rect.x < win_width - 80 or keys[K_RIGHT] and self.rect.x < win_width - 80:
            self.rect.x += self.speed

    # method to "shoot" (use the player position to create a bullet there)
    def fire(self):
        bullet = Bullet(img_bullet, self.rect.centerx, self.rect.top, 15, 20, -15)
        bullets.add(bullet)

# enemy sprite class
class Enemy(GameSprite):
    # enemy movement
    def update(self):
        self.rect.y += self.speed
        global lost
        # disappears upon reaching the screen edge
        if self.rect.y > win_height:
            self.rect.x = randint(80, win_width - 80)
            self.rect.y = 0
            lost = lost + 1

# bullet sprite class
class Bullet(GameSprite):
    # enemy movement
    def update(self):
        self.rect.y += self.speed
        # disappears upon reaching the screen edge
        if self.rect.y < 0:
            self.kill()

        # Check collision with bombs
        for bomb in bombs:
            if sprite.collide_rect(self, bomb):
                bomb.explode()
                self.kill()

# Bomb class
class Bomb(GameSprite):
    def __init__(self, player_image, player_x, player_y, size_x, size_y, player_speed):
        GameSprite.__init__(self, player_image, player_x, player_y, size_x, size_y, player_speed)
        self.exploded = False
    # exploded = False
    
    def update(self):
        if not self.exploded:
            self.rect.y += self.speed
            if self.rect.y > win_height:
                self.kill()
    
    def explode(self):
#        self.image = transform.scale(image.load(img_explosion), (80, 80))
        bomb_sound.play()
        self.exploded = True
        self.kill_enemies()
        self.kill()
        
    def kill_enemies(self):
        constraints = [monsters, asteroids, ship]
        for someting in constraints:
            for p in someting:
                # distance1 = math.hypot(enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery)
                # distance2 = math.hypot(asteroid.rect.centerx - self.rect.centerx, asteroid.rect.centery - self.rect.centery)
                distance = math.hypot(p.rect.centerx - self.rect.centerx, p.rect.centery - self.rect.centery)
                if distance <= 100:  
                    # enemy.kill()
                    # ast.kill()
                    p.kill()


# Create a window
win_width = 1000
win_height = 700
display.set_caption("Shooter")
window = display.set_mode((win_width, win_height))
background = transform.scale(image.load(img_back), (win_width, win_height))
# create sprites
ship = Player(img_hero, 5, win_height - 100, 80, 100, 20)

# creating a group of enemy sprites
monsters = sprite.Group()
for i in range(1, 6):
    monster = Enemy(img_enemy, randint(80, win_width - 80), -40, 80, 50, randint(1, 5))
    monsters.add(monster)

# creating a group of asteroid sprites ()
asteroids = sprite.Group()
for i in range(1, 3):
    asteroid = Enemy(img_ast, randint(30, win_width - 30), -40, 80, 50, randint(1, 7))
    asteroids.add(asteroid) 

bullets = sprite.Group()

bombs = sprite.Group()
for i in range(3):
    bomb = Bomb(img_bomb, randint(80, win_width - 80), -40, 50, 50, randint(2, 4))
    bombs.add(bomb)

# the "game is over" variable: as soon as True is there, sprites stop working in the main loop
finish = False
# Main game loop:
run = True  # the flag is reset by the window close button

rel_time = False  # flag in charge of reload

num_fire = 10  # variable to count shots

while run:
    # "Close" button press event
    for e in event.get():
        if e.type == QUIT:
            run = False
        # space bar press event – the sprite shoots
        elif e.type == KEYDOWN:
            if e.key == K_SPACE:
                # check how many shots have been fired and whether reload is in progress
                if num_fire > 0 and rel_time == False:
                    num_fire = num_fire - 1 # num_fire += 1
                    fire_sound.play()
                    ship.fire()

                if num_fire <= 0 and rel_time == False:  # if the player fired 5 shots
                    last_time = timer()  # record time when this happened
                    rel_time = True  # set the reload flag

    # the game itself: actions of sprites, checking the rules of the game, redrawing
    if not finish:
 
        # update the background
        window.blit(background, (0, 0))

        # launch sprite movements
        ship.update()
        monsters.update()
        
        asteroids.update()

        bullets.update()
        bombs.update()

        # update them in a new location in each loop iteration
        ship.reset()
        monsters.draw(window)
        asteroids.draw(window)
        bullets.draw(window)
        bombs.draw(window)

        # reload
        if rel_time == True:
            now_time = timer()  # read time

            if now_time - last_time < 2:  # before 3 seconds are over, display reload message
                reload = font1.render('Wait, reload...', 1, (255, 196, 0))
                window.blit(reload, (350, 300))
            else:
                num_fire = 10  # set the bullets counter to zero
                rel_time = False  # reset the reload flag

        # check for a collision between a bullet and monsters (both monster and bullet disappear upon a touch)
        collides = sprite.groupcollide(monsters, bullets, True, True)
        for c in collides:
            # this loop will repeat as many times as the number of monsters hit
            score = score + 1
            monster = Enemy(img_enemy, randint(80, win_width - 80), -40, 80, 50, randint(4, 7))
            monsters.add(monster)

        collides2 = sprite.groupcollide(asteroids, bullets, True, True)
        for d in collides2:
            # this loop will repeat as many times as the number of monsters hit
            score = score + 1
            asteroid = Enemy(img_ast, randint(80, win_width - 80), -40, 80, 50, randint(3, 6))
            asteroids.add(asteroid)
        if sprite.spritecollide(ship, monsters, True) or sprite.spritecollide(ship, asteroids, True):
            life = life - 1

        if sprite.spritecollide(ship, bombs, True):
            life = life - 5

        # losing
        if life == 0 or lost >= max_lost:
            finish = True  # lose, set the background and no longer control the sprites.
            window.blit(lose, (250, 300))

        # win checking: how many points scored?
        if score >= goal:
            finish = True
            window.blit(win, (250, 300))

        # write text on the screen
        text = font2.render("Score: " + str(score), 1, (255, 255, 255))
        window.blit(text, (10, 10))

        text_lose = font2.render("Missed: " + str(lost), 1, (255, 255, 255))
        window.blit(text_lose, (10, 50))

        current_ammo = font2.render("Ammo: " + str(num_fire), 1, (255, 255, 255))
        window.blit(current_ammo, (10, 90))

        # set a different color depending on the number of lives
        if life == 10:
            life_color = (0, 200, 0)
        if life == 5:
            life_color = (150, 150, 0)
        if life == 2:
            life_color = (150, 0, 0)

        text_life = font1.render('Life: ' + str(life), 1, life_color)
        window.blit(text_life, (790, 10))

        display.update()

    # bonus: automatic restart of the game
    # else:
    #     finish = False
    #     score = 0
    #     lost = 0
    #     num_fire = 0
    #     life = 10
    #     for b in bullets:
    #         b.kill()
    #     for m in monsters:
    #         m.kill()
    #     for a in asteroids:
    #         a.kill()

    time.delay(50)
