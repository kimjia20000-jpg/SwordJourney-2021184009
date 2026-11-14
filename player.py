from pathlib import Path

from pico2d import (
    load_image,
    get_canvas_width,
    draw_rectangle,
    SDL_KEYDOWN,
    SDL_KEYUP,
    SDLK_LEFT,
    SDLK_RIGHT,
    SDLK_SPACE,
    SDLK_a,
)


BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "assets" / "images" / "player_actions.png"

MOVE_SPEED = 200.0
JUMP_SPEED = 550.0
GRAVITY = 1400.0
GROUND_Y = 80

DRAW_SCALE = 160.0 / 311.0

# 원본 이미지의 왼쪽 위 기준 좌표.
# (left, top, right, bottom)
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

IDLE_FPS = 4.0
RUN_FPS = 10.0

# 첫 번째 검의 임시 공격 시간.
# 나중에 무기별 데이터로 옮긴다.
ATTACK_DURATION = 0.48


class Player:
    def __init__(self):
        self.image = load_image(str(IMAGE_PATH))

        if (self.image.w, self.image.h) != (1448, 1086):
            raise ValueError(
                "player_actions.png는 "
                "1448x1086 크기의 원본 포즈 시트를 사용해야 합니다."
            )

        self.x = 400.0
        self.y = float(GROUND_Y)

        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False
        self.attack_pressed = False

        self.direction = 0
        self.face_direction = 1

        self.velocity_y = 0.0
        self.on_ground = True

        # 이동 상태.
        self.motion = "IDLE"
        self.frame = 0.0

        # 이동 상태와 별도로 관리하는 공격 상태.
        self.attacking = False
        self.attack_elapsed = 0.0
        self.attack_direction = 1

        # 공격 이미지까지 화면 안에 들어오도록 여백 계산.
        all_frames = IDLE_FRAMES + RUN_FRAMES + ATTACK_FRAMES
        max_width = max(
            right - left
            for left, top, right, bottom in all_frames
        )
        self.half_width = max_width * DRAW_SCALE / 2

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
                # 반복 KEYDOWN으로 공격을 초기화하지 않는다.
                if not self.attack_pressed:
                    self.attack_pressed = True

                    # 짧게 눌렀다가 같은 루프에서 떼더라도
                    # 공격 한 번은 시작되도록 여기서 처리.
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
                # 현재 공격은 마무리하고 다음 공격만 중단.
                self.attack_pressed = False

    def start_attack(self):
        # 이번 입력 상태를 반영해 공격 시작 방향 결정.
        input_direction = (
            int(self.right_pressed) - int(self.left_pressed)
        )

        if input_direction != 0:
            self.face_direction = input_direction

        self.attacking = True
        self.attack_elapsed = 0.0

        # 현재 공격이 끝날 때까지 이 방향을 유지한다.
        self.attack_direction = self.face_direction

    def update(self, frame_time):
        # 공격 중에도 이동과 점프 계산은 계속한다.
        self.update_movement(frame_time)
        self.update_motion_animation(frame_time)
        self.update_attack(frame_time)

    def update_movement(self, frame_time):
        self.direction = (
            int(self.right_pressed) - int(self.left_pressed)
        )

        if self.direction != 0:
            self.face_direction = self.direction

            # 공중 공격 중에는 입력 방향으로 즉시 베는 방향 변경.
            # 공격 진행 시간은 유지한다.
            if self.attacking and not self.on_ground:
                self.attack_direction = self.direction

        self.x += self.direction * MOVE_SPEED * frame_time

        self.x = max(
            self.half_width,
            min(
                get_canvas_width() - self.half_width,
                self.x
            )
        )

        if not self.on_ground:
            self.y += (
                self.velocity_y * frame_time
                - 0.5 * GRAVITY * frame_time ** 2
            )
            self.velocity_y -= GRAVITY * frame_time

            if self.y <= GROUND_Y:
                self.y = float(GROUND_Y)
                self.velocity_y = 0.0
                self.on_ground = True

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

                # 나중에 무기 교체 예약 처리를
                # 이 위치에 추가한다.

        # 이전 공격이 끝났고 A를 계속 누르면 다음 공격.
        if not self.attacking and self.attack_pressed:
            self.start_attack()

    def draw(self):
        draw_rectangle(
            0, GROUND_Y - 2,
            get_canvas_width() - 1, GROUND_Y
        )

        if self.attacking:
            # 공격은 반복 순환하지 않고
            # 준비 → 베기 → 마무리 순서로 재생한다.
            progress = self.attack_elapsed / ATTACK_DURATION

            frame_index = min(
                int(progress * len(ATTACK_FRAMES)),
                len(ATTACK_FRAMES) - 1
            )

            frame_rect = ATTACK_FRAMES[frame_index]
            draw_direction = self.attack_direction

        else:
            if self.motion == "IDLE":
                frames = IDLE_FRAMES
            else:
                frames = RUN_FRAMES

            frame_rect = frames[int(self.frame)]
            draw_direction = self.face_direction

        self.draw_frame(frame_rect, draw_direction)

    def draw_frame(self, frame_rect, direction):
        left, top, right, bottom = frame_rect

        source_width = right - left
        source_height = bottom - top
        source_bottom = self.image.h - bottom

        draw_width = source_width * DRAW_SCALE
        draw_height = source_height * DRAW_SCALE
        draw_y = self.y + draw_height / 2

        if direction == 1:
            self.image.clip_draw(
                left, source_bottom,
                source_width, source_height,
                self.x, draw_y,
                draw_width, draw_height
            )

        else:
            self.image.clip_composite_draw(
                left, source_bottom,
                source_width, source_height,
                0, 'h',
                self.x, draw_y,
                draw_width, draw_height
            )