from settings import SLIME_WIDTH, SLIME_HEIGHT


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
        self.speed = 45.0

        # 발판 끝에서 몸 전체가 떨어지지 않도록 여백 설정.
        margin = self.width / 2 + 4

        self.left_limit = platform.left + margin
        self.right_limit = platform.right - margin

        # 필요하면 같은 발판에서도 순찰 구역을 나눈다.
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

        # y는 슬라임의 바닥 기준 높이.
        self.y = float(platform.top)

    def update(self, frame_time):
        if self.left_limit == self.right_limit:
            return

        self.x += self.direction * self.speed * frame_time

        # 끝을 지나간 거리만큼 되돌려 방향 전환.
        while (
            self.x < self.left_limit
            or self.x > self.right_limit
        ):
            if self.x > self.right_limit:
                self.x = 2 * self.right_limit - self.x
                self.direction = -1

            elif self.x < self.left_limit:
                self.x = 2 * self.left_limit - self.x
                self.direction = 1

    def draw(self):
        # 원본 슬라임 이미지에서 실제 몸이 있는 영역.
        # 왼쪽 위 기준: (136, 171) ~ (1311, 987)
        left = 136
        top = 171
        right = 1311
        bottom = 987

        source_width = right - left
        source_height = bottom - top
        source_bottom = self.image.h - bottom

        draw_y = self.y + self.height / 2

        if self.direction == 1:
            self.image.clip_draw(
                left,
                source_bottom,
                source_width,
                source_height,
                self.x,
                draw_y,
                self.width,
                self.height
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
                self.width,
                self.height
            )