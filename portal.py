import math
from pathlib import Path

from pico2d import load_image, draw_rectangle, SDL_KEYDOWN, SDL_KEYUP, SDLK_UP


IMAGE_PATH = Path(__file__).resolve().parent / "assets" / "images" / "portal_sheet.png"
PORTAL_HEIGHT = 152.0
PORTAL_WIDTH = PORTAL_HEIGHT * 707 / 737


class Portal:
    """닫힌 출구 → 활성화 → 위 방향키 입력. 다음 맵 연결은 별도 처리."""

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.image = load_image(str(IMAGE_PATH))
        self.active = False
        self.elapsed = 0.0
        self.up_pressed = False
        self.notice = ""
        self.notice_remaining = 0.0
        self.frames = ((18, 22, 725, 759), (1258, 22, 1965, 759))

    def activate(self):
        self.active = True

    def nearby(self, player):
        # 같은 x에 있어도 아래층이나 공중에서는 진입하지 않는다.
        return (player.alive and player.on_ground
                and abs(player.x - self.x) <= 44
                and abs(player.y - self.y) <= 8)

    def can_enter(self, player):
        return (self.active and self.nearby(player)
                and player.hurt_remaining <= 0 and not player.attacking)

    def handle_event(self, event, player):
        if event.type == SDL_KEYUP and event.key == SDLK_UP:
            self.up_pressed = False
            return False
        if event.type != SDL_KEYDOWN or event.key != SDLK_UP:
            return False
        if self.up_pressed:
            return False
        self.up_pressed = True
        if not self.nearby(player):
            return False
        if not self.active:
            self.show_notice("몬스터를 모두 처치하면 포탈이 열립니다.")
            return False
        if not self.can_enter(player):
            self.show_notice("동작이 끝난 뒤 위 방향키를 다시 눌러 주세요.")
            return False
        return True

    def show_notice(self, text):
        self.notice = text
        self.notice_remaining = 3.0

    def update(self, dt):
        self.elapsed += dt
        self.notice_remaining = max(0.0, self.notice_remaining - dt)

    def draw(self, camera):
        if not camera.visible(self.x - PORTAL_WIDTH / 2, self.x + PORTAL_WIDTH / 2):
            return
        left, top, right, bottom = self.frames[int(self.active)]
        # 시트의 각 프레임을 같은 표시 크기와 바닥 기준으로 출력한다.
        sx, sy = self.image.w / 1983, self.image.h / 793
        left, right = round(left * sx), round(right * sx)
        top, bottom = round(top * sy), round(bottom * sy)
        self.image.clip_draw(
            left, self.image.h - bottom, right - left, bottom - top,
            self.x - camera.x, self.y + PORTAL_HEIGHT / 2,
            PORTAL_WIDTH, PORTAL_HEIGHT,
        )
        if self.active:
            # 문틀은 고정하고 문 안의 작은 빛만 움직인다.
            for i in range(4):
                phase = self.elapsed * 2.0 + i * math.pi / 2
                x = round(self.x - camera.x + math.sin(phase) * 22)
                y = round(self.y + 55 + (math.cos(phase) + 1) * 25)
                draw_rectangle(x - 1, y - 1, x + 1, y + 1,
                               194, 248, 255, filled=True)
