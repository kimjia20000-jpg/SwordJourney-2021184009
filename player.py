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
# (왼쪽, 위쪽, 오른쪽, 아래쪽)
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

        # 이동 애니메이션 상태.
        self.motion = "IDLE"
        self.frame = 0.0

        # 공격 상태.
        self.attacking = False
        self.attack_elapsed = 0.0
        self.attack_direction = 1

        # 이번 공격에서 이미 맞힌 슬라임을 기록한다.
        self.hit_targets = set()

        all_frames = IDLE_FRAMES + RUN_FRAMES + ATTACK_FRAMES

        max_width = max(
            right - left
            for left, top, right, bottom in all_frames
        )

        self.half_width = max_width * PLAYER_DRAW_SCALE / 2

    def handle_event(self, event):
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
        input_direction = (
            int(self.right_pressed) - int(self.left_pressed)
        )

        if input_direction != 0:
            self.face_direction = input_direction

        self.attacking = True
        self.attack_elapsed = 0.0
        self.attack_direction = self.face_direction

        # 새로운 공격이므로 같은 슬라임을 다시 맞힐 수 있다.
        self.hit_targets.clear()

    def update(self, frame_time):
        self.update_movement(frame_time)
        self.update_motion_animation(frame_time)
        self.update_attack(frame_time)
        self.check_attack_hits()

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

        # 공중에서는 공격 진행 상태를 유지하면서 방향만 바꾼다.
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

                # 이후 이 위치에 무기 교체 예약 처리를 추가한다.

        if not self.attacking and self.attack_pressed:
            self.start_attack()

    def get_attack_box(self):
        """현재 공격 구간에 맞는 타격 사각형을 반환한다."""
        if not self.attacking:
            return None

        progress = self.attack_elapsed / ATTACK_DURATION

        # 준비 동작과 마무리 동작에는 타격 판정이 없다.
        if not 0.25 <= progress < 0.75:
            return None

        # 위에서 아래로 베면서 타격 영역도 아래로 이동한다.
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

            # 같은 공격에서 이미 맞은 슬라임은 건너뛴다.
            if slime in self.hit_targets:
                continue

            if rectangles_overlap(
                attack_box,
                slime.get_body_box()
            ):
                if slime.take_damage(BASIC_ATTACK_DAMAGE):
                    self.hit_targets.add(slime)

    def draw(self):
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