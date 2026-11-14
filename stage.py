from pico2d import draw_rectangle

from settings import (
    SCREEN_WIDTH,
    GROUND_Y,
    PLATFORM_THICKNESS,
)


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

    def draw(self):
        # 지형 확인용 임시 사각형.
        # 나중에 같은 영역에 풀과 흙 이미지를 그린다.
        draw_rectangle(
            self.left,
            self.top - self.thickness,
            self.right,
            self.top
        )


class Stage:
    def __init__(self):
        self.spawn_x = 120.0
        self.spawn_y = GROUND_Y

        self.platforms = [
            # 전체 바닥.
            Platform(
                0,
                SCREEN_WIDTH - 1,
                GROUND_Y,
                28
            ),

            # 1층: 좌우 전투 발판.
            Platform(100, 380, 165),
            Platform(900, 1180, 165),

            # 2층: 넓은 중앙 발판.
            Platform(300, 980, 250),

            # 3층: 좌우 발판.
            Platform(160, 490, 335),
            Platform(790, 1120, 335),

            # 4층: 상단 중앙 발판.
            Platform(450, 830, 420),
        ]

    def find_landing(self, x, half_width, old_y, new_y):
        """하강 중 발이 통과한 발판 중 가장 높은 발판을 찾는다."""
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

    def draw(self):
        for platform in self.platforms:
            platform.draw()