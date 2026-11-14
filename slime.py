import math
import random
from pathlib import Path

from pico2d import draw_rectangle, load_image
from settings import SLIME_WIDTH, SLIME_HEIGHT


SLIME_MOVE_SPEED = 65.0
SLIME_JUMP_SPEED = 210.0
SLIME_GRAVITY = 900.0

WAIT_TIME_MIN = 0.35
WAIT_TIME_MAX = 0.65

SQUASH_TIME = 0.16
LAND_TIME = 0.12

SLIME_MAX_HP = 30

# 피격 자세를 유지하는 최소 시간.
HURT_TIME = 0.20

# 수평 넉백과 위로 튀는 정도.
KNOCKBACK_SPEED = 220.0
KNOCKBACK_DECELERATION = 1100.0
KNOCKBACK_UP_SPEED = 120.0

HP_BAR_WIDTH = 40
HP_BAR_HEIGHT = 5
HP_BAR_GAP = 7

HURT_IMAGE_PATH = (
    Path(__file__).resolve().parent
    / "assets"
    / "images"
    / "slime_hurt.png"
)


class Slime:
    # 모든 슬라임이 같은 피격 이미지를 공유한다.
    _hurt_image = None

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

        if Slime._hurt_image is None:
            Slime._hurt_image = load_image(str(HURT_IMAGE_PATH))

        self.hurt_image = Slime._hurt_image

        self.width = SLIME_WIDTH
        self.height = SLIME_HEIGHT

        self.direction = direction
        self.hurt_direction = direction
        self.speed = SLIME_MOVE_SPEED

        # 몸이 늘어나는 연출까지 고려한 여백.
        margin = self.width * 1.15 / 2 + 4

        self.left_limit = platform.left + margin
        self.right_limit = platform.right - margin

        if patrol_left is not None:
            self.left_limit = max(self.left_limit, patrol_left)

        if patrol_right is not None:
            self.right_limit = min(self.right_limit, patrol_right)

        if self.left_limit > self.right_limit:
            raise ValueError("슬라임의 순찰 구역이 너무 좁습니다.")

        self.x = max(self.left_limit, min(self.right_limit, x))

        # y는 몸 아래쪽 높이.
        self.y = float(platform.top)

        self.velocity_y = 0.0
        self.velocity_x = 0.0

        self.state = "WAIT"
        self.state_time = 0.0
        self.wait_duration = random.uniform(0.0, WAIT_TIME_MAX)

        self.max_hp = SLIME_MAX_HP
        self.hp = self.max_hp
        self.alive = True

        self.show_health_bar = False

    def take_damage(self, damage, attack_direction=None):
        """피해와 넉백을 적용한다. 피격 중에도 다시 맞을 수 있다."""
        if not self.alive or damage <= 0:
            return False

        self.hp = max(0, self.hp - damage)
        self.show_health_bar = True

        if self.hp == 0:
            self.alive = False
            self.velocity_x = 0.0
            self.velocity_y = 0.0
            return True

        # 방향을 전달하지 않은 기존 호출에도 대응.
        if attack_direction is None:
            attack_direction = -self.direction

        self.hurt_direction = 1 if attack_direction >= 0 else -1
        self.direction = self.hurt_direction

        self.velocity_x = self.hurt_direction * KNOCKBACK_SPEED
        self.velocity_y = KNOCKBACK_UP_SPEED

        # 기존 점프를 중단하고 피격 상태로 전환한다.
        self.state = "HURT"
        self.state_time = 0.0

        return True

    def get_body_box(self):
        # 이미지 변형과 관계없이 기본 크기로 충돌 판정.
        return (
            self.x - self.width / 2,
            self.y,
            self.x + self.width / 2,
            self.y + self.height
        )

    def start_jump(self):
        flight_time = 2 * SLIME_JUMP_SPEED / SLIME_GRAVITY
        expected_distance = self.speed * flight_time

        if self.direction == 1:
            available = self.right_limit - self.x
        else:
            available = self.x - self.left_limit

        if available < expected_distance:
            self.direction *= -1

        if self.direction == 1:
            available = self.right_limit - self.x
        else:
            available = self.x - self.left_limit

        speed = min(
            self.speed,
            max(0.0, available) / flight_time
        )

        self.velocity_x = self.direction * speed
        self.velocity_y = SLIME_JUMP_SPEED

        self.state = "AIR"
        self.state_time = 0.0

    def clamp_x(self):
        """이동과 넉백 모두 순찰 구역 안으로 제한한다."""
        limited = max(
            self.left_limit,
            min(self.right_limit, self.x)
        )

        if limited != self.x:
            self.velocity_x = 0.0

        self.x = limited

    def update_vertical(self, dt):
        """중력을 적용하고 자기 발판에 착지했는지 반환한다."""
        self.y += (
            self.velocity_y * dt
            - 0.5 * SLIME_GRAVITY * dt ** 2
        )

        self.velocity_y -= SLIME_GRAVITY * dt

        if self.velocity_y <= 0 and self.y <= self.platform.top:
            self.y = float(self.platform.top)
            self.velocity_y = 0.0
            return True

        return False

    def update(self, frame_time):
        if not self.alive:
            return

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
            self.clamp_x()

            if self.update_vertical(frame_time):
                self.enter_land()

        elif self.state == "HURT":
            # 처음에는 빠르게 밀리고 점차 감속한다.
            speed = abs(self.velocity_x)

            if speed > 0:
                move_time = min(
                    frame_time,
                    speed / KNOCKBACK_DECELERATION
                )

                distance = (
                    speed * move_time
                    - 0.5 * KNOCKBACK_DECELERATION * move_time ** 2
                )

                self.x += self.hurt_direction * distance

                speed = max(
                    0.0,
                    speed - KNOCKBACK_DECELERATION * move_time
                )

                self.velocity_x = self.hurt_direction * speed

            self.clamp_x()

            # 공중에서 맞았어도 발판까지 자연스럽게 내려온다.
            landed = self.update_vertical(frame_time)

            if landed and self.state_time >= HURT_TIME:
                self.enter_land()

        elif self.state == "LAND":
            if self.state_time >= LAND_TIME:
                self.state = "WAIT"
                self.state_time = 0.0

                self.wait_duration = random.uniform(
                    WAIT_TIME_MIN,
                    WAIT_TIME_MAX
                )

    def enter_land(self):
        self.velocity_x = 0.0
        self.state = "LAND"
        self.state_time = 0.0

    def get_draw_size(self):
        width_scale = 1.0
        height_scale = 1.0

        if self.state == "SQUASH":
            progress = min(self.state_time / SQUASH_TIME, 1.0)

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
            progress = min(self.state_time / LAND_TIME, 1.0)
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

        if self.state == "HURT":
            image = self.hurt_image

            # 생성한 피격 이미지에서 몸 부분만 사용.
            left = round(image.w * 197 / 1448)
            right = round(image.w * 1288 / 1448)
            top = round(image.h * 181 / 1086)
            bottom = round(image.h * 987 / 1086)

            direction = self.hurt_direction

            draw_width = self.width
            draw_height = self.height

        else:
            image = self.image
            left, top, right, bottom = 136, 171, 1311, 987

            direction = self.direction
            draw_width, draw_height = self.get_draw_size()

        width = right - left
        height = bottom - top
        source_bottom = image.h - bottom

        draw_y = self.y + draw_height / 2

        # 피격 원본은 오른쪽으로 밀리는 자세.
        if direction == 1:
            image.clip_draw(
                left, source_bottom,
                width, height,
                self.x, draw_y,
                draw_width, draw_height
            )
        else:
            image.clip_composite_draw(
                left, source_bottom,
                width, height,
                0, 'h',
                self.x, draw_y,
                draw_width, draw_height
            )

    def draw_health_bar(self):
        if not self.alive or not self.show_health_bar:
            return

        left = round(self.x - HP_BAR_WIDTH / 2)
        bottom = round(
            self.y + self.height * 1.12 + HP_BAR_GAP
        )

        right = left + HP_BAR_WIDTH - 1
        top = bottom + HP_BAR_HEIGHT - 1

        draw_rectangle(
            left - 1, bottom - 1,
            right + 1, top + 1,
            20, 25, 20,
            filled=True
        )

        draw_rectangle(
            left, bottom, right, top,
            70, 70, 70,
            filled=True
        )

        fill_width = round(
            HP_BAR_WIDTH * self.hp / self.max_hp
        )

        if fill_width > 0:
            draw_rectangle(
                left, bottom,
                left + fill_width - 1, top,
                70, 220, 80,
                filled=True
            )