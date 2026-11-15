from pathlib import Path

from pico2d import load_image, draw_rectangle

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, GROUND_Y, PLATFORM_THICKNESS,
)
from slime import Slime
from portal import Portal


BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "assets" / "images"


class Platform:
    def __init__(self, left, right, top, thickness=PLATFORM_THICKNESS):
        self.left = left
        self.right = right
        self.top = top
        self.thickness = thickness

    def draw(self, image, camera):
        if not camera.visible(self.left, self.right):
            return
        tile_width = 160
        first = max(0, int((camera.x - self.left) // tile_width))
        current_x = self.left + first * tile_width
        while current_x < min(self.right, camera.x + camera.width):
            draw_width = min(tile_width, self.right - current_x)
            source_width = max(1, round(image.w * draw_width / tile_width))
            image.clip_draw(
                0, 0, source_width, image.h,
                current_x + draw_width / 2 - camera.x,
                self.top - self.thickness / 2,
                draw_width, self.thickness,
            )
            current_x += draw_width


class Stage:
    def __init__(self):
        self.width = WORLD_WIDTH
        self.height = SCREEN_HEIGHT
        self.spawn_x = 120.0
        self.spawn_y = GROUND_Y
        self.background = load_image(str(IMAGE_DIR / "stage1_background.png"))
        self.platform_image = load_image(str(IMAGE_DIR / "grass_platform.png"))
        self.slime_image = load_image(str(IMAGE_DIR / "slime.png"))
        if (self.slime_image.w, self.slime_image.h) != (1448, 1086):
            raise ValueError("slime.png는 1448x1086 크기의 원본 PNG를 사용해야 합니다.")

        # 모든 구역은 하나의 스테이지. 전체 바닥은 끊기지 않는다.
        self.platforms = [Platform(0, self.width, GROUND_Y, GROUND_Y)]
        self.zones = (
            (0, 1280, "초원 입구"),
            (1280, 2560, "나뭇잎 숲길"),
            (2560, 3840, "햇살 언덕"),
        )
        layouts = [
            # 초원: 낮은 계단과 넓은 중간 발판.
            (250, 500, 165), (440, 760, 250), (700, 980, 335),
            (930, 1220, 250), (1080, 1350, 165),
            # 숲길: 아래쪽 길과 위쪽 길로 나뉘는 발판.
            (1330, 1570, 165), (1500, 1790, 250),
            (1720, 2000, 335), (1930, 2220, 420),
            (2140, 2430, 335), (2310, 2590, 250),
            (1800, 2070, 165),
            # 언덕: 계단을 올라 넓은 상단에 도달, 끝에서 다시 내려옴.
            (2540, 2790, 165), (2710, 2970, 250),
            (2900, 3170, 335), (3090, 3480, 420),
            (3410, 3650, 335), (3590, 3820, 250),
            (3680, 3840, 165),
        ]
        self.platforms.extend(Platform(*layout) for layout in layouts)
        self.create_slimes()
        self.initial_monster_count = len(self.slimes)
        self.cleared = False
        self.clear_banner_remaining = 0.0
        # 오른쪽 끝의 높이 250 발판. 아래층과 진입 판정을 구분한다.
        self.portal = Portal(self.width - 110, self.platforms[-2].top)

        # 장식은 충돌 대상이 아니다. 위치와 색상을 고정해 재시작 시 유지.
        self.trees = [
            (600, 80, 0.85), (1130, 80, 0.7),
            (1420, 80, 1.15), (1670, 80, 1.0),
            (2050, 80, 1.3), (2420, 80, 1.1),
            (2830, 80, 0.8), (3330, 420, 0.6),
        ]

    def create_slimes(self):
        ground = self.platforms[0]
        self.slimes = []
        # 바닥 6마리. 시작 지점과 마지막 출구 예정 공간은 비워 둔다.
        for x, left, right in (
            (620, 530, 800), (1080, 980, 1190),
            (1510, 1360, 1650), (2210, 2100, 2360),
            (2780, 2660, 2890), (3480, 3360, 3600),
        ):
            self.slimes.append(Slime(
                self.slime_image, ground, x,
                direction=1 if len(self.slimes) % 2 == 0 else -1,
                patrol_left=left, patrol_right=right,
            ))
        # 구역별 상단 사냥터 10마리. 좁은 연결 발판은 비운다.
        for index in (1, 2, 3, 6, 8, 9, 10, 14, 16, 17):
            platform = self.platforms[index]
            self.slimes.append(Slime(
                self.slime_image, platform,
                (platform.left + platform.right) / 2,
                direction=1 if index % 2 else -1,
            ))

    @property
    def remaining_monsters(self):
        return sum(slime.alive for slime in self.slimes)

    def zone_name(self, x):
        for left, right, name in self.zones:
            if left <= x < right:
                return name
        return self.zones[-1][2]

    def find_landing(self, x, half_width, old_y, new_y):
        landing = None
        for platform in self.platforms:
            overlaps = x + half_width > platform.left and x - half_width < platform.right
            crosses = old_y >= platform.top and new_y <= platform.top
            if overlaps and crosses:
                if landing is None or platform.top > landing.top:
                    landing = platform
        return landing

    def resolve_clear(self):
        # 마지막 공격과 사망 몬스터 정리가 끝난 뒤 호출한다.
        # 한 번만 전환하므로 배너와 포탈이 매 프레임 초기화되지 않는다.
        if self.cleared or self.remaining_monsters != 0:
            return False
        self.cleared = True
        self.clear_banner_remaining = 3.2
        self.portal.activate()
        return True

    def handle_portal_event(self, event, player):
        if self.portal.handle_event(event, player):
            # 2스테이지 구현 전에는 현재 맵을 유지한다.
            self.portal.show_notice("2스테이지는 준비 중입니다. 현재 맵을 계속 탐험하세요.")

    def draw_status(self, player, normal_font, title_font):
        if not player.alive:
            return
        if self.clear_banner_remaining > 0:
            cx, cy = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2
            draw_rectangle(cx - 260, cy - 48, cx + 260, cy + 64,
                           25, 48, 43, filled=True)
            draw_rectangle(cx - 260, cy - 48, cx + 260, cy + 64, 170, 226, 183)
            title_font.draw(cx - 150, cy + 23, "1스테이지 클리어!", (255, 229, 137))
            normal_font.draw(cx - 193, cy - 22,
                             "오른쪽 끝 출구 포탈이 열렸습니다.", (220, 247, 235))
        if self.portal.notice_remaining > 0:
            message = self.portal.notice
        elif self.portal.nearby(player):
            message = ("위 방향키 : 포탈 진입" if self.portal.active
                       else "닫힌 포탈 — 모든 몬스터를 처치하세요.")
        else:
            return
        draw_rectangle(265, 18, SCREEN_WIDTH - 265, 61, 25, 43, 37, filled=True)
        normal_font.draw(280, 35, message, (215, 241, 255))

    def update(self, dt):
        self.clear_banner_remaining = max(0.0, self.clear_banner_remaining - dt)
        self.portal.update(dt)
        # 화면 밖에서도 몬스터의 이동과 상태 갱신을 계속한다.
        for slime in self.slimes:
            slime.update(dt)

    def draw_background(self, camera):
        # 좌우 교대로 반전해 반복 경계의 색상 연결을 맞춘다.
        offset = camera.x * 0.18
        first_tile = int(offset // SCREEN_WIDTH)
        for tile in range(first_tile, first_tile + 2):
            x = tile * SCREEN_WIDTH + SCREEN_WIDTH / 2 - offset
            if tile % 2:
                self.background.clip_composite_draw(
                    0, 0, self.background.w, self.background.h, 0, 'h',
                    x, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT,
                )
            else:
                self.background.draw(x, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT)

    def draw_tree(self, x, y, scale, camera):
        if not camera.visible(x - 90 * scale, x + 90 * scale):
            return
        x -= camera.x
        def block(l, b, r, t, color):
            draw_rectangle(round(x + l * scale), round(y + b * scale),
                           round(x + r * scale), round(y + t * scale),
                           *color, filled=True)
        block(-10, 0, 12, 155, (109, 76, 44))
        block(-3, 0, 8, 155, (144, 100, 55))
        block(-75, 105, 75, 155, (49, 111, 52))
        block(-57, 145, 60, 190, (63, 139, 56))
        block(-35, 181, 38, 210, (88, 160, 63))
        block(-64, 150, -18, 163, (113, 178, 69))

    def draw_plants(self, camera):
        for index, platform in enumerate(self.platforms):
            if not camera.visible(platform.left, platform.right):
                continue
            start = platform.left + 28
            for x in range(int(start), int(platform.right - 20), 145):
                if not camera.visible(x - 10, x + 10):
                    continue
                sx, y = round(x - camera.x), round(platform.top)
                draw_rectangle(sx - 5, y, sx - 2, y + 9, 67, 128, 46, filled=True)
                draw_rectangle(sx + 2, y, sx + 4, y + 13, 88, 155, 51, filled=True)
                if (x + index) % 3 == 0:
                    draw_rectangle(sx + 1, y + 11, sx + 6, y + 15,
                                   255, 217, 102, filled=True)

    def draw(self, camera):
        self.draw_background(camera)
        for tree in self.trees:
            self.draw_tree(*tree, camera)
        for platform in self.platforms:
            platform.draw(self.platform_image, camera)
        self.draw_plants(camera)
        self.portal.draw(camera)
        for slime in self.slimes:
            if camera.visible(slime.x - slime.width, slime.x + slime.width):
                slime.draw(camera.x)
