from pygame import *
from random import randint, random, uniform
from time import time as timer
import math, os, sys

############################################
# --------------- Safe Init ---------------
############################################
init()
font.init()
# Some environments lack audio device; guard mixer.init
has_audio = True
try:
    mixer.init()
except Exception:
    has_audio = False

############################################
# ---------------- Settings ---------------
############################################
WIN_WIDTH, WIN_HEIGHT, FPS = 1000, 600, 60

# Player
PLAYER_SPEED = 8
PLAYER_SIZE = (80, 100)
PLAYER_LIVES = 10
PLAYER_FIRE_COOLDOWN_BASE = 0.18
CHARGE_THRESHOLD = 2.0
CHARGED_PIERCE = 5
CHARGED_SIZE = (120, 160)
CHARGED_SPEED = -22

# Multishot tuning
SPREAD_VX = 4.0
CHARGED_SPREAD_VX = 3.0
SHOT_X_OFFSET = 12

# Enemies
ENEMY_SIZE = (80, 50)
ASTEROID_SIZE = (80, 50)
ENEMY_MIN_SPEED = 2
ENEMY_MAX_SPEED = 6
ENEMY_FIRE_CHANCE = 0.004
ENEMY_FIRE_COOLDOWN = 1.2

# Bullets
BULLET_SIZE = (15, 20)
BULLET_SPEED = -16
BULLET_DAMAGE = 1
ENEMY_BULLET_SIZE = (10, 16)
ENEMY_BULLET_SPEED = 10
ENEMY_BULLET_DAMAGE = 1

# Boss
BOSS_SIZE = (260, 170)
BOSS_HP = 150
BOSS_SPEED_X = 5
BOSS_SPEED_Y = 2
BOSS_FIRE_COOLDOWN = 2
BOSS_SPREAD = 3

# Levels
LEVELS = {
    1: { 'goal': 20, 'monsters': 6, 'asteroids': 2, 'enemy_fire': True },
    2: { 'goal': 60, 'monsters': 9, 'asteroids': 3, 'enemy_fire': True },
    3: { 'goal': 3, 'monsters': 0, 'asteroids': 0, 'enemy_fire': False }, # Boss level
}

# Power-ups
POWERUP_SIZE = (40, 40)
POWERUP_SPAWN_CHANCE = 0.008
RAPID_FIRE_FACTOR = 0.45
RAPID_FIRE_DURATION = 10.0
SHIELD_DURATION = 6.0

############################################
# -------------- Asset Paths --------------
############################################
ABS_BASE = 'C:/Data Scientist/Algonova/Courses/Python Start II/Modul 5/Shooter/M5L5-M5L8 Shooter/'
def first_existing(*paths):
    for p in paths:
        if p and os.path.exists(p): return p
    return None

img_back_fp   = first_existing(os.path.join(ABS_BASE,'galaxy.jpg'), 'galaxy.jpg')
img_bullet_fp = first_existing(os.path.join(ABS_BASE,'bullet2.png'), 'bullet2.png')
img_hero_fp   = first_existing(os.path.join(ABS_BASE,'rocket.png'), 'rocket.png')
img_enemy_fp  = first_existing(os.path.join(ABS_BASE,'ufo.png'), 'ufo.png')
img_ast_fp    = first_existing(os.path.join(ABS_BASE,'asteroid.png'), 'asteroid.png')
img_bomb_fp   = first_existing(os.path.join(ABS_BASE,'bomb.png'), 'bomb.png')
img_expl_fp   = first_existing(os.path.join(ABS_BASE,'explosion.png'), 'explosion.png')
img_boss_fp   = first_existing(os.path.join(ABS_BASE,'boss.gif'), 'boss.gif')

music_path    = first_existing(os.path.join(ABS_BASE,'Mando.ogg'), 'Mando.ogg')
fire_sfx_path = first_existing(os.path.join(ABS_BASE,'fire.ogg'), 'fire.ogg')
bomb_sfx_path = first_existing(os.path.join(ABS_BASE,'bomb.ogg'), 'bomb.ogg')
charged_cue_path = first_existing(os.path.join(ABS_BASE,'charged.ogg'), 'charged.ogg')

def safe_load_image(fp, size=None, fallback_color=(180,180,180), shape='rect'):
    # Returns a Surface (scaled) even if file missing; draws placeholder.
    if fp and os.path.exists(fp):
        try:
            surf = image.load(fp).convert_alpha()
            if size: surf = transform.scale(surf, size)
            return surf
        except Exception:
            pass
    # placeholder
    w, h = size if size else (60, 40)
    surf = Surface((w, h), SRCALPHA)
    if shape == 'circle':
        draw.circle(surf, fallback_color, (w//2, h//2), min(w,h)//2)
    elif shape == 'ellipse':
        draw.ellipse(surf, fallback_color, (0,0,w,h))
    else:
        surf.fill(fallback_color)
    # add an X
    draw.line(surf, (40,40,40), (0,0), (w,h), 2)
    draw.line(surf, (40,40,40), (0,h), (w,0), 2)
    return surf

############################################
# --------------- Window ------------------
############################################
screen = display.set_mode((WIN_WIDTH, WIN_HEIGHT))
display.set_caption('Shooter — Final')
clock = time.Clock()

font_big = font.SysFont('impact', 200)
font_mid = font.SysFont('impact', 50)
font_sm  = font.SysFont('impact', 50)

win_txt  = font_big.render('YOU WIN!', True, (255,255,255))
lose_txt = font_big.render('YOU LOSE!', True, (180,0,0))

# Music / SFX (safe)
def load_sound_safe(path):
    if not has_audio or not path or not os.path.exists(path): return None
    try: return mixer.Sound(path)
    except Exception: return None

if has_audio and music_path:
    try:
        mixer.music.load(music_path)
        mixer.music.set_volume(0.45)
        mixer.music.play(-1)
    except Exception:
        pass

fire_sound = load_sound_safe(fire_sfx_path)
bomb_sound = load_sound_safe(bomb_sfx_path)
charged_sound = load_sound_safe(charged_cue_path)

background = safe_load_image(img_back_fp, (WIN_WIDTH, WIN_HEIGHT))

############################################
# --------------- Sprites -----------------
############################################
class GameSprite(sprite.Sprite):
    def __init__(self, surf, x, y, speed=0):
        super().__init__()
        self.image = surf
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.speed = speed
    def reset(self, into=screen):
        into.blit(self.image, self.rect)

class Player(GameSprite):
    def __init__(self, x, y):
        super().__init__(safe_load_image(img_hero_fp, size=PLAYER_SIZE, fallback_color=(120,200,255)), x, y, PLAYER_SPEED)
        self.last_shot = 0.0
        self.charging = False
        self.charge_t0 = 0.0
        self.charge_cued = False
        self.rapid_until = 0.0
        self.shield_until = 0.0
    def update(self):
        keys = key.get_pressed()
        if keys[K_a] and self.rect.x > 5: self.rect.x -= self.speed
        if keys[K_d] and self.rect.x < WIN_WIDTH - self.rect.width - 5: self.rect.x += self.speed
        if self.charging:
            elapsed = timer() - self.charge_t0
            if not self.charge_cued and elapsed >= CHARGE_THRESHOLD:
                self.charge_cued = True
                if charged_sound: charged_sound.play()
                # auto-fire charged shot
                for vx, dx in self._dirs_for_level(True):
                    bsurf = safe_load_image(img_bullet_fp, CHARGED_SIZE, (255,240,120))
                    b = Bullet(bsurf, self.rect.centerx - CHARGED_SIZE[0]//2 + dx, self.rect.top - CHARGED_SIZE[1],
                               vy=CHARGED_SPEED, vx=vx*0.6, damage=3, pierce=CHARGED_PIERCE, charged=True)
                    bullets.add(b)
                self.last_shot = timer()
                if fire_sound: fire_sound.play()
    def current_cooldown(self):
        cd = PLAYER_FIRE_COOLDOWN_BASE
        if timer() < self.rapid_until: cd *= RAPID_FIRE_FACTOR
        return cd
    def can_fire(self): return (timer() - self.last_shot) >= self.current_cooldown()
    def _dirs_for_level(self, charged=False):
        if level >= 3:
            vx = CHARGED_SPREAD_VX if charged else SPREAD_VX
            return [(-vx, -SHOT_X_OFFSET), (0.0, 0), (vx, SHOT_X_OFFSET)]
        elif level >= 2:
            vx = CHARGED_SPREAD_VX if charged else SPREAD_VX
            return [(-vx, -SHOT_X_OFFSET), (vx, SHOT_X_OFFSET)]
        else:
            return [(0.0, 0)]
    def tap_fire(self):
        if not self.can_fire(): return
        self.last_shot = timer()
        for vx, dx in self._dirs_for_level(False):
            bsurf = safe_load_image(img_bullet_fp, BULLET_SIZE, (255,255,255))
            b = Bullet(bsurf, self.rect.centerx-7+dx, self.rect.top-18, vy=BULLET_SPEED, vx=vx, damage=BULLET_DAMAGE)
            bullets.add(b)
        if fire_sound: fire_sound.play()
    def start_charge(self):
        if not self.charging:
            self.charging = True; self.charge_t0 = timer(); self.charge_cued = False
    def release_charge(self):
        # In auto-fire mode, release does NOT fire if threshold already hit.
        if not self.charging: return
        hold = timer() - self.charge_t0
        fired = False
        if hold >= CHARGE_THRESHOLD:
            fired = True
        self.charging = False
        if not fired:
            self.tap_fire()
    def has_shield(self): return timer() < self.shield_until

class Enemy(GameSprite):
    def __init__(self, x, y, speed):
        super().__init__(safe_load_image(img_enemy_fp, ENEMY_SIZE, (255,120,120)), x, y, speed)
        self.hp = 1; self.last_fire = 0.0
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > WIN_HEIGHT:
            self.rect.x = randint(80, WIN_WIDTH-80)
            self.rect.y = -self.rect.height
            global lost; lost += 1
        if current_level_data.get('enemy_fire', False):
            if (timer() - self.last_fire) > ENEMY_FIRE_COOLDOWN and random() < ENEMY_FIRE_CHANCE:
                self.last_fire = timer(); self.shoot()
    def shoot(self):
        ex = self.rect.centerx - ENEMY_BULLET_SIZE[0]//2; ey = self.rect.bottom
        bsurf = safe_load_image(img_bullet_fp, ENEMY_BULLET_SIZE, (255,180,180))
        enemy_bullets.add(EnemyBullet(bsurf, ex, ey, ENEMY_BULLET_SPEED, ENEMY_BULLET_DAMAGE))

class Asteroid(Enemy):
    def __init__(self, x, y, speed):
        GameSprite.__init__(self, safe_load_image(img_ast_fp, ASTEROID_SIZE, (180,180,220)), x, y, speed)
        self.hp = 1; self.last_fire = 0.0
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > WIN_HEIGHT:
            self.rect.x = randint(30, WIN_WIDTH-30); self.rect.y = -self.rect.height; global lost; lost += 1

class Bullet(GameSprite):
    def __init__(self, surf, x, y, vy, vx=0.0, damage=1, pierce=1, charged=False):
        super().__init__(surf, x, y, 0)
        self.vx, self.vy, self.damage, self.pierce, self.charged = vx, vy, damage, pierce, charged
        self._shake_phase = 0.0
    def update(self):
        self.rect.x += self.vx; self.rect.y += self.vy
        if self.rect.bottom < 0 or self.rect.right < -40 or self.rect.left > WIN_WIDTH+40:
            self.kill(); return
        if self.charged:
            self._shake_phase += 0.35
            self.rect.x += int(2*math.sin(self._shake_phase))

class EnemyBullet(sprite.Sprite):
    def __init__(self, surf, x, y, vy, damage):
        super().__init__()
        self.image = surf
        self.rect = self.image.get_rect(topleft=(x,y))
        self.vy = vy; self.damage = damage
    def update(self):
        self.rect.y += self.vy
        if self.rect.top > WIN_HEIGHT: self.kill()

class EnemyBulletVector(EnemyBullet):
    def __init__(self, x, y, vx, vy, damage):
        bsurf = safe_load_image(img_bullet_fp, ENEMY_BULLET_SIZE, (255,180,180))
        super().__init__(bsurf, x, y, 0, damage); self.vx, self.vy = vx, vy
    def update(self):
        self.rect.x += self.vx; self.rect.y += self.vy
        if self.rect.top > WIN_HEIGHT or self.rect.bottom < -40 or self.rect.right < -40 or self.rect.left > WIN_WIDTH+40:
            self.kill()

class Bomb(GameSprite):
    def __init__(self, x, y, speed):
        super().__init__(safe_load_image(img_bomb_fp, (50,50), (220,220,120)), x, y, speed)
        self.exploded = False
    def update(self):
        if not self.exploded:
            self.rect.y += self.speed
            if self.rect.top > WIN_HEIGHT: self.kill()
    def explode(self):
        self.image = safe_load_image(img_expl_fp, (90,90), (255,200,160))
        if bomb_sound: bomb_sound.play()
        self.exploded = True; self.kill_enemies(); self.kill()
    def kill_enemies(self):
        for group in (monsters, asteroids):
            for p in group.sprites():
                d = math.hypot(p.rect.centerx - self.rect.centerx, p.rect.centery - self.rect.centery)
                if d <= 110: p.kill()

class Boss(sprite.Sprite):
    def __init__(self):
        super().__init__()
        if img_boss_fp:
            try:
                surf = transform.scale(image.load(img_boss_fp).convert_alpha(), BOSS_SIZE)
            except Exception:
                surf = None
        else:
            surf = None
        if surf is None:
            surf = Surface(BOSS_SIZE, SRCALPHA)
            draw.ellipse(surf, (180, 60, 200), surf.get_rect())
            draw.circle(surf, (255,255,255), (int(BOSS_SIZE[0]*0.35), int(BOSS_SIZE[1]*0.45)), 16)
            draw.circle(surf, (255,255,255), (int(BOSS_SIZE[0]*0.65), int(BOSS_SIZE[1]*0.45)), 16)
            draw.circle(surf, (20,20,40), (int(BOSS_SIZE[0]*0.35), int(BOSS_SIZE[1]*0.45)), 8)
            draw.circle(surf, (20,20,40), (int(BOSS_SIZE[0]*0.65), int(BOSS_SIZE[1]*0.45)), 8)
            points = [(BOSS_SIZE[0]//2 - 40, 10), (BOSS_SIZE[0]//2, -10), (BOSS_SIZE[0]//2 + 40, 10)]
            draw.polygon(surf, (255, 230, 90), points)
            for r in range(4):
                draw.ellipse(surf, (200, 80, 230, 40 - r*8), surf.get_rect().inflate(r*14, r*10), width=6)
        self.image = surf
        self.rect = self.image.get_rect()
        self.rect.centerx = WIN_WIDTH//2; self.rect.y = -BOSS_SIZE[1]
        self.hp = BOSS_HP; self.vx = BOSS_SPEED_X; self.vy = BOSS_SPEED_Y
        self.last_fire = 0.0; self.entered = False
    def update(self):
        if not self.entered:
            self.rect.y += 3
            if self.rect.top >= 20: self.entered = True
            return
        self.rect.x += self.vx; self.rect.y += self.vy
        if self.rect.left <= 10 or self.rect.right >= WIN_WIDTH-10: self.vx *= -1
        if self.rect.top <= 20 or self.rect.bottom >= WIN_HEIGHT//2: self.vy *= -1
        if (timer() - self.last_fire) >= BOSS_FIRE_COOLDOWN:
            self.last_fire = timer(); self.fire_volley()
    def fire_volley(self):
        aim_at_player(self.rect.centerx, self.rect.bottom, speed=1, spread=0)
        for i in range(1, BOSS_SPREAD+1):
            aim_at_player(self.rect.centerx, self.rect.bottom, speed=1 + i, spread= 0.1*i)
            aim_at_player(self.rect.centerx, self.rect.bottom, speed=1 + i, spread=-0.1*i)

############################################
# -------------- Particles & PU -----------
############################################
class Particle(sprite.Sprite):
    def __init__(self, x, y, angle, speed, life, size, color):
        super().__init__()
        self.image = Surface((size,size), SRCALPHA)
        draw.circle(self.image, color, (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=(x,y))
        self.vx, self.vy = math.cos(angle)*speed, math.sin(angle)*speed
        self.life = life; self.max_life = life
    def update(self):
        self.rect.x += self.vx; self.rect.y += self.vy; self.vy += 0.1
        self.life -= 1
        if self.life <= 0: self.kill(); return
        self.image.set_alpha(int(255*(self.life/self.max_life)))

def spawn_explosion(x, y, charged=False):
    count = 36 if charged else 18
    speed_min, speed_max = (2.5, 6.0) if charged else (1.5, 4.0)
    size_min, size_max = (6, 14) if charged else (4, 9)
    for _ in range(count):
        ang = uniform(0, math.tau); spd = uniform(speed_min, speed_max)
        life = randint(20, 40); size = randint(size_min, size_max)
        color = (randint(180,255), randint(120,200), randint(40,140)) if charged else (randint(180,240), randint(180,240), randint(180,240))
        particles.add(Particle(x, y, ang, spd, life, size, color))

POWERUP_TYPES = ('shield','rapid')
class PowerUp(sprite.Sprite):
    def __init__(self, kind, x, y):
        super().__init__()
        self.kind = kind
        self.image = Surface(POWERUP_SIZE, SRCALPHA)
        if kind == 'shield':
            draw.circle(self.image, (120,220,255), (POWERUP_SIZE[0]//2, POWERUP_SIZE[1]//2), POWERUP_SIZE[0]//2)
            draw.circle(self.image, (255,255,255), (POWERUP_SIZE[0]//2, POWERUP_SIZE[1]//2), POWERUP_SIZE[0]//2-6, width=3)
        else:
            draw.rect(self.image, (255,210,90), (6,6,POWERUP_SIZE[0]-12, POWERUP_SIZE[1]-12), border_radius=7)
            draw.polygon(self.image, (255,255,255), [(12, POWERUP_SIZE[1]//2), (POWERUP_SIZE[0]-12, POWERUP_SIZE[1]//2 - 10), (POWERUP_SIZE[0]-12, POWERUP_SIZE[1]//2 + 10)])
        self.rect = self.image.get_rect(center=(x,y)); self.vy = 3
    def update(self):
        self.rect.y += self.vy
        if self.rect.top > WIN_HEIGHT: self.kill()

############################################
# -------------- Utilities ----------------
############################################
def aim_at_player(x, y, speed=12, spread=0.0):
    dx, dy = (ship.rect.centerx - x), (ship.rect.centery - y)
    ang = math.atan2(dy, dx) + spread
    vx, vy = math.cos(ang)*speed, math.sin(ang)*speed
    enemy_bullets.add(EnemyBulletVector(x, y, vx, vy, ENEMY_BULLET_DAMAGE))

def draw_text_center(surf, text_surface, y):
    x = (WIN_WIDTH - text_surface.get_width()) // 2; surf.blit(text_surface, (x, y))

def draw_hud():
    s1 = font_sm.render(f"Score: {score}", True, (255,255,255))
    s2 = font_sm.render(f"Missed: {lost}", True, (255,255,255))
    s3 = font_sm.render(f"Level: {level}", True, (200,220,255))
    screen.blit(s1,(10,10)); screen.blit(s2,(10,36)); screen.blit(s3,(10,62))
    c = (0,200,0) if life>=7 else ((200,180,0) if life>=3 else (200,40,40))
    screen.blit(font_mid.render(str(life), True, c), (WIN_WIDTH-70,6))
    tnow = timer()
    if ship.has_shield(): screen.blit(font_sm.render("Shield", True, (150,220,255)), (WIN_WIDTH-160,60))
    if tnow < ship.rapid_until: screen.blit(font_sm.render("Rapid", True, (255,230,120)), (WIN_WIDTH-160,86))

def draw_boss_hp(boss):
    bar_w, bar_h, x, y = 600, 18, (WIN_WIDTH-600)//2, 12
    draw.rect(screen, (100,100,100), (x,y,bar_w,bar_h), border_radius=6)
    t = max(0.0, min(1.0, boss.hp/BOSS_HP))
    draw.rect(screen, (255,120,120), (x+2,y+2,int((bar_w-4)*t),bar_h-4), border_radius=6)

############################################
# --------------- Game Setup --------------
############################################
screen.fill((10,10,30))
screen.blit(background, (0,0)); display.flip()

score, lost, life = 0, 0, PLAYER_LIVES
level = 1; current_level_data = LEVELS[level]; goal = current_level_data['goal']

ship = Player(5, WIN_HEIGHT - 120)

monsters = sprite.Group(); asteroids = sprite.Group(); bullets = sprite.Group(); enemy_bullets = sprite.Group()
bombs = sprite.Group(); boss_group = sprite.Group(); particles = sprite.Group(); powerups = sprite.Group()

def spawn_level_content(lvl):
    monsters.empty(); asteroids.empty(); bombs.empty()
    data = LEVELS[lvl]
    for _ in range(data['monsters']):
        monsters.add(Enemy(randint(80, WIN_WIDTH-80), randint(-300, -60), randint(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED)))
    for _ in range(data['asteroids']):
        asteroids.add(Asteroid(randint(30, WIN_WIDTH-30), randint(-300, -60), randint(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED+1)))
    for _ in range(3):
        bombs.add(Bomb(randint(80, WIN_WIDTH-80), randint(-600, -40), randint(2, 4)))

spawn_level_content(level)

class EnemyBullet(sprite.Sprite):
    def __init__(self, surf, x, y, vy, damage):
        super().__init__(); self.image = surf
        self.rect = self.image.get_rect(topleft=(x,y)); self.vy = vy; self.damage = damage
    def update(self):
        self.rect.y += self.vy
        if self.rect.top > WIN_HEIGHT: self.kill()

class EnemyBulletVector(EnemyBullet):
    def __init__(self, x, y, vx, vy, damage):
        super().__init__(safe_load_image(img_bullet_fp, ENEMY_BULLET_SIZE, (255,180,180)), x, y, 0, damage)
        self.vx, self.vy = vx, vy
    def update(self):
        self.rect.x += self.vx; self.rect.y += self.vy
        if self.rect.top > WIN_HEIGHT or self.rect.bottom < -40 or self.rect.right < -40 or self.rect.left > WIN_WIDTH+40:
            self.kill()

############################################
# ----------------- Loop ------------------
############################################
display.set_caption('Shooter — v4 FIX (Auto-fire)')
clock = time.Clock()
finish = False; show_end_banner = False; end_banner_time = 0.0

running = True
while running:
    dt_ms = clock.tick(FPS)
    for e in event.get():
        if e.type == QUIT: running = False
        elif e.type == KEYDOWN:
            if e.key == K_ESCAPE: running = False
            elif e.key == K_SPACE: ship.start_charge()
            elif e.key == K_f: ship.tap_fire()
        elif e.type == KEYUP:
            if e.key == K_SPACE: ship.release_charge()

    if not finish:
        screen.blit(background, (0,0))
        ship.update(); monsters.update(); asteroids.update(); bullets.update(); enemy_bullets.update(); bombs.update(); boss_group.update(); particles.update(); powerups.update()
        monsters.draw(screen); asteroids.draw(screen); bullets.draw(screen); enemy_bullets.draw(screen); bombs.draw(screen); boss_group.draw(screen); powerups.draw(screen); particles.draw(screen); ship.reset(); draw_hud()

        if (sprite.spritecollide(ship, monsters, True) or sprite.spritecollide(ship, asteroids, True)) and not ship.has_shield(): life -= 1
        hit_by_bullets = sprite.spritecollide(ship, enemy_bullets, True)
        if hit_by_bullets and not ship.has_shield(): life -= max(1, len(hit_by_bullets))

        for b in bombs.sprites():
            if any(sprite.collide_rect(b, pb) for pb in bullets.sprites()):
                spawn_explosion(b.rect.centerx, b.rect.centery, charged=False); b.explode()

        def on_target_killed(px, py):
            if random() < POWERUP_SPAWN_CHANCE:
                powerups.add(PowerUp(('shield','rapid')[randint(0,1)], px, py))

        # Bullet vs enemies
        for pb in bullets.sprites():
            hits = sprite.spritecollide(pb, monsters, False)
            if hits:
                for m in hits:
                    m.hp -= pb.damage
                    if m.hp <= 0:
                        on_target_killed(m.rect.centerx, m.rect.centery)
                        spawn_explosion(m.rect.centerx, m.rect.centery, charged=pb.charged)
                        m.kill(); 
                        # increment score safely
                        globals()['score'] += 1
                pb.pierce -= 1
                if pb.pierce <= 0: pb.kill()
            hits2 = sprite.spritecollide(pb, asteroids, False)
            if hits2:
                for a in hits2:
                    a.hp -= pb.damage
                    if a.hp <= 0:
                        on_target_killed(a.rect.centerx, a.rect.centery)
                        spawn_explosion(a.rect.centerx, a.rect.centery, charged=pb.charged)
                        a.kill(); globals()['score'] += 1
                pb.pierce -= 1
                if pb.pierce <= 0: pb.kill()

        got = sprite.spritecollide(ship, powerups, True)
        for item in got:
            if item.kind == 'shield': ship.shield_until = timer() + SHIELD_DURATION
            else: ship.rapid_until = timer() + RAPID_FIRE_DURATION

        if level in (1,2):
            while len(monsters) < LEVELS[level]['monsters']:
                monsters.add(Enemy(randint(80, WIN_WIDTH-80), randint(-260, -80), randint(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED)))
            while len(asteroids) < LEVELS[level]['asteroids']:
                asteroids.add(Asteroid(randint(30, WIN_WIDTH-30), randint(-260, -80), randint(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED+1)))

        if level in (1,2) and score >= LEVELS[level]['goal']:
            level += 1; current_level_data = LEVELS[level]; spawn_level_content(level)
            draw_text_center(screen, font_mid.render(f'Level {level}!', True, (255,255,255)), WIN_HEIGHT//2 - 30); display.update(); time.delay(900)
            if level == 3: boss_group.add(Boss())

        if level == 3 and boss_group:
            bboss = next(iter(boss_group)); draw_boss_hp(bboss)
            for pb in bullets.sprites():
                if sprite.collide_rect(pb, bboss):
                    bboss.hp -= pb.damage; spawn_explosion(pb.rect.centerx, pb.rect.centery, charged=True)
                    pb.pierce -= 1
                    if pb.pierce <= 0: pb.kill()
                    bboss.rect.x += randint(-2,2); bboss.rect.y += randint(-1,1)
            if bboss.hp <= 0:
                boss_group.empty(); finish = True; show_end_banner = True; end_banner_time = timer()
                screen.blit(win_txt, (WIN_WIDTH//2 - win_txt.get_width()//2, WIN_HEIGHT//2 - 40))

        if life <= 0 or (lost >= 30 and not finish):
            finish = True; show_end_banner = True; end_banner_time = timer()
            screen.blit(lose_txt, (WIN_WIDTH//2 - lose_txt.get_width()//2, WIN_HEIGHT//2 - 40))

        display.update()

    else:
        if (timer() - end_banner_time) > 1.5:
            show_end_banner = False
            score = 0; lost = 0; life = PLAYER_LIVES; level = 1; current_level_data = LEVELS[level]
            monsters.empty(); asteroids.empty(); bullets.empty(); enemy_bullets.empty(); bombs.empty(); boss_group.empty(); particles.empty(); powerups.empty()
            ship.rect.x, ship.rect.y = 5, WIN_HEIGHT - 120; ship.rapid_until = 0.0; ship.shield_until = 0.0
            spawn_level_content(level); finish = False

quit()
