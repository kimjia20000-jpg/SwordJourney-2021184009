from pathlib import Path

from pico2d import (
    load_image,
    get_canvas_width,
    SDL_KEYDOWN,
    SDL_KEYUP,
    SDLK_LEFT,
    SDLK_RIGHT,
)


BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "assets" / "images" / "player_preview.png"

# 이동 속도: 초당 200픽셀. 조작감을 확인하며 조정할 임시 값.
MOVE_SPEED = 200.0


class Player:
    def __init__(self):
        self.x = 400.0
        self.y = 300.0

        self.image = load_image(str(IMAGE_PATH))

        self.draw_height = 160
        self.draw_width = round(
            self.image.w * self.draw_height / self.image.h
        )

        # 키를 누르고 있는지 각각 기억한다.
        self.left_pressed = False
        self.right_pressed = False

        # 이동 방향: -1은 왼쪽, 0은 정지, 1은 오른쪽.
        self.direction = 0

        # 마지막으로 바라본 방향. 기본 이미지는 오른쪽을 본다.
        self.face_direction = 1

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_LEFT:
                self.left_pressed = True

            elif event.key == SDLK_RIGHT:
                self.right_pressed = True

        elif event.type == SDL_KEYUP:
            if event.key == SDLK_LEFT:
                self.left_pressed = False

            elif event.key == SDLK_RIGHT:
                self.right_pressed = False

    def update(self, frame_time):
        # 오른쪽만 누르면 1, 왼쪽만 누르면 -1.
        # 둘 다 누르거나 둘 다 떼면 0.
        self.direction = (
            int(self.right_pressed) - int(self.left_pressed)
        )

        if self.direction != 0:
            self.face_direction = self.direction

        # 이동 거리 = 방향 × 초당 이동 속도 × 경과 시간.
        self.x += self.direction * MOVE_SPEED * frame_time

        # 이미지의 절반 너비만큼 여백을 두어 화면 밖으로 나가지 않게 한다.
        half_width = self.draw_width / 2
        self.x = max(
            half_width,
            min(get_canvas_width() - half_width, self.x)
        )

    def draw(self):
        if self.face_direction == 1:
            self.image.draw(
                self.x,
                self.y,
                self.draw_width,
                self.draw_height
            )

        else:
            # 원본 이미지 전체를 선택해서 좌우 반전한다.
            self.image.clip_composite_draw(
                0, 0,
                self.image.w, self.image.h,
                0, 'h',
                self.x, self.y,
                self.draw_width, self.draw_height
            )