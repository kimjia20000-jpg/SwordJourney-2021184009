from pico2d import draw_rectangle

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from ui_theme import panel, title, text, rect, MUTED


class Minimap:
    PLAYER_COLOR = (75, 255, 113)
    MONSTER_COLOR = (255, 76, 76)
    EXIT_COLOR = (95, 216, 255)
    CLOSED_EXIT_COLOR = (149, 153, 165)
    ELDER_COLOR = (255, 208, 89)

    GROUND_COLOR = (194, 180, 143)
    MAP_COLOR = (43, 54, 78)
    CAMERA_COLOR = (235, 235, 221)

    HOUSE_COLORS = {
        "red_house": (196, 101, 76),
        "green_house": (96, 162, 148),
        "straw_house": (216, 176, 92),
    }

    def __init__(self):
        self.left = SCREEN_WIDTH - 300
        self.right = SCREEN_WIDTH - 16
        self.top = SCREEN_HEIGHT - 16
        self.bottom = self.top - 139

    def bounds(self, stage):
        # 마을은 한 화면 크기라 전투 맵과 같은 균일 축척을 쓰면
        # 미니맵 가운데에 좁게 표시된다.
        # 마을은 가로·세로를 지도 칸에 맞춰 집 사이 간격을 잘 보이게 한다.
        if stage.number == 0:
            width = self.right - self.left - 26
            height = 68
            scale_x = width / stage.width
            scale_y = height / stage.height
        else:
            scale = min(258 / stage.width, 68 / stage.height)
            scale_x = scale
            scale_y = scale
            width = stage.width * scale
            height = stage.height * scale

        left = (self.left + self.right - width) / 2
        bottom = self.bottom + 31 + (68 - height) / 2

        return left, bottom, scale_x, scale_y

    def project(self, stage, world_x, world_y):
        left, bottom, scale_x, scale_y = self.bounds(stage)

        return (
            round(left + world_x * scale_x),
            round(bottom + world_y * scale_y),
        )

    @staticmethod
    def draw_dot(x, y, color, radius):
        x = round(x)
        y = round(y)

        draw_rectangle(
            x - radius - 1,
            y - radius - 1,
            x + radius + 1,
            y + radius + 1,
            15, 30, 24,
            filled=True,
        )
        draw_rectangle(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            *color,
            filled=True,
        )

    def draw_legend(self, stage, font):
        y = self.bottom + 17

        if stage.number == 0:
            exit_label = "출구 열림" if stage.portal.active else "출구 닫힘"
            exit_color = (
                self.EXIT_COLOR
                if stage.portal.active
                else self.CLOSED_EXIT_COLOR
            )
            entries = (
                (19, "나", self.PLAYER_COLOR),
                (73, "촌장", self.ELDER_COLOR),
                (141, exit_label, exit_color),
            )
        else:
            entries = (
                (20, "나", self.PLAYER_COLOR),
                (97, "몬스터", self.MONSTER_COLOR),
                (
                    205,
                    "보스" if stage.number == 3 else "출구",
                    self.EXIT_COLOR,
                ),
            )

        for offset, label, color in entries:
            x = self.left + offset
            self.draw_dot(x, y, color, 2)
            text(font, x + 10, y, label, MUTED)

    def draw_platforms(self, stage):
        for platform in stage.platforms:
            x1, y = self.project(stage, platform.left, platform.top)
            x2, _ = self.project(stage, platform.right, platform.top)

            draw_rectangle(
                x1, y - 1,
                x2, y,
                *self.GROUND_COLOR,
                filled=True,
            )

    def draw_camera(self, stage, camera):
        left = max(0, camera.x)
        right = min(stage.width, camera.x + camera.width)

        x1, y1 = self.project(stage, left, 0)
        x2, y2 = self.project(stage, right, stage.height)

        draw_rectangle(x1, y1, x2, y2, *self.CAMERA_COLOR)

    def draw_house(self, stage, house_name, world_x, height):
        # 실제 화면에서 그리는 집과 동일한 위치·높이·원본 비율을 쓴다.
        _, _, source_width, source_height = stage.village_sprites[house_name]
        width = height * source_width / source_height
        ground_y = stage.platforms[0].top

        left, bottom = self.project(
            stage, world_x - width / 2, ground_y
        )
        right, top = self.project(
            stage, world_x + width / 2, ground_y + height
        )

        center = (left + right) // 2
        roof_bottom = bottom + (top - bottom) // 2
        roof_height = max(1, top - roof_bottom)
        roof_color = self.HOUSE_COLORS[house_name]

        # 외벽, 문, 창문
        rect(left + 3, bottom, right - 3, roof_bottom, (219, 193, 148))
        rect(center - 2, bottom, center + 2, roof_bottom - 1, (104, 76, 61))

        if right - left >= 16:
            rect(left + 5, bottom + 3, left + 8, bottom + 6, (255, 221, 127))
            rect(right - 8, bottom + 3, right - 5, bottom + 6, (255, 221, 127))

        # 한 줄씩 폭을 줄여 작은 지도에서도 지붕 모양이 보이게 한다.
        for row in range(roof_height):
            fraction = row / roof_height
            half_width = max(1, round((right - left) * (1 - fraction) / 2))
            y = roof_bottom + row
            rect(center - half_width, y, center + half_width, y + 1, roof_color)

    def draw_village(self, stage):
        for house_name, world_x, height in stage.village_houses:
            self.draw_house(stage, house_name, world_x, height)

        ground_y = stage.platforms[0].top

        # 촌장은 플레이어와 같은 자리에 서도 식별되도록
        # 머리 위에 금색 마름모를 표시한다.
        x, y = self.project(stage, stage.elder_x, ground_y + 126)
        rect(x - 1, y - 4, x + 2, y + 5, self.ELDER_COLOR)
        rect(x - 3, y - 2, x + 4, y + 3, self.ELDER_COLOR)

    def draw_portal(self, stage):
        portal = stage.portal

        # 마을에서는 의뢰를 받기 전에도 출구 위치를 알 수 있다.
        if not portal.active and stage.number != 0:
            return

        color = self.EXIT_COLOR if portal.active else self.CLOSED_EXIT_COLOR
        x, y = self.project(stage, portal.x, portal.y + 60)

        if stage.number == 0:
            # 마을 포탈은 문 모양으로 표시한다.
            draw_rectangle(x - 4, y - 5, x + 4, y + 4, *color)
            rect(x - 2, y + 4, x + 3, y + 6, color)
            if portal.active:
                rect(x - 1, y - 3, x + 2, y + 3, color)
        else:
            draw_rectangle(x - 4, y - 5, x + 4, y + 5, *color)

    def draw_monsters(self, stage):
        boss = getattr(stage, "boss", None)

        if boss is not None and boss.alive:
            x, y = self.project(stage, boss.x, boss.y + 100)
            self.draw_dot(x, y, self.EXIT_COLOR, 3)

        for monster in stage.monsters:
            if monster.alive and monster is not boss:
                x, y = self.project(
                    stage,
                    monster.x,
                    monster.y + monster.height / 2,
                )
                self.draw_dot(x, y, self.MONSTER_COLOR, 1)

    def draw(self, stage, player, camera, font):
        panel(self.left, self.bottom, self.right, self.top)

        if stage.number == 0:
            map_title = "새싹 마을 · 전체 지도"
        else:
            map_title = f"{stage.number}스테이지 · 전체 지도"

        title(font, self.left, self.right, self.top, map_title)
        self.draw_legend(stage, font)

        x1, y1 = self.project(stage, 0, 0)
        x2, y2 = self.project(stage, stage.width, stage.height)

        draw_rectangle(
            x1, y1, x2, y2,
            *self.MAP_COLOR,
            filled=True,
        )

        if stage.number == 0:
            self.draw_village(stage)

        self.draw_platforms(stage)
        self.draw_camera(stage, camera)
        self.draw_portal(stage)

        if stage.number != 0:
            self.draw_monsters(stage)

        # 다른 표시와 겹쳐도 내 위치가 보이도록 마지막에 그린다.
        px, py = self.project(stage, player.x, player.y + 36)
        self.draw_dot(px, py, self.PLAYER_COLOR, 2)