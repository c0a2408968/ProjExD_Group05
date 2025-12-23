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
SPAWN_INTERVAL = 90  # タマゴ生成間隔（フレーム数）
WEAPON_MIN_DIST = 300   # 主人公から最低この距離は離す
WEAPON_MAX_DIST = 900   # これ以上先には出さない
WEAPON_INTERVAL = 240   # フレーム間隔（4秒）


# =====================
# 初期化
# =====================
pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("こうかとん、講義に遅刻する")
clock = pg.time.Clock()
font = pg.font.SysFont(None, 32)
happy_img = pg.image.load("fig/koukaton_happy.png").convert_alpha()
happy_img = pg.transform.scale(happy_img, (200, 200))
bg_img = pg.image.load("fig/kyanpus.jpg").convert()  #ゴール時にキャンパスの写真表示
bg_img = pg.transform.scale(bg_img, (WIDTH, HEIGHT))
gameover_bg = pg.image.load("fig/sensei_okoru.png").convert()  #ゲームオーバー時に先生が起こっている写真表示
gameover_bg = pg.transform.scale(gameover_bg, (WIDTH, HEIGHT))



# =====================
# 主人公
# =====================
class Player(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        #self.image = pg.image.load("C:/Users/Admin/Documents/ProjExD/ex5/fig/2.png").convert_alpha()
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

        # ★ ゴール判定用（画面上まで）
        self.hitbox = pg.Rect(x - 20, 0, 80, HEIGHT)

    def update(self, speed):
        self.pole.x -= speed
        self.flag.x -= speed
        self.hitbox.x -= speed

    def draw(self):
        pg.draw.rect(screen, (200, 200, 200), self.pole)
        pg.draw.rect(screen, (255, 0, 0), self.flag)
        # デバッグ用（必要なら）
        # pg.draw.rect(screen, (0,0,255), self.hitbox, 2)


# =====================
# 赤い先生
# =====================
def make_teacher_image():  # 赤い先生を作成
    surf = pg.Surface((40, 60), pg.SRCALPHA)  # 透過あり
    surf.fill((0, 0, 0, 0))  # 完全透明

    # 体
    pg.draw.rect(surf, (200, 50, 50), (5, 10, 30, 45), border_radius=8)

    # 頭
    pg.draw.circle(surf, (230, 80, 80), (20, 12), 10)

    # 目
    pg.draw.circle(surf, (0, 0, 0), (16, 10), 2)
    pg.draw.circle(surf, (0, 0, 0), (24, 10), 2)

    return surf


class Teacher:
    def __init__(self, x):
        self.image = make_teacher_image()
        self.rect = self.image.get_rect(midbottom=(x, GROUND_Y))

        self.vel_y = 0
        self.on_ground = False
        self.jump_timer = 0

        self.mode = "enter"        # ★ 状態
        self.base_speed = 0        # ★ 自分の移動速度

    def update(self, grounds, scroll_speed, speed_boost):
        RIGHT_LIMIT = WIDTH - 80

        # ===== フェーズ① 登場 =====
        if self.mode == "enter":
            self.rect.x += scroll_speed * 1.5  # 少し速め
            if self.rect.x >= RIGHT_LIMIT:
                self.rect.x = RIGHT_LIMIT
                self.mode = "wait"

        # ===== フェーズ② 右端待機 =====
        # elif self.mode == "wait":

        #     if speed_boost > 0:
        #         # 加速中：固定せず、世界より遅く流れる
        #         self.rect.x -= (scroll_speed - scroll_speed * 0.4)
        #     else:
        #         # 通常時：右端に張り付く
        #         self.rect.x = RIGHT_LIMIT

        elif self.mode == "wait":
            # 通常時は右端に固定
            self.rect.x = RIGHT_LIMIT

            # 加速が始まったら chase へ
            if speed_boost > 0:
                self.mode = "chase"


        elif self.mode == "chase":
            # 加速中：距離が縮まる
            if speed_boost > 0:
                self.rect.x -= (scroll_speed - scroll_speed * 0.4)
            else:
                # 加速終了 → その場で停止
                self.mode = "stop"


        elif self.mode == "stop":
            # 再加速したら、また追い詰めフェーズへ
            if speed_boost > 0:
                self.mode = "chase"


        # ===== 重力・ジャンプ（共通）=====
        self.jump_timer += 1
        if self.jump_timer >= 90 and self.on_ground:
            self.vel_y = JUMP_POWER
            self.on_ground = False
            self.jump_timer = 0

        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        self.on_ground = False
        for g in grounds:
            if (
                self.rect.colliderect(g)
                and self.vel_y >= 0
                and self.rect.bottom - self.vel_y <= g.top
            ):
                self.rect.bottom = g.top
                self.vel_y = 0
                self.on_ground = True
                break


    
    def draw(self):
        screen.blit(self.image, self.rect)


# =====================
# バス
# =====================
class Bus:
    """
    空から落下してくるバス障害物を表すクラス。
    上から着地することは可能だが、
    横や下から衝突するとゲームオーバーになる。
    """
    def __init__(self, x: int) -> None:
        """
        バスを生成する
        引数：x (int)：バスを出現させるx座標
        戻り値：なし
        """
        self.image = pg.image.load(
            "fig/bus_nonstep_close.png"
        ).convert_alpha()
        self.image = pg.transform.scale(self.image, (100, 50))
        self.rect = self.image.get_rect(midtop=(x, -50))  # 画面の外からの登場のため、負の値
        self.vel_y = 6  # 落下速度

    def update(self, speed: int) -> None:
        """
        バスの位置を更新する
        引数：speed (int)：スクロール速度
        戻り値：なし
        """
        self.rect.y += self.vel_y
        self.rect.x -= speed  # ステージが進むごとに横移動のスピードが速くなる

    def draw(self) -> None:
        """
        バスを画面に描画する
        引数：なし
        戻り値：なし
        """
        screen.blit(self.image, self.rect)



# =====================
# タマゴ
# =====================
class Egg:
    def __init__(self):
        egg_images = [
            pg.image.load("fig/egg1.png").convert_alpha(),
            pg.image.load("fig/egg2.png").convert_alpha(),
            pg.image.load("fig/egg3.png").convert_alpha(),
            pg.image.load("fig/egg4.png").convert_alpha(),
            pg.image.load("fig/egg5.png").convert_alpha(),
            pg.image.load("fig/egg6.png").convert_alpha()
        ]
        self.image = random.choice(egg_images)  # 6枚からランダム
        self.image = pg.transform.scale(self.image, (self.image.get_width()//2, self.image.get_height()//2))  # サイズ縮小
        self.image.set_colorkey((255, 255, 255))  # 白を透過
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH  # 画面右端から出現
        self.rect.bottom = GROUND_Y  # 地面に設置
        

    def update(self, speed):
        self.rect.x -= speed*0.8  # 背景スクロールの80%の速度で左へ
        return self.rect.right > 0  # 画面外に出たかどうかを返す
       
    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Egg_Counter:
    def __init__(self, max_count=7, pos=(700, 400)):
        self.count = 0
        self.max_count = max_count
        self.pos = pos  # 画面右下など表示位置

    def add(self):
        self.count += 1
        if self.count >= self.max_count:
            self.count = 0
            return True  # カウントが最大になったらTrue（加速トリガー）
        return False

    def draw(self, screen, font):  # 右下に表示
        text = font.render(f"EGGS: {self.count}", True, (0, 0, 0))
        screen.blit(text, self.pos)

    def reset(self):
        self.count = 0  # カウントリセット


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
    goal_distance = 12000
    egg_timer = 0
    eggs = []
    egg_counter = Egg_Counter()
    speed_boost = 0
    boost_frames = FPS*0.5  # 1秒間に画面が更新される回数（フレーム/秒）が0.5倍加速持続時間
    weapon_spawned = False

    player = Player()  # ★ ここで1回だけ生成（武器数を保持するため）

    while True:
        player.reset_for_stage()  # ★ 位置だけリセット（weapon_countは保持）

        weapon_spawned = False
        steps = []
        holes = []
        buses = []
        teachers = []  # 先生リスト

        # ===== 武器の出現数（0〜2個）=====
        r = random.random()
        if r < 0.7:
            weapon_spawn = 1
        elif r < 0.9:
            weapon_spawn = 2
        else:
            weapon_spawn = 0

        teacher_appeared = False
        goal = GoalFlag(goal_distance)

        weapons = []
        effects = []
        weapon_effects = []
        enemies = []

        # ===============================

        frame = 0
        state = "play"
        next_stage = False
        current_speed = speed
        clear_screen = ClearScreen(bg_img, font)
        gameover_screen = GameOverScreen(gameover_bg, font)

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
                            # 武器エフェクト
                            weapon_effects.append(WeaponUseEffect(player))

                            # 攻撃エフェクト
                            # fx = player.rect.right + 40
                            # fy = player.rect.centery
                            # effects.append(AttackEffect(fx, fy))

                            # === 攻撃判定 ===
                            attack_rect = pg.Rect(
                                player.rect.right,
                                player.rect.top - 50,     # 上に広げる
                                200,                      # 横幅も少し広げる
                                player.rect.height + 50   # 下にも広げる
                            )


                            # バス破壊
                            for b in buses[:]:
                                if attack_rect.colliderect(b.rect):
                                    buses.remove(b)
                                    effects.append(
                                        AttackEffect(b.rect.centerx, b.rect.centery)
                                    )

                            # === 先生撃破 ===
                            for t in teachers[:]:
                                if attack_rect.colliderect(t.rect):
                                    teachers.remove(t)
                                    state = "teacher_clear"   # 特別クリア状態へ

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

                    if state == "teacher_clear":
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

                # ===== 段差・穴の生成 =====
                if frame % 80 == 0:
                    x = WIDTH + 100

                    # ゴール直前は穴を出さない
                    if goal.hitbox.x - x < 200:
                        steps.append(Step(x))
                    else:
                        if random.random() < 0.5:
                            steps.append(Step(x))
                        else:
                            holes.append(Hole(x))

                # ===== 地面生成 =====
                base_grounds = [pg.Rect(0, GROUND_Y, WIDTH, HEIGHT)]
                teacher_grounds = [pg.Rect(0, GROUND_Y, WIDTH, HEIGHT)]

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


                # ===== 武器生成（確実に出る版）=====
                if frame % WEAPON_INTERVAL == 0:

                    for _ in range(30):  # 最大30回試行
                        x = random.randint(
                            player.rect.right + WEAPON_MIN_DIST,
                            player.rect.right + WEAPON_MAX_DIST
                        )

                        weapon_rect = pg.Rect(x - 20, GROUND_Y - 40, 40, 40)

                        ok = True

                        # 段差と重なっていないか
                        for s in steps:
                            if weapon_rect.colliderect(s.rect):
                                ok = False
                                break

                        # 穴の上でないか
                        for h in holes:
                            if weapon_rect.colliderect(h.rect):
                                ok = False
                                break

                        # 画面内すぎる場所は禁止（突然出現防止）
                        if x < WIDTH + 40:
                            ok = False

                        if ok:
                            weapons.append(WeaponItem(x))
                            break

                # バスの生成
                if frame % 300 == 0:  # 一定時間ごとにバスを生成
                    buses.append(Bus(random.randint(100, WIDTH - 100)))  # ランダムな位置からバスを落下させる
                if speed_boost > 0:
                    current_speed = speed * 2
                    speed_boost -= 1
                else:
                    current_speed = speed

                for s in steps:
                    s.update(current_speed)
                for h in holes:
                    h.update(current_speed)
                for b in buses:
                    b.update(current_speed)

                
                for w in weapons:
                    w.update(current_speed)

                # goal.update(speed)
                goal.update(current_speed)

                for t in teachers:
                    t.update(teacher_grounds, current_speed, speed_boost)


                if player.update(grounds) == "fall":
                    state = "gameover"

                # 段差の横衝突                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                for s in steps:
                    if player.rect.colliderect(s.rect):
                        if not (player.rect.bottom <= s.rect.top + 5 and player.vel_y >= 0):
                            state = "gameover"

                # バスの衝突
                for b in buses:
                    if player.rect.colliderect(b.rect):
                        if (player.vel_y >= 0 and player.rect.bottom - player.vel_y <= b.rect.top):  # バスの上から着地した場合はセーフ
                            player.rect.bottom = b.rect.top
                            player.vel_y = 0
                            player.jump_count = 0
                        else:
                            state = "gameover"  # 横 or 下に当たったらゲームオーバー
                buses = [b for b in buses if b.rect.top < HEIGHT]  # 画面外のバス画像は削除            

                # ゴール
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

                if player.rect.colliderect(goal.hitbox):
                    state = "clear"

                # 低確率で先生を出現
                if (
                    not teacher_appeared
                    and frame % 120 == 0
                    and random.random() < 0.5
                ):
                    teachers.append(Teacher(player.rect.left - 80))
                    teacher_appeared = True
                # タマゴ生成
                egg_timer += 1
                if egg_timer >= SPAWN_INTERVAL:
                    eggs.append(Egg())  # ここで Egg を作る
                    egg_timer = 0
                
                # タマゴ更新
                for egg in eggs[:]:
                    egg.update(current_speed)  # 移動
                    if egg.rect.top > HEIGHT or egg.rect.right < 0:
                        eggs.remove(egg)
                        continue  # 画面外に出たら削除

                    if player.rect.colliderect(egg.rect):
                        eggs.remove(egg)
                        if egg_counter.add():
                            speed_boost = boost_frames  # 加速トリガー

                pg.display.update()

            # ---------- 描画 ----------
            screen.fill((135, 206, 235))
            pg.draw.rect(screen, (50, 200, 50), (0, GROUND_Y, WIDTH, HEIGHT))

            for h in holes:
                pg.draw.rect(screen, (0, 0, 0), h.rect)
            for s in steps:
                pg.draw.rect(screen, (50, 200, 50), s.rect)
            for b in buses:
                b.draw()
            for t in teachers:  # 先生の描画
                t.draw()
                # pg.draw.rect(screen, (50, 200, 50), s.rect)

            for w in weapons:
                w.draw()

            for we in weapon_effects:
                we.draw()
            for e in effects:
                e.draw()

            goal.draw()
            screen.blit(player.image, player.rect)

            if speed_boost > 0:
                dark_overlay = pg.Surface((WIDTH, HEIGHT))
                dark_overlay.set_alpha(80)  # 透明度
                dark_overlay.fill((0, 0, 0))
                screen.blit(dark_overlay,(0,0))
            for egg in eggs:
                egg_counter.draw(screen, font)
                egg.draw(screen)
                # egg.update(current_speed)

            screen.blit(font.render(f"STAGE {stage}", True, (0, 0, 0)), (10, 10))
            screen.blit(font.render(f"WEAPON × {player.weapon_count}", True, (0, 0, 0)), (10, 40))

            # 半透明背景用Surface
            overlay = pg.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(160)   # 0=完全透明, 255=不透明（150〜180がおすすめ）
            overlay.fill((255, 255, 255))  # 白

            if state == "clear":
                if teacher_appeared:
                    msg = "Class cancellation!Y/N"
                else:
                    msg = "NEXT STAGE? Y / N"
                screen.blit(font.render(msg, True, (0, 0, 255)),
                            (WIDTH//2 - 120, HEIGHT//2))
            if state == "gameover":
                gameover_screen.draw(screen)

            elif state == "clear":
                clear_screen.draw(screen)

            elif state == "teacher_clear":
                overlay = pg.Surface((WIDTH, HEIGHT))
                overlay.set_alpha(180)
                overlay.fill((255, 255, 255))
                screen.blit(overlay, (0, 0))

                screen.blit(
                    happy_img,
                    happy_img.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
                )

                msg = font.render("Teacher defeated! Next Stage? Y / N", True, (0, 120, 0))
                screen.blit(
                    msg,
                    msg.get_rect(center=(WIDTH//2, HEIGHT//2 + 80))
                )

            pg.display.update()
            clock.tick(FPS)

            if next_stage:
                break


# =====================
# ゴール画面クラス
# =====================
class ClearScreen:
    """
    ゴールの旗に着いた時にゴールの画面を表示するクラス
    """
    def __init__(self, bg_img: pg.Surface, font: pg.font.Font) -> None:
        """
        screen : pg.Surface描画対象となる画面
        """
        self.bg_img = bg_img
        self.font = font

    def draw(self, screen: pg.Surface) -> None:
        # 背景
        screen.blit(self.bg_img, (0, 0))

        # 半透明オーバーレイ
        overlay = pg.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(120)
        overlay.fill((255, 255, 255))
        screen.blit(overlay, (0, 0))

        # 文字
        title = self.font.render(
            "Arrival at campus. Avoid being late!", True, (0, 120, 0)
        )
        screen.blit(
            title,
            title.get_rect(center=(WIDTH // 2 - 150, HEIGHT // 2 - 80))
        )

        sub = self.font.render(
            "The next day?  Y / N", True, (0, 0, 0)
        )
        screen.blit(
            sub,
            sub.get_rect(center=(WIDTH // 2 - 150, HEIGHT // 2 - 30))
        )


# =====================
# ゲームオーバー画面クラス
# =====================
class GameOverScreen:
    """
    段差に当たった時や穴に落ちたときにゲームオーバーを表示させるクラス
    """
    def __init__(self, bg_img: pg.Surface, font: pg.font.Font) -> None:
        """
        bg_img : ゲームオーバー画面の背景画像
        font : 文字描画に使用するフォント
        """
        self.bg_img = bg_img
        self.font = font

    def draw(self, screen: pg.Surface) -> None:
        # 背景
        screen.blit(self.bg_img, (0, 0))

        # 半透明オーバーレイ
        overlay = pg.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(140)
        overlay.fill((255, 255, 255))
        screen.blit(overlay, (0, 0))

        # 文字
        title = self.font.render(
            "Kokaton is late.....", True, (200, 0, 0)
        )
        screen.blit(
            title,
            title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        )

        retry = self.font.render(
            "R : Retry", True, (0, 0, 0)
        )
        screen.blit(
            retry,
            retry.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        )

# =====================
if __name__ == "__main__":
    main()
