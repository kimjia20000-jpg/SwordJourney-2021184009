import math

from pico2d import draw_rectangle
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from skills import SKILL_DATA
from weapons import WEAPONS


def bar(font, label, value, maximum, y, color):
    left, right, height = 82, 306, 20
    font.draw(28, y + 9, label, (225, 233, 222))
    draw_rectangle(left, y, right, y + height, 52, 62, 59, filled=True)
    width = round((right - left) * max(0.0, min(1.0, value / maximum)))
    if width > 0:
        draw_rectangle(left, y, left + width, y + height, *color, filled=True)
    font.draw(left + 8, y + 10, f"{int(value)} / {maximum}", (255, 255, 255))


def draw_player_status(player, stage, font):
    top = SCREEN_HEIGHT - 16
    draw_rectangle(16, top - 183, 322, top, 25, 40, 35, filled=True)
    draw_rectangle(16, top - 183, 322, top, 105, 141, 116)
    font.draw(28, top - 22, f"레벨 {player.level}  ·  모험가", (255, 227, 145))
    bar(font, "체력", player.hp, player.max_hp, top - 65, (195, 67, 63))
    bar(font, "마나", player.mp, player.max_mp, top - 96, (49, 112, 196))
    bar(font, "경험", player.exp, player.exp_to_next, top - 127, (155, 125, 45))
    font.draw(28, top - 160,
              f"남은 몬스터  {stage.remaining_monsters} / {stage.initial_monster_count}",
              (235, 239, 219))

    weapon = WEAPONS[player.equipped_weapon]
    draw_rectangle(16, top - 233, 322, top - 192, 25, 40, 35, filled=True)
    font.draw(28, top - 214, f'{weapon["name"]} · 공격력 {weapon["damage"]}', (231, 215, 159))
    if player.pending_weapon is not None:
        draw_rectangle(16, top - 272, 322, top - 239, 25, 40, 35, filled=True)
        font.draw(28, top - 256, f'예약: {WEAPONS[player.pending_weapon]["name"]}', (145, 217, 248))


def draw_skill_bar(player, font):
    # 바닥 높이 80보다 아래에 배치해 전투 화면을 가리지 않는다.
    for index, (name, spec) in enumerate(SKILL_DATA.items()):
        left, bottom = 374 + index * 266, 8
        right, top = left + 250, bottom + 62
        unlocked = player.level >= spec["level"]
        cooldown = player.skills.cooldowns[name]
        color = (103, 185, 219) if unlocked else (92, 104, 98)
        draw_rectangle(left, bottom, right, top, 24, 39, 36, filled=True)
        draw_rectangle(left, bottom, right, top, *color)
        player.skills.draw_sprite(name, left + 32, bottom + 34, 36, 44)
        font.draw(left + 59, bottom + 43, f'{spec["key"]}  {spec["name"]}',
                  (238, 245, 242) if unlocked else (150, 160, 153))
        if not unlocked:
            status = f'{spec["level"]}레벨 해금'
        elif cooldown > 0:
            status = f'대기 {math.ceil(cooldown * 10) / 10:.1f}초'
        elif player.mp + 1e-9 < spec["mana"]:
            status = f'마나 부족 ({spec["mana"]})'
        else:
            status = f'마나 {spec["mana"]} · 사용 가능'
        font.draw(left + 59, bottom + 18, status, (168, 215, 240) if unlocked else (150, 160, 153))


def draw_messages(player, font):
    if not player.alive:
        return
    if player.level_notice_remaining > 0:
        draw_rectangle(400, SCREEN_HEIGHT - 104, 880, SCREEN_HEIGHT - 63,
                       40, 49, 29, filled=True)
        font.draw(418, SCREEN_HEIGHT - 84, player.level_notice, (255, 232, 137))
    if player.notice_remaining > 0:
        draw_rectangle(400, 144, 910, 185, 25, 40, 35, filled=True)
        font.draw(418, 164, player.notice, (210, 239, 251))


def draw_level_effect(player, camera_x):
    if not player.alive or player.level_notice_remaining <= 0:
        return
    # 레벨업 초기 1.2초 동안 몸 양옆으로 금빛 입자가 올라간다.
    elapsed = 2.5 - player.level_notice_remaining
    if elapsed < 0 or elapsed > 1.2:
        return
    for i in range(6):
        phase = (elapsed * 0.9 + i / 6) % 1.0
        x = round(player.x - camera_x + (-1 if i % 2 else 1) * (23 + i * 2))
        y = round(player.y + phase * 110)
        draw_rectangle(x - 1, y - 3, x + 1, y + 3, 255, 223, 112, filled=True)
