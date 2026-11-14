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

# 원본 이미지의 왼쪽 위 기준 좌표.
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

# 전투 테스트 설정.
BASIC_ATTACK_DAMAGE = 10
PLAYER_MAX_HP = 100
SLIME_CONTACT_DAMAGE = 10

INVINCIBLE_DURATION = 1.0
BLINK_INTERVAL = 0.08

# 검과 머리카락을 제외한 몸 주변의 접촉 판정.
# 현재 캐릭터 크기에 맞춰 조정할 수 있는 값.
PLAYER_BODY_HALF_WIDTH = 16.0
PLAYER_BODY_HEIGHT = 72.0


def rectangles_overlap(a, b):
    """두 사각형이 겹치는지 확인한다."""
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

        if (self.image.w, self.image.h) != (1448, 1086):
            raise ValueError(
                "player_actions.png는 "
                "1448x1086 크기의 원본 이미지를 사용해야 합니다."
            )

        # x는 캐릭터 중심, y는 발 기준 높이.
        self.x = self.stage.spawn_x
        self.y = self.stage.spawn_y
        self.foot_half_width = PLAYER_FOOT_HALF_WIDTH

        # 입력 상태.
        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False
        self.attack_pressed = False

        self.direction = 0
        self.face_direction = 1

        # 점프 상태.
        self.velocity_y = 0.0
        self.on_ground = True

        # 이동 애니메이션.
        self.motion = "IDLE"
        self.frame = 0.0

        # 공격 상태.
        self.attacking = False
        self.attack_elapsed = 0.0
        self.attack_direction = 1
        self.hit_targets = set()

        # 체력과 피격 상태.
        self.max_hp = PLAYER_MAX_HP
        self.hp = self.max_hp
        self.alive = True
        self.invincible_remaining = 0.0

        all_frames = IDLE_FRAMES + RUN_FRAMES + ATTACK_FRAMES

        max_width = max(
            right - left
            for left, top, right, bottom in all_frames
        )

        self.half_width = max_width * PLAYER_DRAW_SCALE / 2

    def handle_event(self, event):
        if not self.alive:
            return

        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_LEFT:
                self.left_pressed = True

            elif event.key == SDLK_RIGHT:
                self.right_pressed = True

            elif event.key == SDLK_SPACE:
                if not self.jump_pressed:
                    self.jump_pressed = True

                    if self.on_ground:
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
        if not self.alive:
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

    def update(self, frame_time):
        if not self.alive:
            return

        # 무적 시간은 실제 경과 시간에 따라 감소.
        self.invincible_remaining = max(
            0.0,
            self.invincible_remaining - frame_time
        )

        self.update_movement(frame_time)
        self.update_motion_animation(frame_time)
        self.update_attack(frame_time)

        # 플레이어의 공격을 먼저 처리한다.
        self.check_attack_hits()

        # 공격으로 처치되지 않은 슬라임만 접촉 피해를 준다.
        self.check_contact_damage()

    def update_movement(self, frame_time):
        self.direction = (
            int(self.right_pressed) - int(self.left_pressed)
        )

        if self.direction != 0:
            self.face_direction = self.direction

        self.x += self.direction * MOVE_SPEED * frame_time

        self.x = max(
            self.half_width,
            min(
                get_canvas_width() - self.half_width,
                self.x
            )
        )

        old_y = self.y

        self.y += (
            self.velocity_y * frame_time
            - 0.5 * GRAVITY * frame_time ** 2
        )

        self.velocity_y -= GRAVITY * frame_time
        self.on_ground = False

        if self.velocity_y <= 0:
            landing = self.stage.find_landing(
                self.x,
                self.foot_half_width,
                old_y,
                self.y
            )

            if landing is not None:
                self.y = float(landing.top)
                self.velocity_y = 0.0
                self.on_ground = True

        # 공중 공격 중에는 방향키로 즉시 회전.
        if (
            self.attacking
            and not self.on_ground
            and self.direction != 0
        ):
            self.attack_direction = self.direction

    def update_motion_animation(self, frame_time):
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
                self.frame + IDLE_FPS * frame_time
            ) % len(IDLE_FRAMES)

        elif self.motion == "RUN":
            self.frame = (
                self.frame + RUN_FPS * frame_time
            ) % len(RUN_FRAMES)

        else:
            self.frame = 1.0

    def update_attack(self, frame_time):
        if self.attacking:
            self.attack_elapsed += frame_time

            if self.attack_elapsed >= ATTACK_DURATION:
                self.attacking = False
                self.attack_elapsed = 0.0

                # 이후 무기 교체 예약을 처리할 위치.

        if not self.attacking and self.attack_pressed:
            self.start_attack()

    def get_attack_box(self):
        if not self.attacking:
            return None

        progress = self.attack_elapsed / ATTACK_DURATION

        # 준비와 마무리 구간에는 타격 판정이 없다.
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
            self.y + top_y
        )

    def check_attack_hits(self):
        attack_box = self.get_attack_box()

        if attack_box is None:
            return

        for slime in self.stage.slimes:
            if not slime.alive:
                continue

            if slime in self.hit_targets:
                continue

            if rectangles_overlap(
                attack_box,
                slime.get_body_box()
            ):
                if slime.take_damage(BASIC_ATTACK_DAMAGE):
                    self.hit_targets.add(slime)

    def get_body_box(self):
        """플레이어 몸의 접촉 판정 영역."""
        return (
            self.x - PLAYER_BODY_HALF_WIDTH,
            self.y,
            self.x + PLAYER_BODY_HALF_WIDTH,
            self.y + PLAYER_BODY_HEIGHT
        )

    def check_contact_damage(self):
        if not self.alive:
            return

        if self.invincible_remaining > 0:
            return

        body_box = self.get_body_box()

        for slime in self.stage.slimes:
            if not slime.alive:
                continue

            if rectangles_overlap(
                body_box,
                slime.get_body_box()
            ):
                if self.take_damage(SLIME_CONTACT_DAMAGE):
                    # 여러 마리와 겹쳐도 이번에는 한 번만 피해.
                    break

    def take_damage(self, damage):
        if not self.alive or damage <= 0:
            return False

        if self.invincible_remaining > 0:
            return False

        self.hp = max(0, self.hp - damage)

        if self.hp == 0:
            self.die()

        else:
            self.invincible_remaining = INVINCIBLE_DURATION

        return True

    def die(self):
        self.alive = False
        self.invincible_remaining = 0.0

        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False
        self.attack_pressed = False

        self.direction = 0
        self.velocity_y = 0.0

        self.attacking = False
        self.attack_elapsed = 0.0
        self.hit_targets.clear()

        self.motion = "IDLE"
        self.frame = 0.0

    def draw(self):
        # 무적 시간에는 캐릭터를 번갈아 숨겨 깜빡임 표현.
        if self.alive and self.invincible_remaining > 0:
            blink_phase = int(
                self.invincible_remaining / BLINK_INTERVAL
            )

            if blink_phase % 2 == 1:
                return

        if self.attacking:
            progress = self.attack_elapsed / ATTACK_DURATION

            frame_index = min(
                int(progress * len(ATTACK_FRAMES)),
                len(ATTACK_FRAMES) - 1
            )

            frame_rect = ATTACK_FRAMES[frame_index]
            direction = self.attack_direction

        else:
            if self.motion == "IDLE":
                frames = IDLE_FRAMES
            else:
                frames = RUN_FRAMES

            frame_rect = frames[int(self.frame)]
            direction = self.face_direction

        self.draw_frame(frame_rect, direction)

    def draw_frame(self, frame_rect, direction):
        left, top, right, bottom = frame_rect

        source_width = right - left
        source_height = bottom - top
        source_bottom = self.image.h - bottom

        draw_width = source_width * PLAYER_DRAW_SCALE
        draw_height = source_height * PLAYER_DRAW_SCALE
        draw_y = self.y + draw_height / 2

        if direction == 1:
            self.image.clip_draw(
                left,
                source_bottom,
                source_width,
                source_height,
                self.x,
                draw_y,
                draw_width,
                draw_height
            )

        else:
            self.image.clip_composite_draw(
                left,
                source_bottom,
                source_width,
                source_height,
                0,
                'h',
                self.x,
                draw_y,
                draw_width,
                draw_height
            )