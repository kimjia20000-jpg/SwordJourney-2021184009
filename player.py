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
IMAGE_PATH = BASE_DIR / "assets" / "images" / "player_preview.png"

# 조작감을 확인하면서 조정할 임시 수치.
MOVE_SPEED = 200.0          # 픽셀/초
JUMP_SPEED = 550.0          # 점프 시작 시 위쪽 속도
GRAVITY = 1400.0           # 픽셀/초²
GROUND_Y = 80              # 바닥 높이


class Player:
    def __init__(self):
        self.image = load_image(str(IMAGE_PATH))

        self.draw_height = 160
        self.draw_width = round(
            self.image.w * self.draw_height / self.image.h
        )

        # 위치는 이미지의 중심 좌표.
        self.x = 400.0
        self.y = GROUND_Y + self.draw_height / 2

        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False

        self.direction = 0
        self.face_direction = 1

        # 위쪽이 양수, 아래쪽이 음수.
        self.velocity_y = 0.0
        self.on_ground = True

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_LEFT:
                self.left_pressed = True

            elif event.key == SDLK_RIGHT:
                self.right_pressed = True

            elif event.key == SDLK_SPACE:
                # 길게 누를 때 발생하는 반복 입력으로
                # 점프가 다시 실행되지 않게 한다.
                if not self.jump_pressed:
                    self.jump_pressed = True

                    # 바닥에 있을 때만 점프 시작.
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
        # 1. 지상과 공중 모두 같은 방식으로 좌우 이동.
        self.direction = (
            int(self.right_pressed) - int(self.left_pressed)
        )

        if self.direction != 0:
            self.face_direction = self.direction

        self.x += self.direction * MOVE_SPEED * frame_time

        # 2. 좌우 화면 경계 제한.
        half_width = self.draw_width / 2
        self.x = max(
            half_width,
            min(get_canvas_width() - half_width, self.x)
        )

        # 3. 공중에서는 중력에 따라 위치와 수직 속도 변경.
        if not self.on_ground:
            self.y += (
                self.velocity_y * frame_time
                - 0.5 * GRAVITY * frame_time ** 2
            )
            self.velocity_y -= GRAVITY * frame_time

            # 4. 이미지 아래쪽이 바닥에 닿으면 착지.
            ground_center_y = GROUND_Y + self.draw_height / 2

            if self.y <= ground_center_y:
                self.y = ground_center_y
                self.velocity_y = 0.0
                self.on_ground = True

    def draw(self):
        # 이번 단계의 착지 확인용 바닥선.
        # 배경 객체를 만들 때 별도 파일로 옮길 예정.
        draw_rectangle(
            0, GROUND_Y - 2,
            get_canvas_width() - 1, GROUND_Y
        )

        if self.face_direction == 1:
            self.image.draw(
                self.x,
                self.y,
                self.draw_width,
                self.draw_height
            )

        else:
            self.image.clip_composite_draw(
                0, 0,
                self.image.w, self.image.h,
                0, 'h',
                self.x, self.y,
                self.draw_width, self.draw_height
            )