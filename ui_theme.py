"""스테이지 배경과 무관한 공통 RPG UI. 이미지 없이도 선명한 패널."""
from pico2d import draw_rectangle

INK = (47, 54, 72)
MUTED = (112, 110, 116)
NAVY = (43, 54, 78)
GOLD = (203, 164, 91)
CREAM = (246, 239, 221)
WHITE = (255, 251, 240)


def rect(l, b, r, t, color):
    if r > l and t > b:
        draw_rectangle(round(l), round(b), round(r), round(t), *color, filled=True)


def bevel(l, b, r, t, color, cut=5):
    rect(l + cut, b, r - cut, t, color)
    rect(l, b + cut, r, t - cut, color)
    rect(l + 2, b + 2, r - 2, t - 2, color)


def panel(l, b, r, t, dark=False):
    bevel(l + 3, b - 4, r + 3, t - 4, (30, 33, 45))
    bevel(l, b, r, t, INK)
    bevel(l + 2, b + 2, r - 2, t - 2, GOLD)
    bevel(l + 4, b + 4, r - 4, t - 4, NAVY if dark else CREAM)
    rect(l + 9, t - 6, r - 9, t - 5, (108, 121, 151) if dark else WHITE)
    for x in (l + 7, r - 9):
        rect(x, b + 7, x + 2, b + 9, GOLD)
        rect(x, t - 9, x + 2, t - 7, GOLD)


def text(font, x, y, value, color=INK):
    font.draw(round(x), round(y), str(value), color)


def title(font, l, r, top, name, hint=''):
    bevel(l + 7, top - 37, r - 7, top - 7, NAVY, 3)
    text(font, l + 18, top - 22, name, WHITE)
    if hint:
        text(font, r - 72, top - 22, hint, (233, 208, 155))


def slot(l, b, size=58, selected=False, pending=False, hover=False):
    color = (255, 210, 80) if selected else (100, 205, 255) if pending else GOLD if hover else (158, 151, 141)
    bevel(l, b, l + size, b + size, color, 3)
    bevel(l + 2, b + 2, l + size - 2, b + size - 2, (56, 66, 85), 2)
    rect(l + 4, b + size - 9, l + size - 4, b + size - 4, (72, 84, 106))
    rect(l + 4, b + 4, l + size - 4, b + 7, (37, 45, 64))


def keycap(font, x, y, key):
    bevel(x, y, x + 22, y + 19, GOLD, 2)
    rect(x + 1, y + 2, x + 21, y + 18, NAVY)
    text(font, x + 5, y + 10, key, WHITE)


def meter(l, b, width, height, value, maximum, color):
    ratio = max(0, min(1, value / maximum)) if maximum else 0
    bevel(l, b, l + width, b + height, (90, 85, 88), 3)
    rect(l + 2, b + 2, l + width - 2, b + height - 2, (45, 48, 61))
    end = l + 2 + (width - 4) * ratio
    rect(l + 2, b + 2, end, b + height - 2, color)
    highlight = tuple(min(255, c + 40) for c in color)
    rect(l + 2, b + height - 7, end, b + height - 3, highlight)
