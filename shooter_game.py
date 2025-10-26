from pygame import *
from random import *
# from time import time as timer

win_width =  1000
win_height = 700
#Game scene:
window = display.set_mode((win_width, win_height))
display.set_caption('WLECOMA BAKC GESAHe!')
background = transform.scale(image.load('galaxy.jpg'), (win_width, win_height))

#music

mixer.init()
mixer.music.load('space.ogg')
mixer.music.set_volume(0.1)
mixer.music.play()
fire_sound = mixer.Sound('fire.ogg')
# money = mixer.Sound('money.ogg')
# kick = mixer.Sound('kick.ogg')

font.init()
font2 = font.SysFont('courier',40)

font3 = font.SysFont('impact',150)
score = 0 #ships hit
lost = 0 #ships missed
max_lost = 30
life = 3

win = font3.render('YOU WIN!', True,(255,255,255))
lose = font3.render('YOU LOSE!',True,(180,0,0))

player_speed = 10
player_x = 10
player_y = 10
goal = 30

class Game(sprite.Sprite):
    #class constructor
    def __init__(self, player_image, player_x, player_y, size_x, size_y, player_speed):
        super().__init__()
        #every sprite must store the image property
        self.image = transform.scale(image.load(player_image), (size_x, size_y))
        self.speed = player_speed

        #every sprite must have the rect property - the rectangle it is fitted in
        self.rect = self.image.get_rect()
        self.rect.x = player_x
        self.rect.y = player_y
    
    def draw(self):
        window.blit(self.image, (self.rect.x, self.rect.y))

#heir class for the player sprite (controlled by arrows)
class Player(Game):
    def update(self):
        keys = key.get_pressed()
        if keys[K_a] and self.rect.x > 5:
            self.rect.x -= self.speed
        if keys[K_d] and self.rect.x < win_width - 70:
            self.rect.x += self.speed
    def fire(self):
        bullet = Bullet('bullet.png',self.rect.centerx, self.rect.top,15,20,15)
        bullets.add(bullet)

# bullet sprite class
class Bullet(Game):
    # enemy movement
    def update(self):
        self.rect.y -= self.speed
        # disappears upon reaching the screen edge
        if self.rect.y <0:
            self.kill()

class Enemy(Game):
    #enemy movement
    def update(self):
        self.rect.y += self.speed
        global lost
        #disappears if it reaches the edge of the screen
        if self.rect.y > win_height:
            self.rect.x = randint(80, win_width - 80)
            self.rect.y = 0
            lost = lost + 1

hero = Player('rocket.png',10,win_height-100,80,100,15)
monsters = sprite.Group()
for i in range(1, 11):
    monster = Enemy('ufo.png', randint(80, win_width - 80),0,80,50, randint(10,25))
    monsters.add(monster)

monsters2 = sprite.Group()
for i in range(1, 11):
    monster2 = Enemy('asteroid.png', randint(80, win_width - 80),0,80,50, randint(10,25))
    monsters.add(monster2)


bullets = sprite.Group()

run = True
# clock = time.Clock()
FPS = 70
finish = False

while run:
    from time import *
    for e in event.get():
        if e.type == QUIT:
            run = False

        #dash
        if e.type == KEYDOWN:
            if e.key == K_SPACE:
                fire_sound.play()
                hero.fire()

    if not finish:
        window.blit(background,(0,0))
        hero.update()
        hero.draw()
        bullets.update()
        bullets.draw(window)
        #writing text on the screen
        text = font2.render('Score: ' + str(score), 1,(255,255,255))
        window.blit(text,(10,5))

        text_lose = font2.render('Missed: ' +str(lost),1,(255,255,255))
        window.blit(text_lose,(10,50))
        monsters.update()
        monsters.draw(window)
        collides = sprite.groupcollide(monsters,bullets,True,True)

        for c in collides:
            # this loop will repeat as many times as the number of monsters hit
            score = score +1
            monster = Enemy('ufo.png', randint(80, win_width - 80),0,80,50, randint(10,25))
            monsters.add(monster)
        if sprite.spritecollide(hero,monsters,False) or sprite.spritecollide(hero,monsters2,False):
            life = life - 1
        # losing
        if life == 0 or lost >= max_lost:
            finish = True
            window.blit(lose,(300,350))

        if score >= goal:
            finish = True
            window.blit(win,(300, 350))

        display.update()
    time.delay(500)
         
    
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak
#borak