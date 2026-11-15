import math
from pico2d import draw_rectangle
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from skills import SKILL_DATA
from weapons import WEAPONS
from ui_theme import panel, title, text, rect, slot, keycap, meter, INK, MUTED, NAVY, GOLD, WHITE


def draw_player_status(player, stage, font):
    panel(16, 550, 354, 704)
    # 첫 대기 프레임에서 얼굴과 상체를 잘라 초상화로 사용한다.
    slot(28, 600, 76)
    player.image.clip_draw(103, player.image.h - 217, 166, 204, 66, 639, 65, 74)
    rect(30, 580, 102, 600, GOLD)
    rect(32, 582, 100, 598, NAVY)
    text(font, 38, 590, f'Lv. {player.level}', WHITE)
    text(font, 116, 682, '모험가', INK)
    text(font, 203, 682, f'공격력 {player.attack_power}', MUTED)
    for label, value, maximum, y, color in (
        ('HP', player.hp, player.max_hp, 649, (208, 66, 86)),
        ('MP', player.mp, player.max_mp, 621, (54, 120, 207)),
    ):
        meter(116, y, 224, 23, value, maximum, color)
        text(font, 124, y + 12, label, WHITE)
        text(font, 193, y + 12, f'{int(value)} / {maximum}', WHITE)
    meter(116, 600, 224, 13, player.exp, player.exp_to_next, (193, 151, 61))
    text(font, 116, 586, f'EXP  {player.exp} / {player.exp_to_next}', MUTED)
    weapon = WEAPONS[player.equipped_weapon]
    text(font, 30, 565, weapon['name'], INK)
    status = '교체 예약 중' if player.pending_weapon else weapon['speed_label'] + ' · ' + weapon['range_label']
    text(font, 220, 565, status, MUTED)


def draw_stage_header(stage, player, font):
    panel(452, 645, 828, 704, dark=True)
    text(font, 473, 683, f'STAGE {stage.number:02d}', (237, 202, 126))
    text(font, 584, 683, stage.zone_name(player.x), WHITE)
    remaining = stage.remaining_monsters
    label = f'{"늑대" if stage.number == 2 else "몬스터"} 처치  {stage.initial_monster_count - remaining} / {stage.initial_monster_count}' if remaining else '보상 수령 완료 · 출구 포탈 개방'
    text(font, 487, 660, label, (202, 211, 225))


def draw_skill_bar(player, font):
    panel(342, 6, 1008, 74)
    for index, (name, spec) in enumerate(SKILL_DATA.items()):
        l, b = 354 + index * 190, 14
        unlocked = player.level >= spec['level']
        cooldown = player.skills.cooldowns[name]
        ready = unlocked and cooldown <= 0 and player.mp >= spec['mana']
        slot(l, b, 52, hover=ready)
        player.skills.draw_sprite(name, l + 26, b + 29, 32, 37)
        keycap(font, l - 2, b - 1, spec['key'])
        text(font, l + 60, b + 37, spec['name'], INK if unlocked else MUTED)
        if not unlocked:
            status = f'Lv. {spec["level"]} 해금'
        elif cooldown > 0:
            status = f'대기 {cooldown:.1f}초'
        elif not ready:
            status = '마나 부족'
        else:
            status = f'MP {spec["mana"]} · 준비'
        text(font, l + 60, b + 14, status, (43, 105, 155) if ready else MUTED)
        if cooldown > 0:
            meter(l + 3, b + 23, 46, 6, cooldown, spec['cooldown'], (117, 156, 206))
        if not unlocked:
            text(font, l + 24, b + 9, str(spec['level']), (219, 207, 178))


def draw_skill_window(player, font):
    if not player.inventory.skill_visible or not player.alive:
        return
    panel(22, 124, 360, 425)
    title(font, 22, 360, 425, '전투 스킬', 'K 닫기')
    text(font, 40, 371, '모든 검 공통 · 레벨에 따라 해금', MUTED)
    for i, (name, spec) in enumerate(SKILL_DATA.items()):
        y = 260 - i * 106
        slot(40, y + 14, 56)
        player.skills.draw_sprite(name, 68, y + 44, 34, 40)
        keycap(font, 39, y + 12, spec['key'])
        unlocked = player.level >= spec['level']
        text(font, 109, y + 65, spec['name'], INK)
        text(font, 109, y + 42, f'Lv. {spec["level"]}  ·  MP {spec["mana"]}  ·  재사용 {spec["cooldown"]:g}초', MUTED)
        damage = round(player.attack_power * spec['multiplier'])
        text(font, 109, y + 19, f'피해 {damage}  ·  ' + ('해금 완료' if unlocked else '아직 잠긴 스킬'), (48, 111, 150) if unlocked else MUTED)
    text(font, 40, 140, '장착한 검에 따라 위력과 범위가 달라져요.', MUTED)


def draw_messages(player, font):
    if not player.alive:
        return
    if player.level_notice_remaining > 0:
        panel(432, 592, 848, 633, dark=True)
        text(font, 453, 613, player.level_notice, (255, 225, 137))
    if player.notice_remaining > 0:
        panel(392, 134, 908, 173, dark=True)
        text(font, 410, 154, player.notice, WHITE)


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
