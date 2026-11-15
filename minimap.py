from pico2d import draw_rectangle
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from ui_theme import panel, title, text, rect, MUTED


class Minimap:
    """맵 전체와 현재 화면 범위를 고정 UI 좌표로 표시한다."""

    def __init__(self):
        self.left = SCREEN_WIDTH - 300
        self.right = SCREEN_WIDTH - 16
        self.top = SCREEN_HEIGHT - 16
        self.bottom = self.top - 139

    def bounds(self, stage):
        scale = min(258 / stage.width, 68 / stage.height)
        width, height = stage.width * scale, stage.height * scale
        left = (self.left + self.right - width) / 2
        bottom = self.bottom + 31 + (68 - height) / 2
        return left, bottom, scale

    def project(self, stage, x, y):
        left, bottom, scale = self.bounds(stage)
        return left + x * scale, bottom + y * scale

    def draw(self, stage, player, camera, font):
        panel(self.left, self.bottom, self.right, self.top)
        title(font, self.left, self.right, self.top, f'{stage.number}스테이지 · 전체 지도')
        text(font, self.left + 30, self.bottom + 17, '나', MUTED)
        text(font, self.left + 107, self.bottom + 17, '몬스터', MUTED)
        text(font, self.left + 215, self.bottom + 17, '보스' if stage.number == 3 else '출구', MUTED)
        self.draw_dot(self.left + 20, self.bottom + 17, (75, 255, 113), 2)
        self.draw_dot(self.left + 97, self.bottom + 17, (255, 76, 76), 2)
        self.draw_dot(self.left + 205, self.bottom + 17, (95, 216, 255), 2)
        left, bottom, scale = self.bounds(stage)
        draw_rectangle(round(left), round(bottom),
                       round(left + stage.width * scale), round(bottom + stage.height * scale),
                       43, 54, 78, filled=True)
        for platform in stage.platforms:
            x1, y = self.project(stage, platform.left, platform.top)
            x2, _ = self.project(stage, platform.right, platform.top)
            draw_rectangle(round(x1), round(y) - 1, round(x2), round(y),
                           194, 180, 143, filled=True)
        # 흰 테두리는 현재 카메라가 보여주는 월드 영역.
        x1, y1 = self.project(stage, camera.x, 0)
        x2, y2 = self.project(stage, camera.x + camera.width, stage.height)
        draw_rectangle(round(x1), round(y1), round(x2), round(y2), 235, 235, 221)
        if stage.number == 3 and stage.boss.alive:
            x,y=self.project(stage,stage.boss.x,stage.boss.y+100)
            self.draw_dot(x,y,(95,216,255),3)
        if stage.portal.active:
            x, y = self.project(stage, stage.portal.x, stage.portal.y + 60)
            # 출구는 점보다 큰 푸른 사각 테두리로 구분한다.
            x, y = round(x), round(y)
            draw_rectangle(x - 4, y - 5, x + 4, y + 5, 95, 216, 255)
        for slime in stage.monsters:
            if slime.alive and slime is not getattr(stage,'boss',None):
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
