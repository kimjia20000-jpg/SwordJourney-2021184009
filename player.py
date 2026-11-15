from pathlib import Path

from pico2d import (
    load_image, SDL_KEYDOWN, SDL_KEYUP,
    SDLK_LEFT, SDLK_RIGHT, SDLK_SPACE, SDLK_a, SDLK_s, SDLK_d,
)
from settings import (
    PLAYER_DRAW_SCALE, PLAYER_FOOT_HALF_WIDTH, MOVE_SPEED,
    JUMP_SPEED, GRAVITY, IDLE_FPS, RUN_FPS, ATTACK_DURATION,
)

from skills import SkillController, SKILL_DATA

BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "assets" / "images" / "player_actions.png"
HURT_IMAGE_PATH = BASE_DIR / "assets" / "images" / "player_hurt.png"
IDLE_FRAMES = (
    (103, 13, 313, 324), (456, 13, 667, 324),
    (809, 14, 1020, 324), (1163, 18, 1375, 325),
)
RUN_FRAMES = (
    (89, 379, 316, 678), (467, 379, 664, 686),
    (791, 379, 1031, 686), (1178, 382, 1381, 687),
)
ATTACK_FRAMES = (
    (76, 741, 292, 1050), (440, 743, 683, 1050),
    (779, 754, 1063, 1050), (1172, 741, 1393, 1050),
)
BASIC_ATTACK_DAMAGE = 10
PLAYER_MAX_HP = 100
SLIME_CONTACT_DAMAGE = 10
INVINCIBLE_DURATION = 1.0
BLINK_INTERVAL = 0.08
PLAYER_BODY_HALF_WIDTH = 16.0
PLAYER_BODY_HEIGHT = 72.0
HURT_DURATION = 0.22
KNOCKBACK_SPEED = 300.0
KNOCKBACK_DECELERATION = 1000.0
KNOCKBACK_UP_SPEED = 180.0


def rectangles_overlap(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


class Player:
    def __init__(self, stage):
        self.stage = stage
        self.image = load_image(str(IMAGE_PATH))
        self.hurt_image = load_image(str(HURT_IMAGE_PATH))
        if (self.image.w, self.image.h) != (1448, 1086):
            raise ValueError("player_actions.png는 1448x1086 크기의 원본 이미지를 사용해야 합니다.")
        self.hurt_rect = (
            0, round(self.hurt_image.h * 35 / 1254),
            round(self.hurt_image.w * 1214 / 1254),
            round(self.hurt_image.h * 1228 / 1254),
        )
        self.x = stage.spawn_x
        self.y = stage.spawn_y
        self.foot_half_width = PLAYER_FOOT_HALF_WIDTH
        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False
        self.attack_pressed = False
        self.direction = 0
        self.face_direction = 1
        self.velocity_y = 0.0
        self.on_ground = True
        self.motion = "IDLE"
        self.frame = 0.0
        self.attacking = False
        self.attack_elapsed = 0.0
        self.attack_direction = 1
        self.hit_targets = set()
        self.max_hp = PLAYER_MAX_HP
        self.hp = self.max_hp
        self.alive = True
        self.level = 1
        self.exp = 0
        self.max_mp = 50
        self.mp = float(self.max_mp)
        self.attack_power = BASIC_ATTACK_DAMAGE
        self.notice = ""
        self.notice_remaining = 0.0
        self.level_notice = ""
        self.level_notice_remaining = 0.0
        self.skill_keys_pressed = set()
        self.skills = SkillController(self)
        self.invincible_remaining = 0.0
        self.hurt_remaining = 0.0
        self.hurt_face_direction = 1
        self.knockback_velocity_x = 0.0
        self.half_width = max(
            right - left for left, top, right, bottom
            in IDLE_FRAMES + RUN_FRAMES + ATTACK_FRAMES
        ) * PLAYER_DRAW_SCALE / 2

    @property
    def exp_to_next(self):
        return 50 + (self.level - 1) * 25

    def gain_exp(self, amount):
        if not self.alive or amount <= 0:
            return
        self.exp += amount
        leveled = False
        unlocked = []
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            self.max_hp += 10
            self.max_mp += 5
            self.hp = self.max_hp
            self.mp = float(self.max_mp)
            leveled = True
            unlocked.extend(spec["name"] for spec in SKILL_DATA.values()
                            if spec["level"] == self.level)
        if leveled:
            self.level_notice = f"레벨 {self.level}! " + (
                " · ".join(unlocked) + " 해금" if unlocked else "체력과 마나 회복"
            )
            self.level_notice_remaining = 2.5

    def deal_damage(self, target, damage, direction):
        # 기본 공격과 모든 스킬이 이 경로를 공유한다.
        # 이미 죽은 대상은 take_damage에서 거부하므로 경험치가 중복되지 않는다.
        if not self.alive:
            return False
        if not target.take_damage(damage, attack_direction=direction):
            return False
        if not target.alive:
            self.gain_exp(target.exp_reward)
        return True

    def show_notice(self, text):
        self.notice = text
        self.notice_remaining = 1.6

    def handle_event(self, event):
        if not self.alive:
            return
        skill_keys = {SDLK_s: "slash", SDLK_d: "wave"}
        if event.type == SDL_KEYUP and event.key in skill_keys:
            self.skill_keys_pressed.discard(event.key)
            return
        if event.type == SDL_KEYDOWN and event.key in skill_keys:
            if event.key not in self.skill_keys_pressed:
                self.skill_keys_pressed.add(event.key)
                self.skills.try_cast(skill_keys[event.key])
            return
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_LEFT:
                self.left_pressed = True
            elif event.key == SDLK_RIGHT:
                self.right_pressed = True
            elif event.key == SDLK_SPACE:
                if not self.jump_pressed:
                    self.jump_pressed = True
                    if self.on_ground and self.hurt_remaining <= 0:
                        self.velocity_y = JUMP_SPEED
                        self.on_ground = False
            elif event.key == SDLK_a:
                if not self.attack_pressed:
                    self.attack_pressed = True
                    if not self.attacking:
                        self.start_attack()
        elif event.type == SDL_KEYUP:
            if event.key == SDLK_LEFT:
                self.left_pressed = False
            elif event.key == SDLK_RIGHT:
                self.right_pressed = False
            elif event.key == SDLK_SPACE:
                self.jump_pressed = False
            elif event.key == SDLK_a:
                self.attack_pressed = False

    def start_attack(self):
        if not self.alive or self.hurt_remaining > 0 or self.skills.active is not None:
            return
        input_direction = int(self.right_pressed) - int(self.left_pressed)
        if input_direction:
            self.face_direction = input_direction
        self.attacking = True
        self.attack_elapsed = 0.0
        self.attack_direction = self.face_direction
        self.hit_targets.clear()

    def cancel_attack(self):
        self.attacking = False
        self.attack_elapsed = 0.0
        self.hit_targets.clear()

    def update(self, dt):
        if not self.alive:
            return
        self.mp = min(float(self.max_mp), self.mp + 2.0 * dt)
        self.notice_remaining = max(0.0, self.notice_remaining - dt)
        self.level_notice_remaining = max(0.0, self.level_notice_remaining - dt)
        self.invincible_remaining = max(0.0, self.invincible_remaining - dt)
        was_hurt = self.hurt_remaining > 0
        self.update_movement(dt)
        self.skills.update(dt)
        if was_hurt:
            self.hurt_remaining = max(0.0, self.hurt_remaining - dt)
            if self.hurt_remaining <= 0:
                self.knockback_velocity_x = 0.0
                self.frame = 0.0
            return
        self.update_motion_animation(dt)
        self.update_attack(dt)
        self.check_attack_hits()
        self.check_contact_damage()

    def update_movement(self, dt):
        if self.hurt_remaining > 0:
            self.direction = 0
            self.update_knockback(dt)
        else:
            self.direction = int(self.right_pressed) - int(self.left_pressed)
            if self.direction:
                self.face_direction = self.direction
            self.x += self.direction * MOVE_SPEED * dt
        # 화면 경계가 아니라 전체 스테이지 경계로 제한한다.
        limited_x = max(self.half_width, min(self.stage.width - self.half_width, self.x))
        if limited_x != self.x:
            self.knockback_velocity_x = 0.0
        self.x = limited_x
        old_y = self.y
        self.y += self.velocity_y * dt - 0.5 * GRAVITY * dt * dt
        self.velocity_y -= GRAVITY * dt
        self.on_ground = False
        if self.velocity_y <= 0:
            platform = self.stage.find_landing(self.x, self.foot_half_width, old_y, self.y)
            if platform is not None:
                self.y = float(platform.top)
                self.velocity_y = 0.0
                self.on_ground = True
        if self.attacking and not self.on_ground and self.direction:
            self.attack_direction = self.direction

    def update_knockback(self, dt):
        speed = abs(self.knockback_velocity_x)
        if speed <= 0:
            return
        direction = 1 if self.knockback_velocity_x > 0 else -1
        move_time = min(dt, self.hurt_remaining, speed / KNOCKBACK_DECELERATION)
        self.x += direction * (
            speed * move_time - 0.5 * KNOCKBACK_DECELERATION * move_time ** 2
        )
        self.knockback_velocity_x = direction * max(
            0.0, speed - KNOCKBACK_DECELERATION * move_time
        )

    def update_motion_animation(self, dt):
        next_motion = "AIR" if not self.on_ground else ("RUN" if self.direction else "IDLE")
        if next_motion != self.motion:
            self.motion = next_motion
            self.frame = 0.0
        if self.motion == "IDLE":
            self.frame = (self.frame + IDLE_FPS * dt) % len(IDLE_FRAMES)
        elif self.motion == "RUN":
            self.frame = (self.frame + RUN_FPS * dt) % len(RUN_FRAMES)
        else:
            self.frame = 1.0

    def update_attack(self, dt):
        if self.attacking:
            self.attack_elapsed += dt
            if self.attack_elapsed >= ATTACK_DURATION:
                self.attacking = False
                self.attack_elapsed = 0.0
        if not self.attacking and self.attack_pressed:
            self.start_attack()

    def get_attack_box(self):
        if not self.attacking:
            return None
        progress = self.attack_elapsed / ATTACK_DURATION
        if not 0.25 <= progress < 0.75:
            return None
        if progress < 0.5:
            near_x, far_x, bottom_y, top_y = 4, 44, 20, 65
        else:
            near_x, far_x, bottom_y, top_y = 4, 48, 4, 40
        if self.attack_direction == 1:
            left, right = self.x + near_x, self.x + far_x
        else:
            left, right = self.x - far_x, self.x - near_x
        return left, self.y + bottom_y, right, self.y + top_y

    def check_attack_hits(self):
        box = self.get_attack_box()
        if box is None:
            return
        for slime in self.stage.slimes:
            if not slime.alive or slime in self.hit_targets:
                continue
            if rectangles_overlap(box, slime.get_body_box()):
                if self.deal_damage(slime, self.attack_power, self.attack_direction):
                    self.hit_targets.add(slime)

    def get_body_box(self):
        return (self.x - PLAYER_BODY_HALF_WIDTH, self.y,
                self.x + PLAYER_BODY_HALF_WIDTH, self.y + PLAYER_BODY_HEIGHT)

    def check_contact_damage(self):
        if not self.alive or self.invincible_remaining > 0:
            return
        for slime in self.stage.slimes:
            if slime.alive and rectangles_overlap(self.get_body_box(), slime.get_body_box()):
                if self.take_damage(SLIME_CONTACT_DAMAGE, source_x=slime.x):
                    break

    def take_damage(self, damage, source_x=None):
        if not self.alive or damage <= 0 or self.invincible_remaining > 0:
            return False
        self.hp = max(0, self.hp - damage)
        if self.hp == 0:
            self.die()
            return True
        self.invincible_remaining = INVINCIBLE_DURATION
        if source_x is None or source_x == self.x:
            direction = -self.face_direction
        else:
            direction = -1 if source_x > self.x else 1
        self.cancel_attack()
        self.skills.cancel_cast()
        self.hurt_remaining = HURT_DURATION
        self.hurt_face_direction = -direction
        self.face_direction = self.hurt_face_direction
        self.knockback_velocity_x = direction * KNOCKBACK_SPEED
        self.velocity_y = KNOCKBACK_UP_SPEED
        self.on_ground = False
        self.direction = 0
        self.frame = 0.0
        return True

    def die(self):
        self.alive = False
        self.invincible_remaining = 0.0
        self.hurt_remaining = 0.0
        self.knockback_velocity_x = 0.0
        self.left_pressed = self.right_pressed = False
        self.jump_pressed = self.attack_pressed = False
        self.direction = 0
        self.velocity_y = 0.0
        self.cancel_attack()
        self.skills.clear_on_death()
        self.skill_keys_pressed.clear()
        self.motion = "IDLE"
        self.frame = 0.0

    def draw(self, camera_x=0.0):
        if self.alive and self.hurt_remaining > 0:
            self.draw_hurt(camera_x)
            return
        if self.alive and self.invincible_remaining > 0:
            if int(self.invincible_remaining / BLINK_INTERVAL) % 2 == 1:
                return
        if self.skills.active is not None:
            index = min(int(self.skills.progress * len(ATTACK_FRAMES)), len(ATTACK_FRAMES) - 1)
            rect, direction = ATTACK_FRAMES[index], self.skills.direction
        elif self.attacking:
            index = min(int(self.attack_elapsed / ATTACK_DURATION * len(ATTACK_FRAMES)),
                        len(ATTACK_FRAMES) - 1)
            rect, direction = ATTACK_FRAMES[index], self.attack_direction
        else:
            frames = IDLE_FRAMES if self.motion == "IDLE" else RUN_FRAMES
            rect, direction = frames[int(self.frame)], self.face_direction
        left, top, right, bottom = rect
        width, height = right - left, bottom - top
        self.draw_image(self.image, rect, direction,
                        width * PLAYER_DRAW_SCALE, height * PLAYER_DRAW_SCALE, camera_x)

    def draw_hurt(self, camera_x=0.0):
        left, top, right, bottom = self.hurt_rect
        draw_height = 311.0 * PLAYER_DRAW_SCALE
        draw_width = draw_height * (right - left) / (bottom - top)
        self.draw_image(self.hurt_image, self.hurt_rect, self.hurt_face_direction,
                        draw_width, draw_height, camera_x)

    def draw_image(self, image, rect, direction, width, height, camera_x):
        left, top, right, bottom = rect
        source_width, source_height = right - left, bottom - top
        # 실제 x는 바꾸지 않는다. 화면에 그리는 좌표만 변환한다.
        draw_x, draw_y = self.x - camera_x, self.y + height / 2
        if direction == 1:
            image.clip_draw(left, image.h - bottom, source_width, source_height,
                            draw_x, draw_y, width, height)
        else:
            image.clip_composite_draw(left, image.h - bottom, source_width, source_height,
                                      0, 'h', draw_x, draw_y, width, height)
