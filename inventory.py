from pathlib import Path

from pico2d import (
    load_image, draw_rectangle, get_time,
    SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN,
    SDL_BUTTON_LEFT, SDLK_i, SDLK_1, SDLK_2, SDLK_k,
)
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from weapons import WEAPONS
from ui_theme import panel, title, text, rect, slot, keycap, INK, MUTED, WHITE, GOLD, NAVY


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
        self.skill_visible = False
        self.counts = {"hp_potion": 3, "mp_potion": 3}
        # 같은 포션은 한 슬롯에 쌓인다. 나머지는 이후 아이템용 빈 슬롯.
        self.slots = ["hp_potion", "mp_potion", "adventurer_sword", None,
                      None, None, None, None]
        self.left = SCREEN_WIDTH - 346
        self.right = SCREEN_WIDTH - 16
        self.bottom = 98
        self.top = 386
        self.mouse_x = -1
        self.mouse_y = -1
        self.keys_pressed = set()
        self.last_click_slot = None
        self.last_click_time = 0.0
        self.feedback = ""
        self.feedback_color = (190, 242, 196)
        self.feedback_remaining = 0.0

    def grant_items(self, rewards):
        """공간과 항목을 먼저 검사하고 보상 묶음을 한 번에 넣는다."""
        if not self.player.alive:
            return False
        if any(item not in ITEMS and item not in WEAPONS for item in rewards):
            return False
        if any(not isinstance(count, int) or count <= 0 for count in rewards.values()):
            return False
        # 검은 고유 장비로 취급하며 같은 검을 다시 받아도 슬롯을 추가하지 않는다.
        new_items = [item for item in rewards if item not in self.slots]
        free_slots = [i for i, item in enumerate(self.slots) if item is None]
        if len(new_items) > len(free_slots):
            return False
        for index, item in zip(free_slots, new_items):
            self.slots[index] = item
        for item, count in rewards.items():
            if item in ITEMS:
                self.counts[item] = self.counts.get(item, 0) + count
            else:
                self.player.owned_weapons.add(item)
        return True

    def slot_rect(self, index):
        column, row = index % 4, index // 4
        left = self.left + 22 + column * 74
        bottom = self.top - 140 - row * 74
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
        self.skill_visible = False
        self.reset_click()

    def use_item(self, item_id):
        p = self.player
        if item_id in WEAPONS:
            return p.request_equip(item_id)
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
        watched_keys = (SDLK_i, SDLK_1, SDLK_2, SDLK_k)
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
            elif event.key == SDLK_k:
                self.skill_visible = not self.skill_visible
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
        if item_id in WEAPONS:
            self.player.weapon_art.draw_icon(item_id, x, y, height)
            return
        left, top, right, bottom = ITEMS[item_id]["rect"]
        sx, sy = self.image.w / 1774, self.image.h / 887
        left, right = round(left * sx), round(right * sx)
        top, bottom = round(top * sy), round(bottom * sy)
        width = height * (right - left) / (bottom - top)
        self.image.clip_draw(left, self.image.h - bottom,
                             right - left, bottom - top, x, y, width, height)

    def draw_quickbar(self, font):
        for index, item_id in enumerate(ITEMS):
            l, b = 742 + index * 65, 14
            slot(l, b, 52)
            self.draw_icon(item_id, l + 27, b + 29, 37)
            keycap(font, l - 2, b - 1, ITEMS[item_id]['key'])
            text(font, l + 36, b + 10, self.counts[item_id], WHITE)
        text(font, 882, 49, 'I  인벤토리', INK)
        text(font, 882, 26, 'K  스킬 창', MUTED)

    def draw(self, font):
        self.draw_quickbar(font)
        if not self.visible or not self.player.alive:
            return
        panel(self.left, self.bottom, self.right, self.top)
        title(font, self.left, self.right, self.top, '인벤토리', 'I 닫기')
        text(font, self.left + 22, self.top - 56, '소지품', INK)
        text(font, self.right - 99, self.top - 56,
             f'{sum(i is not None for i in self.slots)} / {len(self.slots)} 칸', MUTED)
        hovered = self.slot_at(self.mouse_x, self.mouse_y)
        for index, item_id in enumerate(self.slots):
            left, bottom, right, top = self.slot_rect(index)
            equipped = item_id == self.player.equipped_weapon
            pending = item_id is not None and item_id == self.player.pending_weapon
            slot(left, bottom, 64, equipped, pending, index == hovered)
            if item_id is not None:
                self.draw_icon(item_id, (left + right) / 2, bottom + 36, 42)
                if item_id in ITEMS:
                    text(font, right - 17, bottom + 12, self.counts[item_id], WHITE)
                elif equipped or pending:
                    rect(left + 4, bottom + 3, right - 4, bottom + 20, NAVY)
                    text(font, left + 16, bottom + 12, '장착' if equipped else '예약',
                         (255, 210, 80) if equipped else (100, 205, 255))
        text(font, self.left + 22, self.bottom + 49, '더블클릭  ·  검 장착 / 포션 사용', INK)
        text(font, self.left + 22, self.bottom + 25, '장착 중에는 금색 테두리가 표시돼요.', MUTED)
        if hovered is not None and self.slots[hovered] is not None:
            self.draw_tooltip(self.slots[hovered], font)

    def draw_tooltip(self, item_id, font):
        if item_id in WEAPONS:
            self.draw_weapon_tooltip(item_id, font)
            return
        spec = ITEMS[item_id]
        left, right = self.left - 260, self.left - 12
        bottom, top = self.top - 170, self.top
        panel(left, bottom, right, top)
        title(font, left, right, top, spec['name'])
        resource_name = '체력' if spec['stat'] == 'hp' else '마나'
        text(font, left + 16, top - 57, f'{resource_name} {spec["amount"]} 회복', INK)
        text(font, left + 16, top - 83, f'보유 수량: {self.counts[item_id]}개', INK)
        text(font, left + 16, top - 112, f'{spec["key"]} 키 또는 더블클릭', MUTED)
        text(font, left + 16, top - 143, '가득 차면 소모하지 않음', MUTED)

    def draw_weapon_tooltip(self, weapon_id, font):
        spec = WEAPONS[weapon_id]
        left, right = self.left - 286, self.left - 12
        bottom, top = self.top - 246, self.top
        panel(left, bottom, right, top)
        title(font, left, right, top, spec['name'])
        lines = [
            f'공격력  {spec["damage"]}',
            f'공격 속도  {spec["speed_label"]}',
            f'공격 범위  {spec["range_label"]} ({spec["reach"]})',
            f'강화 베기 피해  {spec["damage"] * 2}',
            f'검기 발사 피해  {round(spec["damage"] * 1.5)}',
            '현재 장착 중' if weapon_id == self.player.equipped_weapon else
            '동작 종료 후 장착 예약' if weapon_id == self.player.pending_weapon else
            '더블클릭으로 장착',
            '공통 스킬 · 크리티컬 없음',
        ]
        for index, line in enumerate(lines):
            text(font, left + 16, top - 58 - index * 27, line,
                 INK if index < 5 else (53, 109, 151))

    def draw_feedback(self, camera_x, font):
        if not self.player.alive or self.feedback_remaining <= 0:
            return
        rise = (0.8 - self.feedback_remaining) * 25
        font.draw(self.player.x - camera_x - 18, self.player.y + 110 + rise,
                  self.feedback, self.feedback_color)
