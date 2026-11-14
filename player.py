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


BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "assets" / "images" / "player_actions.png"

# 이동과 점프 설정.
MOVE_SPEED = 200.0
JUMP_SPEED = 550.0
GRAVITY = 1400.0

# 모든 프레임에 같은 배율 적용.
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
ATTACK_DURATION = 0.48


class Player:
    def __init__(self, stage):
        self.stage = stage

        self.image = load_image(str(IMAGE_PATH))

        if (self.image.w, self.image.h) != (1448, 1086):
            raise ValueError(
                "player_actions.png는 "
                "1448x1086 크기의 원본 포즈 시트를 사용해야 합니다."
            )

        # x: 캐릭터 중심, y: 발 기준 높이.
        self.x = self.stage.spawn_x
        self.y = self.stage.spawn_y

        # 착지 판정은 검을 제외한 발 주변 영역으로 처리.
        self.foot_half_width = 14.0

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

        # 이동과 별도로 관리하는 공격 상태.
        self.attacking = False
        self.attack_elapsed = 0.0
        self.attack_direction = 1

        # 이미지 전체가 화면 안에 들어오도록 경계 여백 계산.
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
                # 키를 길게 눌러도 자동 재점프하지 않게 처리.
                if not self.jump_pressed:
                    self.jump_pressed = True

                    if self.on_ground:
                        self.velocity_y = JUMP_SPEED
                        self.on_ground = False

            elif event.key == SDLK_a:
                # 반복 KEYDOWN으로 현재 공격을 초기화하지 않는다.
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
                # 현재 공격은 마무리하고 연속 공격만 중단.
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

    def update(self, frame_time):
        # 공격 중에도 이동과 중력 계산을 계속한다.
        self.update_movement(frame_time)
        self.update_motion_animation(frame_time)
        self.update_attack(frame_time)

    def update_movement(self, frame_time):
        self.direction = (
            int(self.right_pressed) - int(self.left_pressed)
        )

        # 1. 좌우 이동.
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

        # 2. 중력 적용 전 발 높이 저장.
        old_y = self.y

        # 발판 위에서도 계산한다.
        # 착지 처리로 발판 위에 유지하고,
        # 가장자리로 나가면 자연스럽게 떨어지게 한다.
        self.y += (
            self.velocity_y * frame_time
            - 0.5 * GRAVITY * frame_time ** 2
        )
        self.velocity_y -= GRAVITY * frame_time

        self.on_ground = False

        # 3. 하강 중에만 발판 윗면과 충돌.
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

        # 4. 공중 공격 중에는 방향키로 즉시 공격 방향 변경.
        # 공격 진행 시간과 점프 속도는 유지한다.
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
            # 점프 전용 이미지가 없어 임시 공중 자세 사용.
            self.frame = 1.0

    def update_attack(self, frame_time):
        if self.attacking:
            self.attack_elapsed += frame_time

            if self.attack_elapsed >= ATTACK_DURATION:
                self.attacking = False
                self.attack_elapsed = 0.0

                # 이후 공격 종료 시 무기 교체 예약을 처리할 위치.

        # A를 계속 누르고 있다면 다음 공격 시작.
        if not self.attacking and self.attack_pressed:
            self.start_attack()

    def draw(self):
        if self.attacking:
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

        # 위쪽 기준 좌표를 pico2d의 아래쪽 기준으로 변환.
        source_bottom = self.image.h - bottom

        draw_width = source_width * DRAW_SCALE
        draw_height = source_height * DRAW_SCALE

        # 프레임 높이가 달라도 아래쪽을 발 높이에 맞춘다.
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