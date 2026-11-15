import math
from pathlib import Path

from pico2d import load_image


WEAPONS = {
    "adventurer_sword": {
        "name": "모험가의 검", "damage": 10, "duration": .48,
        "speed_label": "빠름", "reach": 48, "height_bonus": 0,
        "range_label": "짧음", "skill_scale": 1.0,
        "description": "가볍고 빠르게 휘두르는 검",
        "icon": (277, 297, 441, 704),
    },
    "forest_sword": {
        "name": "숲의 장검", "damage": 20, "duration": .65,
        "speed_label": "보통", "reach": 68, "height_bonus": 8,
        "range_label": "중간", "skill_scale": 1.15,
        "description": "위력과 거리가 균형 잡힌 검",
        "icon": (988, 29, 1184, 704),
        "blade": (988, 29, 1184, 555), "pivot_y": 535,
        "draw_width": 22, "draw_height": 50,
    },
    "heavy_sword": {
        "name": "묵직한 대검", "damage": 30, "duration": .85,
        "speed_label": "느림", "reach": 88, "height_bonus": 16,
        "range_label": "넓음", "skill_scale": 1.30,
        "description": "느리지만 강하고 넓게 베는 검",
        "icon": (1670, 10, 1952, 708),
        "blade": (1670, 10, 1952, 548), "pivot_y": 519,
        "draw_width": 35, "draw_height": 66,
    },
}
DEFAULT_WEAPON = "adventurer_sword"
IMAGE_PATH = Path(__file__).resolve().parent / "assets" / "images" / "weapon_icons.png"

# 기존 자세의 검 가드와 끝점 좌표. 캐릭터의 손과 발 위치는 그대로 유지한다.
POSE_ANCHORS = {
    (103, 13, 313, 324): ((261, 221), (306, 169)),
    (456, 13, 667, 324): ((615, 220), (660, 169)),
    (809, 14, 1020, 324): ((968, 223), (1015, 171)),
    (1163, 18, 1375, 325): ((1323, 227), (1371, 174)),
    (89, 379, 316, 678): ((269, 548), (304, 489)),
    (467, 379, 664, 686): ((618, 548), (655, 508)),
    (791, 379, 1031, 686): ((985, 550), (1024, 495)),
    (1178, 382, 1381, 687): ((1336, 549), (1372, 510)),
    (76, 741, 292, 1050): ((114, 819), (86, 748)),
    (440, 743, 683, 1050): ((608, 901), (675, 852)),
    (779, 754, 1063, 1050): ((973, 977), (1055, 992)),
    (1172, 741, 1393, 1050): ((1331, 932), (1386, 883)),
}


class WeaponArt:
    def __init__(self):
        self.image = load_image(str(IMAGE_PATH))

    def source_rect(self, rect):
        left, top, right, bottom = rect
        sx, sy = self.image.w / 2172, self.image.h / 724
        left, right = round(left * sx), round(right * sx)
        top, bottom = round(top * sy), round(bottom * sy)
        return left, self.image.h - bottom, right - left, bottom - top

    def draw_icon(self, weapon_id, x, y, height=46):
        rect = WEAPONS[weapon_id]["icon"]
        width = max(28 if weapon_id == "heavy_sword" else 22,
                    height * (rect[2] - rect[0]) / (rect[3] - rect[1]))
        self.image.clip_draw(*self.source_rect(rect), x, y, width, height)

    def draw_held(self, player, rect, direction, scale, camera_x, hurt=False):
        spec = WEAPONS[player.equipped_weapon]
        if "blade" not in spec:
            return  # 모험가의 검은 기존 자세에 그려진 검을 사용한다.
        if hurt:
            # 피격 원본 1254x1254 기준. 저장 크기에 따른 비율도 반영한다.
            sx, sy = player.hurt_image.w / 1254, player.hurt_image.h / 1254
            guard, tip = (895 * sx, 885 * sy), (1156 * sx, 841 * sy)
        else:
            guard, tip = POSE_ANCHORS[tuple(rect)]
        left, top, right, bottom = rect
        gx = player.x - camera_x + (guard[0] - (left + right) / 2) * scale * direction
        gy = player.y + (bottom - guard[1]) * scale
        dx, dy = (tip[0] - guard[0]) * direction, guard[1] - tip[1]
        length = math.hypot(dx, dy)
        ux, uy = dx / length, dy / length
        blade = spec["blade"]
        distance = (spec["pivot_y"] - (blade[1] + blade[3]) / 2) / (blade[3] - blade[1])
        distance *= spec["draw_height"]
        angle = math.atan2(uy, ux) - math.pi / 2
        # 더 큰 칼날을 기존 검 가드에 맞춰 겹쳐 그린다. 손과 손잡이는 유지한다.
        self.image.clip_composite_draw(
            *self.source_rect(blade), angle, '',
            gx + ux * distance, gy + uy * distance,
            spec["draw_width"], spec["draw_height"],
        )
