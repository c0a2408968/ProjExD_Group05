import pygame as pg
import sys
import os
import random

# 指定条件
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# =====================
# 定数
# =====================
WIDTH, HEIGHT = 800, 450
FPS = 60
GROUND_Y = 360
GRAVITY = 1
JUMP_POWER = -18
MAX_JUMP = 3

# =====================
# 初期化
# =====================
pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("こうかとん、講義に遅刻する")
clock = pg.time.Clock()
font = pg.font.SysFont(None, 32)

# =====================
# 主人公
# =====================
class Player(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pg.image.load("fig/2.png").convert_alpha()
        self.image = pg.transform.scale(self.image, (48, 48))
        self.rect = self.image.get_rect(midbottom=(150, GROUND_Y))
        self.vel_y = 0
        self.jump_count = 0
        self.weapon_count = 0   # 武器の所持数

    def reset_for_stage(self):
        """ステージ開始時に位置や落下速度だけリセット（武器数は保持）"""
        self.rect.midbottom = (150, GROUND_Y)
        self.vel_y = 0
        self.jump_count = 0

    def update(self, grounds):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        landed = False
        for g in grounds:
            if (
                self.rect.colliderect(g)
                and self.vel_y >= 0
                and self.rect.bottom - self.vel_y <= g.top
            ):
                self.rect.bottom = g.top
                self.vel_y = 0
                self.jump_count = 0
                landed = True

        # 画面下に落ちたら穴落下
        if not landed and self.rect.top > HEIGHT:
            return "fall"
        return None

    def jump(self):
        if self.jump_count < MAX_JUMP:
            self.vel_y = JUMP_POWER
            self.jump_count += 1

    # （将来、敵を実装してから使う用。今は未使用でもOK）
    def attack(self, enemies, effects):
        if self.weapon_count <= 0:
            return
        attack_rect = pg.Rect(self.rect.right, self.rect.top, 60, self.rect.height)
        for enemy in enemies[:]:
            if attack_rect.colliderect(enemy.rect):
                dead = enemy.take_damage()
                if dead:
                    enemies.remove(enemy)
                    effects.append(AttackEffect(enemy.rect.centerx, enemy.rect.centery))

# =====================
# 段差
# =====================
class Step:
    def __init__(self, x):
        h = random.choice([40, 80])
        w = random.randint(80, 140)
        self.rect = pg.Rect(x, GROUND_Y - h, w, h)

    def update(self, speed):
        self.rect.x -= speed

# =====================
# 穴
# =====================
class Hole:
    def __init__(self, x):
        w = random.randint(100, 160)
        self.rect = pg.Rect(x, GROUND_Y, w, HEIGHT)

    def update(self, speed):
        self.rect.x -= speed

# =====================
# ゴール旗
# =====================
class GoalFlag:
    def __init__(self, x):
        self.pole = pg.Rect(x, GROUND_Y - 120, 10, 120)
        self.flag = pg.Rect(x + 10, GROUND_Y - 120, 50, 30)

    def update(self, speed):
        self.pole.x -= speed
        self.flag.x -= speed

    def draw(self):
        pg.draw.rect(screen, (200, 200, 200), self.pole)
        pg.draw.rect(screen, (255, 0, 0), self.flag)

# =====================
# 武器
# =====================
class WeaponItem:
    def __init__(self, x):
        self.image = pg.image.load("fig/buki.png").convert_alpha()
        self.image = pg.transform.scale(self.image, (40, 40))
        self.rect = self.image.get_rect(midbottom=(x, GROUND_Y))

    def update(self, speed):
        self.rect.x -= speed

    def draw(self):
        screen.blit(self.image, self.rect)

# =====================
# 攻撃エフェクト
# =====================
class AttackEffect:
    def __init__(self, x, y):
        self.image = pg.image.load("fig/kougeki.png").convert_alpha()
        self.image = pg.transform.scale(self.image, (60, 60))
        self.rect = self.image.get_rect(center=(x, y))
        self.life = 25
        self.visible = True

    def update(self):
        self.life -= 1
        if self.life % 4 == 0:
            self.visible = not self.visible

    def draw(self):
        if self.visible:
            screen.blit(self.image, self.rect)

# =====================
# 武器エフェクト
# =====================
class WeaponUseEffect:
    def __init__(self, player):
        base = pg.image.load("fig/buki.png").convert_alpha()
        base = pg.transform.scale(base, (40, 40))

        # 45度右に傾ける
        self.image = pg.transform.rotate(base, -45)

        self.player = player

        self.offset_x = player.rect.width - 3
        self.offset_y = -5

        self.rect = self.image.get_rect()
        self.life = 20

        self.update_position()

    def update_position(self):
        self.rect.centerx = self.player.rect.left + self.offset_x
        self.rect.centery = self.player.rect.centery + self.offset_y

    def update(self):
        self.life -= 1
        self.update_position()  #  毎フレーム追従

    def draw(self):
        screen.blit(self.image, self.rect)


# =====================
# メイン
# =====================
def main():
    stage = 1
    speed = 6
    goal_distance = 2500

    player = Player()  # ★ ここで1回だけ生成（武器数を保持するため）

    while True:
        player.reset_for_stage()  # ★ 位置だけリセット（weapon_countは保持）

        steps = []
        holes = []
        goal = GoalFlag(goal_distance)

        weapons = []
        effects = []
        weapon_effects = []
        enemies = []

        # ===== 武器の出現数（0〜2個）=====
        r = random.random()
        if r < 0.7:
            weapon_spawn = 1
        elif r < 0.9:
            weapon_spawn = 2
        else:
            weapon_spawn = 0

        for _ in range(weapon_spawn):
            x = random.randint(WIDTH + 200, goal_distance - 300)
            weapons.append(WeaponItem(x))
        # ===============================

        frame = 0
        state = "play"
        next_stage = False

        while True:
            # ---------- イベント ----------
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_SPACE and state == "play":
                        player.jump()

                    # ===== 攻撃（Enterキー）=====
                    if event.key == pg.K_RETURN and state == "play":
                        if player.weapon_count > 0:
                            # 武器（主人公に追従）
                            weapon_effects.append(WeaponUseEffect(player))

                            # 攻撃エフェクト（その場に出る）
                            fx = player.rect.right + 40
                            fy = player.rect.centery
                            effects.append(AttackEffect(fx, fy))

                            player.weapon_count -= 1
                    # ============================

                    if state == "clear":
                        if event.key == pg.K_y:
                            stage += 1
                            speed += 1
                            goal_distance += 1500
                            next_stage = True
                        if event.key == pg.K_n:
                            pg.quit()
                            sys.exit()

                    if state == "gameover" and event.key == pg.K_r:
                        next_stage = True

            # ---------- ゲーム処理 ----------
            if state == "play":
                frame += 1

                if frame % 80 == 0:
                    x = WIDTH + 50
                    if random.random() < 0.5:
                        steps.append(Step(x))
                    else:
                        holes.append(Hole(x))

                for s in steps:
                    s.update(speed)
                for h in holes:
                    h.update(speed)
                for w in weapons:
                    w.update(speed)

                goal.update(speed)

                # ===== 地面生成 =====
                base_grounds = [pg.Rect(0, GROUND_Y, WIDTH, HEIGHT)]

                for h in holes:
                    new_grounds = []
                    for g in base_grounds:
                        if not g.colliderect(h.rect):
                            new_grounds.append(g)
                        else:
                            if g.left < h.rect.left:
                                new_grounds.append(
                                    pg.Rect(g.left, g.top, h.rect.left - g.left, g.height)
                                )
                            if h.rect.right < g.right:
                                new_grounds.append(
                                    pg.Rect(h.rect.right, g.top, g.right - h.rect.right, g.height)
                                )
                    base_grounds = new_grounds

                grounds = base_grounds + [s.rect for s in steps]

                if player.update(grounds) == "fall":
                    state = "gameover"

                # 段差の横衝突
                for s in steps:
                    if player.rect.colliderect(s.rect):
                        if not (player.rect.bottom <= s.rect.top + 5 and player.vel_y >= 0):
                            state = "gameover"

                # ===== 武器取得 =====
                for w in weapons[:]:
                    if player.rect.colliderect(w.rect):
                        player.weapon_count += 1
                        weapons.remove(w)

                # ===== エフェクト更新 =====
                for e in effects[:]:
                    e.update()
                    if e.life <= 0:
                        effects.remove(e)

                for we in weapon_effects[:]:
                    we.update()
                    if we.life <= 0:
                        weapon_effects.remove(we)

                if player.rect.colliderect(goal.pole):
                    state = "clear"

            # ---------- 描画 ----------
            screen.fill((135, 206, 235))
            pg.draw.rect(screen, (50, 200, 50), (0, GROUND_Y, WIDTH, HEIGHT))

            for h in holes:
                pg.draw.rect(screen, (0, 0, 0), h.rect)
            for s in steps:
                pg.draw.rect(screen, (50, 200, 50), s.rect)

            for w in weapons:
                w.draw()

            for we in weapon_effects:
                we.draw()
            for e in effects:
                e.draw()

            goal.draw()
            screen.blit(player.image, player.rect)

            screen.blit(font.render(f"STAGE {stage}", True, (0, 0, 0)), (10, 10))
            screen.blit(font.render(f"WEAPON × {player.weapon_count}", True, (0, 0, 0)), (10, 40))

            if state == "gameover":
                screen.blit(font.render("GAME OVER (R)", True, (255, 0, 0)),
                            (WIDTH//2 - 100, HEIGHT//2))

            if state == "clear":
                screen.blit(font.render("NEXT STAGE? Y / N", True, (0, 0, 0)),
                            (WIDTH//2 - 120, HEIGHT//2))

            pg.display.update()
            clock.tick(FPS)

            if next_stage:
                break

# =====================
if __name__ == "__main__":
    main()
