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
)


BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "assets" / "images" / "player_actions.png"

MOVE_SPEED = 200.0
JUMP_SPEED = 550.0
GRAVITY = 1400.0
GROUND_Y = 80

# 모든 동작에 같은 배율을 적용한다.
DRAW_SCALE = 160.0 / 311.0

# 원본 이미지의 왼쪽 위를 기준으로 한 프레임 영역.
# (left, top, right, bottom)
# 각 캐릭터 주변의 빈 공간을 제외한 좌표다.
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

# 초당 애니메이션 프레임 진행 수.
IDLE_FPS = 4.0
RUN_FPS = 10.0


class Player:
    def __init__(self):
        self.image = load_image(str(IMAGE_PATH))

        if (self.image.w, self.image.h) != (1448, 1086):
            raise ValueError(
                "player_actions.png는 "
                "1448x1086 크기의 원본 포즈 시트를 사용해야 합니다."
            )

        self.x = 400.0

        # 이번 단계부터 y는 이미지 중심이 아니라 발 기준 높이.
        self.y = float(GROUND_Y)

        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False

        self.direction = 0
        self.face_direction = 1

        self.velocity_y = 0.0
        self.on_ground = True

        # 이동 상태와 애니메이션 진행 위치.
        self.motion = "IDLE"
        self.frame = 0.0

        # 모든 현재 프레임이 화면 안에 들어오도록 여백 계산.
        all_frames = IDLE_FRAMES + RUN_FRAMES
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

        elif event.type == SDL_KEYUP:
            if event.key == SDLK_LEFT:
                self.left_pressed = False

            elif event.key == SDLK_RIGHT:
                self.right_pressed = False

            elif event.key == SDLK_SPACE:
                self.jump_pressed = False

    def update(self, frame_time):
        # 1. 좌우 이동.
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

        # 2. 점프와 착지.
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

        # 3. 이동 상태 결정.
        if not self.on_ground:
            next_motion = "AIR"
        elif self.direction != 0:
            next_motion = "RUN"
        else:
            next_motion = "IDLE"

        # 상태가 바뀔 때만 애니메이션을 처음부터 시작.
        if next_motion != self.motion:
            self.motion = next_motion
            self.frame = 0.0

        # 4. 실제 경과 시간에 따라 애니메이션 진행.
        if self.motion == "IDLE":
            self.frame = (
                self.frame + IDLE_FPS * frame_time
            ) % len(IDLE_FRAMES)

        elif self.motion == "RUN":
            self.frame = (
                self.frame + RUN_FPS * frame_time
            ) % len(RUN_FRAMES)

        else:
            # 점프 전용 이미지가 없으므로
            # 공중에서는 달리기 시트의 한 자세를 임시 사용.
            self.frame = 1.0

    def draw(self):
        draw_rectangle(
            0, GROUND_Y - 2,
            get_canvas_width() - 1, GROUND_Y
        )

        if self.motion == "IDLE":
            frames = IDLE_FRAMES
        else:
            frames = RUN_FRAMES

        left, top, right, bottom = frames[int(self.frame)]

        source_width = right - left
        source_height = bottom - top

        # 이미지 좌표의 위쪽 기준을
        # pico2d의 아래쪽 기준으로 변환.
        source_bottom = self.image.h - bottom

        draw_width = source_width * DRAW_SCALE
        draw_height = source_height * DRAW_SCALE

        # 프레임 높이가 달라도 아래쪽을 발 기준 높이에 맞춘다.
        draw_y = self.y + draw_height / 2

        if self.face_direction == 1:
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