from pathlib import Path

from pico2d import load_image

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GROUND_Y,
    PLATFORM_THICKNESS,
)

from slime import Slime


BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "assets" / "images"


class Platform:
    def __init__(
        self,
        left,
        right,
        top,
        thickness=PLATFORM_THICKNESS
    ):
        self.left = left
        self.right = right
        self.top = top
        self.thickness = thickness

    def draw(self, image):
        # 긴 발판에서도 그림을 지나치게 늘리지 않도록 반복 출력.
        tile_width = 160
        current_x = self.left

        while current_x < self.right:
            draw_width = min(
                tile_width,
                self.right - current_x
            )

            # 마지막 조각은 필요한 만큼만 잘라서 출력.
            source_width = max(
                1,
                round(image.w * draw_width / tile_width)
            )

            image.clip_draw(
                0,
                0,
                source_width,
                image.h,
                current_x + draw_width / 2,
                self.top - self.thickness / 2,
                draw_width,
                self.thickness
            )

            current_x += draw_width


class Stage:
    def __init__(self):
        self.spawn_x = 120.0
        self.spawn_y = GROUND_Y

        self.background = load_image(
            str(IMAGE_DIR / "stage1_background.png")
        )

        self.platform_image = load_image(
            str(IMAGE_DIR / "grass_platform.png")
        )

        self.slime_image = load_image(
            str(IMAGE_DIR / "slime.png")
        )

        if (
            self.slime_image.w,
            self.slime_image.h
        ) != (1448, 1086):
            raise ValueError(
                "slime.png는 방금 생성한 "
                "1448x1086 크기의 원본 PNG를 사용해야 합니다."
            )

        self.platforms = [
            # 전체 바닥: 착지 높이는 유지하고 흙을 아래까지 채운다.
            Platform(
                0,
                SCREEN_WIDTH,
                GROUND_Y,
                GROUND_Y
            ),

            # 1층 좌우.
            Platform(100, 380, 165),
            Platform(900, 1180, 165),

            # 2층 중앙.
            Platform(300, 980, 250),

            # 3층 좌우 연결 구역.
            Platform(160, 490, 335),
            Platform(790, 1120, 335),

            # 4층 상단 중앙.
            Platform(450, 830, 420),
        ]

        self.slimes = []
        self.create_slimes()

    def create_slimes(self):
        ground = self.platforms[0]
        first_left = self.platforms[1]
        first_right = self.platforms[2]
        middle = self.platforms[3]
        upper = self.platforms[6]

        # 시작 위치 주변은 비우고,
        # 넓은 구역에 총 8마리를 배치한다.
        self.slimes = [
            # 전체 바닥: 2마리.
            Slime(
                self.slime_image,
                ground,
                x=400,
                direction=1,
                patrol_left=280,
                patrol_right=520
            ),
            Slime(
                self.slime_image,
                ground,
                x=1050,
                direction=-1,
                patrol_left=900,
                patrol_right=1180
            ),

            # 1층 좌우: 각각 1마리.
            Slime(
                self.slime_image,
                first_left,
                x=250,
                direction=-1
            ),
            Slime(
                self.slime_image,
                first_right,
                x=1040,
                direction=1
            ),

            # 중앙 발판: 순찰 구역을 나눈 2마리.
            Slime(
                self.slime_image,
                middle,
                x=450,
                direction=1,
                patrol_left=350,
                patrol_right=590
            ),
            Slime(
                self.slime_image,
                middle,
                x=820,
                direction=-1,
                patrol_left=690,
                patrol_right=930
            ),

            # 최상단 발판: 2마리.
            Slime(
                self.slime_image,
                upper,
                x=540,
                direction=1,
                patrol_left=490,
                patrol_right=600
            ),
            Slime(
                self.slime_image,
                upper,
                x=740,
                direction=-1,
                patrol_left=680,
                patrol_right=790
            ),
        ]

    def find_landing(self, x, half_width, old_y, new_y):
        landing = None

        for platform in self.platforms:
            overlaps_x = (
                x + half_width > platform.left
                and x - half_width < platform.right
            )

            crosses_top = (
                old_y >= platform.top
                and new_y <= platform.top
            )

            if overlaps_x and crosses_top:
                if landing is None or platform.top > landing.top:
                    landing = platform

        return landing

    def update(self, frame_time):
        for slime in self.slimes:
            slime.update(frame_time)

    def draw(self):
        # 배경 → 지형 → 몬스터 순서로 출력.
        self.background.draw(
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            SCREEN_WIDTH,
            SCREEN_HEIGHT
        )

        for platform in self.platforms:
            platform.draw(self.platform_image)

        for slime in self.slimes:
            slime.draw()