import math
import random

from pico2d import draw_rectangle
from settings import SLIME_WIDTH, SLIME_HEIGHT


SLIME_MOVE_SPEED = 65.0
SLIME_JUMP_SPEED = 210.0
SLIME_GRAVITY = 900.0

WAIT_TIME_MIN = 0.35
WAIT_TIME_MAX = 0.65

SQUASH_TIME = 0.16
LAND_TIME = 0.12

SLIME_MAX_HP = 30
HIT_FLASH_TIME = 0.18

HP_BAR_WIDTH = 40
HP_BAR_HEIGHT = 5
HP_BAR_GAP = 7


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

        # y는 몸 아래쪽 기준 높이.
        self.y = float(platform.top)
        self.velocity_y = 0.0
        self.velocity_x = 0.0

        self.state = "WAIT"
        self.state_time = 0.0
        self.wait_duration = random.uniform(
            0.0,
            WAIT_TIME_MAX
        )

        # 체력과 생존 상태.
        self.max_hp = SLIME_MAX_HP
        self.hp = self.max_hp
        self.alive = True

        # 첫 피격 전에는 체력바를 숨긴다.
        self.show_health_bar = False
        self.hit_flash_remaining = 0.0

    def take_damage(self, damage):
        """피해를 적용하고 실제로 적용됐는지 반환한다."""
        if not self.alive or damage <= 0:
            return False

        self.hp = max(0, self.hp - damage)

        self.show_health_bar = True
        self.hit_flash_remaining = HIT_FLASH_TIME

        if self.hp == 0:
            self.alive = False

        return True

    def get_body_box(self):
        # 변형 연출 때문에 피격 범위가 계속 바뀌지 않도록
        # 기본 크기를 기준으로 판정한다.
        return (
            self.x - self.width / 2,
            self.y,
            self.x + self.width / 2,
            self.y + self.height
        )

    def start_jump(self):
        flight_time = (
            2 * SLIME_JUMP_SPEED / SLIME_GRAVITY
        )

        expected_distance = self.speed * flight_time

        if self.direction == 1:
            available_distance = self.right_limit - self.x
        else:
            available_distance = self.x - self.left_limit

        if available_distance < expected_distance:
            self.direction *= -1

        if self.direction == 1:
            available_distance = self.right_limit - self.x
        else:
            available_distance = self.x - self.left_limit

        jump_speed_x = min(
            self.speed,
            max(0.0, available_distance) / flight_time
        )

        self.velocity_x = self.direction * jump_speed_x
        self.velocity_y = SLIME_JUMP_SPEED

        self.state = "AIR"
        self.state_time = 0.0

    def update(self, frame_time):
        if not self.alive:
            return

        self.hit_flash_remaining = max(
            0.0,
            self.hit_flash_remaining - frame_time
        )

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

            self.x = max(
                self.left_limit,
                min(self.right_limit, self.x)
            )

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

            width_scale = 1.0 + 0.15 * progress
            height_scale = 1.0 - 0.18 * progress

        elif self.state == "AIR":
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

            squash = math.sin(math.pi * progress)

            width_scale = 1.0 + 0.12 * squash
            height_scale = 1.0 - 0.15 * squash

        return (
            self.width * width_scale,
            self.height * height_scale
        )

    def draw(self):
        if not self.alive:
            return

        # 피격 깜빡임은 시각 효과이며 별도의 무적 시간은 아니다.
        if self.hit_flash_remaining > 0:
            if int(self.hit_flash_remaining / 0.045) % 2 == 1:
                return

        left = 136
        top = 171
        right = 1311
        bottom = 987

        source_width = right - left
        source_height = bottom - top
        source_bottom = self.image.h - bottom

        draw_width, draw_height = self.get_draw_size()
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

    def draw_health_bar(self):
        if not self.alive or not self.show_health_bar:
            return

        left = round(self.x - HP_BAR_WIDTH / 2)

        # 몸이 늘어나는 연출에도 체력바가 겹치지 않도록
        # 최대 표시 높이 위에 배치한다.
        bottom = round(
            self.y + self.height * 1.12 + HP_BAR_GAP
        )

        right = left + HP_BAR_WIDTH - 1
        top = bottom + HP_BAR_HEIGHT - 1

        # 어두운 테두리.
        draw_rectangle(
            left - 1,
            bottom - 1,
            right + 1,
            top + 1,
            20, 25, 20,
            filled=True
        )

        # 체력이 비어 있는 부분.
        draw_rectangle(
            left,
            bottom,
            right,
            top,
            70, 70, 70,
            filled=True
        )

        # 남은 체력에 비례하는 초록색 영역.
        fill_width = round(
            HP_BAR_WIDTH * self.hp / self.max_hp
        )

        if fill_width > 0:
            draw_rectangle(
                left,
                bottom,
                left + fill_width - 1,
                top,
                70, 220, 80,
                filled=True
            )