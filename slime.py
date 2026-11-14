import math
import random

from settings import SLIME_WIDTH, SLIME_HEIGHT


# 슬라임 움직임을 확인하면서 조정할 임시 수치.
SLIME_MOVE_SPEED = 65.0
SLIME_JUMP_SPEED = 210.0
SLIME_GRAVITY = 900.0

# 착지 후 다음 점프까지 기다리는 시간.
WAIT_TIME_MIN = 0.35
WAIT_TIME_MAX = 0.65

# 점프 직전 움츠리는 시간.
SQUASH_TIME = 0.16

# 착지 직후 눌리는 시간.
LAND_TIME = 0.12


class Slime:
    def __init__(
        self,
        image,
        platform,
        x,
        direction=1,
        patrol_left=None,
        patrol_right=None
    ):
        self.image = image
        self.platform = platform

        self.width = SLIME_WIDTH
        self.height = SLIME_HEIGHT

        self.direction = direction
        self.speed = SLIME_MOVE_SPEED

        # 몸이 옆으로 늘어나는 연출까지 고려한 여백.
        margin = self.width * 1.15 / 2 + 4

        self.left_limit = platform.left + margin
        self.right_limit = platform.right - margin

        if patrol_left is not None:
            self.left_limit = max(
                self.left_limit,
                patrol_left
            )

        if patrol_right is not None:
            self.right_limit = min(
                self.right_limit,
                patrol_right
            )

        if self.left_limit > self.right_limit:
            raise ValueError("슬라임의 순찰 구역이 너무 좁습니다.")

        self.x = max(
            self.left_limit,
            min(self.right_limit, x)
        )

        # y는 슬라임 몸의 아래쪽 높이.
        self.y = float(platform.top)
        self.velocity_y = 0.0

        # WAIT: 대기, SQUASH: 점프 준비,
        # AIR: 공중, LAND: 착지.
        self.state = "WAIT"
        self.state_time = 0.0

        # 개체마다 첫 점프 시점을 다르게 한다.
        self.wait_duration = random.uniform(0.0, WAIT_TIME_MAX)

        # 공중에서 사용할 가로 속도.
        self.velocity_x = 0.0

    def start_jump(self):
        # 같은 높이로 돌아오는 예상 비행 시간.
        flight_time = (
            2 * SLIME_JUMP_SPEED / SLIME_GRAVITY
        )

        expected_distance = self.speed * flight_time

        if self.direction == 1:
            available_distance = self.right_limit - self.x
        else:
            available_distance = self.x - self.left_limit

        # 앞으로 충분히 뛸 공간이 없으면 방향 변경.
        if available_distance < expected_distance:
            self.direction *= -1

        if self.direction == 1:
            available_distance = self.right_limit - self.x
        else:
            available_distance = self.x - self.left_limit

        # 순찰 구역이 좁으면 이번 점프의 가로 속도를 줄인다.
        jump_speed_x = min(
            self.speed,
            max(0.0, available_distance) / flight_time
        )

        self.velocity_x = self.direction * jump_speed_x
        self.velocity_y = SLIME_JUMP_SPEED

        self.state = "AIR"
        self.state_time = 0.0

    def update(self, frame_time):
        self.state_time += frame_time

        if self.state == "WAIT":
            if self.state_time >= self.wait_duration:
                self.state = "SQUASH"
                self.state_time = 0.0

        elif self.state == "SQUASH":
            if self.state_time >= SQUASH_TIME:
                self.start_jump()

        elif self.state == "AIR":
            self.x += self.velocity_x * frame_time

            self.y += (
                self.velocity_y * frame_time
                - 0.5 * SLIME_GRAVITY * frame_time ** 2
            )

            self.velocity_y -= SLIME_GRAVITY * frame_time

            # 수치 오차가 있어도 순찰 구역 밖으로 나가지 않게 제한.
            self.x = max(
                self.left_limit,
                min(self.right_limit, self.x)
            )

            # 자신이 배치된 발판에 착지.
            if (
                self.velocity_y <= 0
                and self.y <= self.platform.top
            ):
                self.y = float(self.platform.top)
                self.velocity_y = 0.0
                self.velocity_x = 0.0

                self.state = "LAND"
                self.state_time = 0.0

        elif self.state == "LAND":
            if self.state_time >= LAND_TIME:
                self.state = "WAIT"
                self.state_time = 0.0

                self.wait_duration = random.uniform(
                    WAIT_TIME_MIN,
                    WAIT_TIME_MAX
                )

    def get_draw_size(self):
        width_scale = 1.0
        height_scale = 1.0

        if self.state == "SQUASH":
            progress = min(
                self.state_time / SQUASH_TIME,
                1.0
            )

            # 점프 직전 점점 납작해진다.
            width_scale = 1.0 + 0.15 * progress
            height_scale = 1.0 - 0.18 * progress

        elif self.state == "AIR":
            # 빠르게 상승하거나 떨어질 때 조금 길어진다.
            # 최고점에서는 원래 비율에 가까워진다.
            stretch = min(
                abs(self.velocity_y) / SLIME_JUMP_SPEED,
                1.0
            )

            width_scale = 1.0 - 0.06 * stretch
            height_scale = 1.0 + 0.12 * stretch

        elif self.state == "LAND":
            progress = min(
                self.state_time / LAND_TIME,
                1.0
            )

            # 착지 순간 살짝 눌렸다가 원래 모습으로 복귀.
            squash = math.sin(math.pi * progress)

            width_scale = 1.0 + 0.12 * squash
            height_scale = 1.0 - 0.15 * squash

        return (
            self.width * width_scale,
            self.height * height_scale
        )

    def draw(self):
        # 원본 이미지의 실제 슬라임 영역.
        left = 136
        top = 171
        right = 1311
        bottom = 987

        source_width = right - left
        source_height = bottom - top
        source_bottom = self.image.h - bottom

        draw_width, draw_height = self.get_draw_size()

        # 크기가 변해도 몸 아래쪽의 높이는 유지.
        draw_y = self.y + draw_height / 2

        if self.direction == 1:
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