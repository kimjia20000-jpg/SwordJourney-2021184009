from pico2d import draw_rectangle


class Platform:
    def __init__(self, left, right, top, thickness=16):
        self.left = left
        self.right = right
        self.top = top
        self.thickness = thickness

    def draw(self):
        # 착지와 이동을 확인하기 위한 임시 발판.
        # 추후 같은 위치에 풀과 흙 이미지를 적용한다.
        draw_rectangle(
            self.left,
            self.top - self.thickness,
            self.right,
            self.top
        )


class Stage:
    def __init__(self):
        self.spawn_x = 100.0
        self.spawn_y = 80.0

        self.platforms = [
            # 전체 바닥.
            Platform(0, 800, 80, 24),

            # 1층: 좌우 발판.
            Platform(60, 270, 150),
            Platform(530, 740, 150),

            # 2층: 중앙 발판.
            Platform(230, 570, 220),

            # 3층: 좌우 연결 발판.
            Platform(120, 300, 290),
            Platform(500, 680, 290),

            # 4층: 상단 중앙 발판.
            Platform(280, 520, 360),
        ]

    def find_landing(self, x, half_width, old_y, new_y):
        """하강 중 발이 통과한 발판 중 가장 높은 발판을 반환한다."""
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