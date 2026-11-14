from pathlib import Path

from pico2d import (
    load_image,
    get_canvas_width,
    SDL_KEYDOWN,
    SDL_KEYUP,
    SDLK_LEFT,
    SDLK_RIGHT,
    SDLK_SPACE,
    SDLK_a,
)

from settings import (
    PLAYER_DRAW_SCALE,
    PLAYER_FOOT_HALF_WIDTH,
    MOVE_SPEED,
    JUMP_SPEED,
    GRAVITY,
    IDLE_FPS,
    RUN_FPS,
    ATTACK_DURATION,
)


BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "assets" / "images" / "player_actions.png"
HURT_IMAGE_PATH = BASE_DIR / "assets" / "images" / "player_hurt.png"

IDLE_FRAMES = (
    (103, 13, 313, 324),
    (456, 13, 667, 324),
    (809, 14, 1020, 324),
    (1163, 18, 1375, 325),
)

RUN_FRAMES = (
    (89, 379, 316, 678),
    (467, 379, 664, 686),
    (791, 379, 1031, 686),
    (1178, 382, 1381, 687),
)

ATTACK_FRAMES = (
    (76, 741, 292, 1050),
    (440, 743, 683, 1050),
    (779, 754, 1063, 1050),
    (1172, 741, 1393, 1050),
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
    return (
        a[0] < b[2]
        and a[2] > b[0]
        and a[1] < b[3]
        and a[3] > b[1]
    )


class Player:
    def __init__(self, stage):
        self.stage = stage

        self.image = load_image(str(IMAGE_PATH))
        self.hurt_image = load_image(str(HURT_IMAGE_PATH))

        if (self.image.w, self.image.h) != (1448, 1086):
            raise ValueError(
                "player_actions.png는 "
                "1448x1086 크기의 원본 이미지를 사용해야 합니다."
            )

        self.hurt_rect = (
            0,
            round(self.hurt_image.h * 35 / 1254),
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
        self.invincible_remaining = 0.0

        self.hurt_remaining = 0.0
        self.hurt_face_direction = 1
        self.knockback_velocity_x = 0.0

        all_frames = IDLE_FRAMES + RUN_FRAMES + ATTACK_FRAMES
        self.half_width = (
            max(right - left for left, top, right, bottom in all_frames)
            * PLAYER_DRAW_SCALE / 2
        )

    def handle_event(self, event):
        if not self.alive:
            return

        # 피격 중에도 키를 누르거나 뗀 상태는 기록한다.
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
        if not self.alive or self.hurt_remaining > 0:
            return

        input_direction = (
            int(self.right_pressed) - int(self.left_pressed)
        )

        if input_direction != 0:
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

        self.invincible_remaining = max(
            0.0, self.invincible_remaining - dt
        )

        was_hurt = self.hurt_remaining > 0

        self.update_movement(dt)

        if was_hurt:
            self.hurt_remaining = max(
                0.0, self.hurt_remaining - dt
            )

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
            self.direction = (
                int(self.right_pressed) - int(self.left_pressed)
            )

            if self.direction != 0:
                self.face_direction = self.direction

            self.x += self.direction * MOVE_SPEED * dt

        minimum_x = self.half_width
        maximum_x = get_canvas_width() - self.half_width
        limited_x = max(minimum_x, min(maximum_x, self.x))

        if limited_x != self.x:
            self.knockback_velocity_x = 0.0

        self.x = limited_x

        old_y = self.y

        self.y += (
            self.velocity_y * dt
            - 0.5 * GRAVITY * dt * dt
        )

        self.velocity_y -= GRAVITY * dt
        self.on_ground = False

        if self.velocity_y <= 0:
            platform = self.stage.find_landing(
                self.x, self.foot_half_width, old_y, self.y
            )

            if platform is not None:
                self.y = float(platform.top)
                self.velocity_y = 0.0
                self.on_ground = True

        # 공중 공격은 방향키로 공격 방향을 바꿀 수 있다.
        if (
            self.attacking
            and not self.on_ground
            and self.direction != 0
        ):
            self.attack_direction = self.direction

    def update_knockback(self, dt):
        speed = abs(self.knockback_velocity_x)

        if speed <= 0:
            return

        direction = 1 if self.knockback_velocity_x > 0 else -1

        move_time = min(
            dt,
            self.hurt_remaining,
            speed / KNOCKBACK_DECELERATION,
        )

        distance = (
            speed * move_time
            - 0.5 * KNOCKBACK_DECELERATION * move_time ** 2
        )

        self.x += direction * distance

        next_speed = max(
            0.0,
            speed - KNOCKBACK_DECELERATION * move_time,
        )

        self.knockback_velocity_x = direction * next_speed

    def update_motion_animation(self, dt):
        if not self.on_ground:
            next_motion = "AIR"
        elif self.direction != 0:
            next_motion = "RUN"
        else:
            next_motion = "IDLE"

        if next_motion != self.motion:
            self.motion = next_motion
            self.frame = 0.0

        if self.motion == "IDLE":
            self.frame = (
                self.frame + IDLE_FPS * dt
            ) % len(IDLE_FRAMES)

        elif self.motion == "RUN":
            self.frame = (
                self.frame + RUN_FPS * dt
            ) % len(RUN_FRAMES)

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
            near_x, far_x = 4, 44
            bottom_y, top_y = 20, 65
        else:
            near_x, far_x = 4, 48
            bottom_y, top_y = 4, 40

        if self.attack_direction == 1:
            left = self.x + near_x
            right = self.x + far_x
        else:
            left = self.x - far_x
            right = self.x - near_x

        return (
            left,
            self.y + bottom_y,
            right,
            self.y + top_y,
        )

    def check_attack_hits(self):
        attack_box = self.get_attack_box()

        if attack_box is None:
            return

        for slime in self.stage.slimes:
            if not slime.alive or slime in self.hit_targets:
                continue

            if rectangles_overlap(
                attack_box,
                slime.get_body_box(),
            ):
                # 실제 공격 방향을 전달해 그 방향으로 밀어낸다.
                if slime.take_damage(
                    BASIC_ATTACK_DAMAGE,
                    attack_direction=self.attack_direction,
                ):
                    # 같은 공격으로 같은 슬라임을 중복 타격하지 않는다.
                    self.hit_targets.add(slime)

    def get_body_box(self):
        return (
            self.x - PLAYER_BODY_HALF_WIDTH,
            self.y,
            self.x + PLAYER_BODY_HALF_WIDTH,
            self.y + PLAYER_BODY_HEIGHT,
        )

    def check_contact_damage(self):
        if not self.alive or self.invincible_remaining > 0:
            return

        player_box = self.get_body_box()

        for slime in self.stage.slimes:
            if not slime.alive:
                continue

            if rectangles_overlap(
                player_box,
                slime.get_body_box(),
            ):
                if self.take_damage(
                    SLIME_CONTACT_DAMAGE,
                    source_x=slime.x,
                ):
                    break

    def take_damage(self, damage, source_x=None):
        if (
            not self.alive
            or damage <= 0
            or self.invincible_remaining > 0
        ):
            return False

        self.hp = max(0, self.hp - damage)

        if self.hp == 0:
            self.die()
            return True

        self.invincible_remaining = INVINCIBLE_DURATION

        if source_x is None or source_x == self.x:
            knockback_direction = -self.face_direction
        elif source_x > self.x:
            knockback_direction = -1
        else:
            knockback_direction = 1

        self.cancel_attack()

        self.hurt_remaining = HURT_DURATION
        self.hurt_face_direction = -knockback_direction
        self.face_direction = self.hurt_face_direction

        self.knockback_velocity_x = (
            knockback_direction * KNOCKBACK_SPEED
        )

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

        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False
        self.attack_pressed = False

        self.direction = 0
        self.velocity_y = 0.0

        self.cancel_attack()

        self.motion = "IDLE"
        self.frame = 0.0

    def draw(self):
        if self.alive and self.hurt_remaining > 0:
            self.draw_hurt()
            return

        if self.alive and self.invincible_remaining > 0:
            blink_frame = int(
                self.invincible_remaining / BLINK_INTERVAL
            )

            if blink_frame % 2 == 1:
                return

        if self.attacking:
            index = min(
                int(
                    self.attack_elapsed
                    / ATTACK_DURATION
                    * len(ATTACK_FRAMES)
                ),
                len(ATTACK_FRAMES) - 1,
            )

            rect = ATTACK_FRAMES[index]
            direction = self.attack_direction

        else:
            frames = (
                IDLE_FRAMES if self.motion == "IDLE" else RUN_FRAMES
            )

            rect = frames[int(self.frame)]
            direction = self.face_direction

        self.draw_frame(rect, direction)

    def draw_frame(self, rect, direction):
        left, top, right, bottom = rect

        width = right - left
        height = bottom - top
        source_bottom = self.image.h - bottom

        draw_width = width * PLAYER_DRAW_SCALE
        draw_height = height * PLAYER_DRAW_SCALE
        draw_y = self.y + draw_height / 2

        if direction == 1:
            self.image.clip_draw(
                left, source_bottom,
                width, height,
                self.x, draw_y,
                draw_width, draw_height,
            )
        else:
            self.image.clip_composite_draw(
                left, source_bottom,
                width, height,
                0, "h",
                self.x, draw_y,
                draw_width, draw_height,
            )

    def draw_hurt(self):
        left, top, right, bottom = self.hurt_rect

        width = right - left
        height = bottom - top
        source_bottom = self.hurt_image.h - bottom

        draw_height = 311.0 * PLAYER_DRAW_SCALE
        draw_width = draw_height * width / height
        draw_y = self.y + draw_height / 2

        if self.hurt_face_direction == 1:
            self.hurt_image.clip_draw(
                left, source_bottom,
                width, height,
                self.x, draw_y,
                draw_width, draw_height,
            )
        else:
            self.hurt_image.clip_composite_draw(
                left, source_bottom,
                width, height,
                0, "h",
                self.x, draw_y,
                draw_width, draw_height,
            )