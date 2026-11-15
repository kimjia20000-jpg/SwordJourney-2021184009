from pathlib import Path

from pico2d import (
    load_image, draw_rectangle, get_time,
    SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN,
    SDL_BUTTON_LEFT, SDLK_i, SDLK_1, SDLK_2,
)
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


IMAGE_PATH = Path(__file__).resolve().parent / "assets" / "images" / "potion_icons.png"
ITEMS = {
    "hp_potion": {"name": "체력 포션", "stat": "hp", "maximum": "max_hp",
                  "amount": 30, "key": "1", "color": (241, 113, 109),
                  "rect": (212, 97, 785, 841)},
    "mp_potion": {"name": "마나 포션", "stat": "mp", "maximum": "max_mp",
                  "amount": 20, "key": "2", "color": (112, 180, 255),
                  "rect": (989, 98, 1561, 841)},
}
DOUBLE_CLICK_SECONDS = 0.35


class Inventory:
    def __init__(self, player):
        self.player = player
        self.image = load_image(str(IMAGE_PATH))
        self.visible = False
        self.counts = {"hp_potion": 3, "mp_potion": 3}
        # 같은 포션은 한 슬롯에 쌓인다. 나머지는 이후 아이템용 빈 슬롯.
        self.slots = ["hp_potion", "mp_potion", None, None, None, None, None, None]
        self.left = SCREEN_WIDTH - 366
        self.right = SCREEN_WIDTH - 16
        self.bottom = 88
        self.top = 362
        self.mouse_x = -1
        self.mouse_y = -1
        self.keys_pressed = set()
        self.last_click_slot = None
        self.last_click_time = 0.0
        self.feedback = ""
        self.feedback_color = (190, 242, 196)
        self.feedback_remaining = 0.0

    def slot_rect(self, index):
        column, row = index % 4, index // 4
        left = self.left + 24 + column * 76
        bottom = self.top - 130 - row * 76
        return left, bottom, left + 64, bottom + 64

    def slot_at(self, x, y):
        if not self.visible:
            return None
        for index in range(len(self.slots)):
            left, bottom, right, top = self.slot_rect(index)
            if left <= x < right and bottom <= y < top:
                return index
        return None

    def reset_click(self):
        self.last_click_slot = None
        self.last_click_time = 0.0

    def close(self):
        self.visible = False
        self.reset_click()

    def use_item(self, item_id):
        p = self.player
        if not p.alive or item_id not in ITEMS:
            return False
        spec = ITEMS[item_id]
        if self.counts[item_id] <= 0:
            p.show_notice(f'{spec["name"]}이 없습니다.')
            return False
        current = getattr(p, spec["stat"])
        maximum = getattr(p, spec["maximum"])
        if current >= maximum - 1e-9:
            p.show_notice("이미 가득 찼습니다. 포션은 사용하지 않았어요.")
            return False
        recovered = min(spec["amount"], maximum - current)
        setattr(p, spec["stat"], min(maximum, current + recovered))
        self.counts[item_id] -= 1
        p.show_notice(f'{spec["name"]} 사용 · {recovered:g} 회복')
        self.feedback = f'+{recovered:g}'
        self.feedback_color = spec["color"]
        self.feedback_remaining = 0.8
        return True

    def handle_event(self, event):
        if not self.player.alive:
            return False
        watched_keys = (SDLK_i, SDLK_1, SDLK_2)
        if event.type == SDL_KEYUP and event.key in watched_keys:
            self.keys_pressed.discard(event.key)
            return True
        if event.type == SDL_KEYDOWN and event.key in watched_keys:
            if event.key in self.keys_pressed:
                return True
            self.keys_pressed.add(event.key)
            # 키 입력을 중간에 넣은 클릭 쌍은 더블클릭으로 취급하지 않는다.
            self.reset_click()
            if event.key == SDLK_i:
                self.visible = not self.visible
            elif event.key == SDLK_1:
                self.use_item("hp_potion")
            else:
                self.use_item("mp_potion")
            return True
        if event.type in (SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN):
            self.mouse_x = event.x
            self.mouse_y = SCREEN_HEIGHT - 1 - event.y
        if event.type != SDL_MOUSEBUTTONDOWN:
            return False
        if event.button != SDL_BUTTON_LEFT:
            self.reset_click()
            return False
        index = self.slot_at(self.mouse_x, self.mouse_y)
        if index is None or self.slots[index] is None:
            self.reset_click()
            return False
        now = get_time()
        if (self.last_click_slot == index
                and 0 <= now - self.last_click_time <= DOUBLE_CLICK_SECONDS):
            self.reset_click()
            self.use_item(self.slots[index])
        else:
            self.last_click_slot = index
            self.last_click_time = now
        return True

    def update(self, dt):
        self.feedback_remaining = max(0.0, self.feedback_remaining - dt)

    def draw_icon(self, item_id, x, y, height=44):
        left, top, right, bottom = ITEMS[item_id]["rect"]
        sx, sy = self.image.w / 1774, self.image.h / 887
        left, right = round(left * sx), round(right * sx)
        top, bottom = round(top * sy), round(bottom * sy)
        width = height * (right - left) / (bottom - top)
        self.image.clip_draw(left, self.image.h - bottom,
                             right - left, bottom - top, x, y, width, height)

    def draw_quickbar(self, font):
        # 스킬 슬롯 오른쪽에 항상 남은 포션 수와 I키 안내를 표시한다.
        for index, item_id in enumerate(ITEMS):
            left, bottom = 906 + index * 120, 8
            draw_rectangle(left, bottom, left + 112, bottom + 62,
                           24, 39, 36, filled=True)
            draw_rectangle(left, bottom, left + 112, bottom + 62, *ITEMS[item_id]["color"])
            self.draw_icon(item_id, left + 27, bottom + 33, 40)
            font.draw(left + 51, bottom + 43, ITEMS[item_id]["key"] + " 키", (231, 238, 229))
            font.draw(left + 51, bottom + 18, f'{self.counts[item_id]}개', (239, 228, 175))
        font.draw(1158, 39, "I 가방", (224, 235, 214))

    def draw(self, font):
        self.draw_quickbar(font)
        if not self.visible or not self.player.alive:
            return
        draw_rectangle(self.left, self.bottom, self.right, self.top,
                       24, 39, 36, filled=True)
        draw_rectangle(self.left, self.bottom, self.right, self.top, 154, 179, 135)
        font.draw(self.left + 16, self.top - 24, "인벤토리", (255, 232, 161))
        font.draw(self.right - 102, self.top - 24, "I 닫기", (203, 218, 198))
        font.draw(self.left + 16, self.top - 54, "아이템에 마우스를 올려 보세요.", (177, 195, 183))
        hovered = self.slot_at(self.mouse_x, self.mouse_y)
        for index, item_id in enumerate(self.slots):
            left, bottom, right, top = self.slot_rect(index)
            draw_rectangle(left, bottom, right, top, 38, 55, 48, filled=True)
            border = (229, 212, 137) if index == hovered else (85, 109, 91)
            draw_rectangle(left, bottom, right, top, *border)
            if item_id is not None:
                self.draw_icon(item_id, (left + right) / 2, bottom + 34)
                count = self.counts[item_id]
                draw_rectangle(right - 24, bottom + 2, right - 2, bottom + 22,
                               19, 29, 26, filled=True)
                font.draw(right - 21, bottom + 11, str(count),
                          (255, 238, 179) if count else (157, 164, 157))
        font.draw(self.left + 16, self.bottom + 42, "더블클릭으로 포션 사용", (221, 231, 219))
        font.draw(self.left + 16, self.bottom + 20, "1 체력 포션  /  2 마나 포션", (183, 213, 229))
        if hovered is not None and self.slots[hovered] is not None:
            self.draw_tooltip(self.slots[hovered], font)

    def draw_tooltip(self, item_id, font):
        spec = ITEMS[item_id]
        # 가방 왼쪽에 고정해 화면 밖으로 나가거나 슬롯을 가리지 않는다.
        left, right = self.left - 260, self.left - 12
        bottom, top = self.top - 148, self.top
        draw_rectangle(left, bottom, right, top, 18, 31, 30, filled=True)
        draw_rectangle(left, bottom, right, top, *spec["color"])
        font.draw(left + 12, top - 24, spec["name"], spec["color"])
        resource_name = "체력" if spec["stat"] == "hp" else "마나"
        font.draw(left + 12, top - 54, f'{resource_name} {spec["amount"]} 회복', (239, 239, 221))
        font.draw(left + 12, top - 82, f'보유 수량: {self.counts[item_id]}개', (219, 228, 213))
        font.draw(left + 12, top - 110, f'{spec["key"]} 키 또는 더블클릭', (190, 218, 237))
        font.draw(left + 12, top - 134, "가득 차면 소모하지 않음", (168, 185, 173))

    def draw_feedback(self, camera_x, font):
        if not self.player.alive or self.feedback_remaining <= 0:
            return
        rise = (0.8 - self.feedback_remaining) * 25
        font.draw(self.player.x - camera_x - 18, self.player.y + 110 + rise,
                  self.feedback, self.feedback_color)
