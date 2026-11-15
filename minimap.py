from pico2d import draw_rectangle
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Minimap:
    """맵 전체와 현재 화면 범위를 고정 UI 좌표로 표시한다."""

    def __init__(self):
        self.left = SCREEN_WIDTH - 336
        self.right = SCREEN_WIDTH - 16
        self.top = SCREEN_HEIGHT - 16
        self.bottom = self.top - 128

    def bounds(self, stage):
        scale = min(296 / stage.width, 78 / stage.height)
        width, height = stage.width * scale, stage.height * scale
        left = (self.left + self.right - width) / 2
        bottom = self.bottom + 12 + (78 - height) / 2
        return left, bottom, scale

    def project(self, stage, x, y):
        left, bottom, scale = self.bounds(stage)
        return left + x * scale, bottom + y * scale

    def draw(self, stage, player, camera, font):
        draw_rectangle(self.left, self.bottom, self.right, self.top,
                       25, 43, 37, filled=True)
        draw_rectangle(self.left, self.bottom, self.right, self.top, 160, 183, 139)
        font.draw(self.left + 12, self.top - 22, "1스테이지 · 전체 지도", (240, 240, 220))
        left, bottom, scale = self.bounds(stage)
        draw_rectangle(round(left), round(bottom),
                       round(left + stage.width * scale), round(bottom + stage.height * scale),
                       38, 63, 50, filled=True)
        for platform in stage.platforms:
            x1, y = self.project(stage, platform.left, platform.top)
            x2, _ = self.project(stage, platform.right, platform.top)
            draw_rectangle(round(x1), round(y) - 1, round(x2), round(y),
                           151, 173, 114, filled=True)
        # 흰 테두리는 현재 카메라가 보여주는 월드 영역.
        x1, y1 = self.project(stage, camera.x, 0)
        x2, y2 = self.project(stage, camera.x + camera.width, stage.height)
        draw_rectangle(round(x1), round(y1), round(x2), round(y2), 235, 235, 221)
        for slime in stage.slimes:
            if slime.alive:
                x, y = self.project(stage, slime.x, slime.y + slime.height / 2)
                self.draw_dot(x, y, (255, 76, 76), 1)
        # 플레이어를 마지막에 표시해 겹쳤을 때도 눈에 띄게 한다.
        x, y = self.project(stage, player.x, player.y + 36)
        self.draw_dot(x, y, (75, 255, 113), 2)

    @staticmethod
    def draw_dot(x, y, color, radius):
        x, y = round(x), round(y)
        draw_rectangle(x - radius - 1, y - radius - 1,
                       x + radius + 1, y + radius + 1, 15, 30, 24, filled=True)
        draw_rectangle(x - radius, y - radius, x + radius, y + radius,
                       *color, filled=True)
