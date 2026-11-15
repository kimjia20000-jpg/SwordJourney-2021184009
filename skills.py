import math
from pathlib import Path

from pico2d import load_image, draw_rectangle
from weapons import WEAPONS


# 모든 검이 공통으로 사용하는 스킬. 피해는 현재 기본 공격력에 비례한다.
SKILL_DATA = {
    "slash": {"name": "강화 베기", "key": "S", "level": 3,
              "mana": 10, "cooldown": 2.0, "duration": 0.50, "multiplier": 2.0},
    "wave": {"name": "검기 발사", "key": "D", "level": 5,
             "mana": 15, "cooldown": 3.0, "duration": 0.42, "multiplier": 1.5},
}
IMAGE_PATH = Path(__file__).resolve().parent / "assets" / "images" / "skill_effects.png"
EFFECT_RECTS = {"slash": (125, 92, 700, 791), "wave": (1130, 248, 1649, 648)}


def overlap(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


class SwordWave:
    """발사 방향을 유지하는 관통 검기. 몬스터별 한 번만 피해를 준다."""

    def __init__(self, x, y, direction, damage, scale=1.0):
        self.x, self.y = x, y
        self.direction = direction
        self.damage = damage
        self.speed = 620.0
        self.remaining_distance = 520.0
        self.width, self.height = 78.0 * scale, 60.0 * scale
        self.alive = True
        self.hit_targets = set()

    def update(self, dt, player, effects):
        old_x = self.x
        distance = min(self.speed * dt, self.remaining_distance)
        self.x += self.direction * distance
        self.remaining_distance -= distance
        # 이동 전후 범위를 합쳐 빠르게 날아가도 적을 건너뛰지 않는다.
        swept_box = (min(old_x, self.x) - self.width / 2, self.y - self.height / 2,
                     max(old_x, self.x) + self.width / 2, self.y + self.height / 2)
        for target in player.stage.slimes:
            if not target.alive or target in self.hit_targets:
                continue
            if overlap(swept_box, target.get_body_box()):
                if player.deal_damage(target, self.damage, self.direction):
                    self.hit_targets.add(target)
                    effects.add_hit(target.x, target.y + target.height / 2)
        if (self.remaining_distance <= 0
                or self.x < -self.width or self.x > player.stage.width + self.width):
            self.alive = False


class SkillController:
    def __init__(self, player):
        self.player = player
        self.image = load_image(str(IMAGE_PATH))
        self.cooldowns = {name: 0.0 for name in SKILL_DATA}
        self.active = None
        self.elapsed = 0.0
        self.direction = 1
        self.hit_targets = set()
        self.wave_launched = False
        self.cast_damage = 0
        self.cast_scale = 1.0
        self.waves = []
        self.hit_effects = []

    def try_cast(self, name):
        p, spec = self.player, SKILL_DATA[name]
        if not p.alive:
            return False
        if p.level < spec["level"]:
            p.show_notice(f'{spec["name"]}: {spec["level"]}레벨에 해금됩니다.')
            return False
        if p.hurt_remaining > 0 or self.active is not None:
            p.show_notice("현재 동작이 끝난 뒤 다시 사용하세요.")
            return False
        if self.cooldowns[name] > 0:
            p.show_notice(f'{spec["name"]}: {self.cooldowns[name]:.1f}초 후 사용 가능')
            return False
        if p.mp + 1e-9 < spec["mana"]:
            p.show_notice("마나가 부족합니다.")
            return False
        # 검증을 모두 통과한 경우에만 소모한다. 기본 공격보다 스킬을 우선한다.
        p.cancel_attack()
        p.mp = max(0.0, p.mp - spec["mana"])
        self.cooldowns[name] = spec["cooldown"]
        self.active, self.elapsed = name, 0.0
        input_direction = int(p.right_pressed) - int(p.left_pressed)
        if input_direction:
            p.face_direction = input_direction
        self.direction = p.face_direction
        self.cast_damage = round(p.attack_power * spec["multiplier"])
        self.cast_scale = WEAPONS[p.equipped_weapon]["skill_scale"]
        self.hit_targets.clear()
        self.wave_launched = False
        return True

    def cancel_cast(self):
        # 피격으로 취소해도 이미 사용한 마나/재사용 시간은 되돌리지 않는다.
        self.active = None
        self.elapsed = 0.0
        self.hit_targets.clear()

    def clear_on_death(self):
        self.cancel_cast()
        self.waves.clear()
        self.hit_effects.clear()

    @property
    def progress(self):
        if self.active is None:
            return 0.0
        return min(1.0, self.elapsed / SKILL_DATA[self.active]["duration"])

    def slash_geometry(self):
        # 그리는 크기와 판정 크기를 같은 계산에서 가져온다.
        p = self.player
        phase = max(0.0, min(1.0, (self.progress - 0.20) / 0.60))
        scale = (0.85 + 0.15 * math.sin(math.pi * phase)) * self.cast_scale
        width, height = 108.0 * scale, 112.0 * scale
        center_x = p.x + self.direction * (12 + width / 2)
        center_y = p.y + 54 - 10 * phase
        box = (center_x - width / 2, center_y - height / 2,
               center_x + width / 2, center_y + height / 2)
        return center_x, center_y, width, height, box

    def update(self, dt):
        p = self.player
        for name in self.cooldowns:
            self.cooldowns[name] = max(0.0, self.cooldowns[name] - dt)
        for effect in self.hit_effects:
            effect[2] += dt
        self.hit_effects[:] = [effect for effect in self.hit_effects if effect[2] < .16]

        if self.active is not None:
            self.elapsed += dt
            # 지상에서는 시전 방향 고정, 공중에서는 현재 입력을 따른다.
            direction = int(p.right_pressed) - int(p.left_pressed)
            if not p.on_ground and direction:
                self.direction = direction
            if self.active == "slash" and .20 <= self.progress < .80:
                box = self.slash_geometry()[4]
                for target in p.stage.slimes:
                    if not target.alive or target in self.hit_targets:
                        continue
                    if overlap(box, target.get_body_box()):
                        if p.deal_damage(target, self.cast_damage, self.direction):
                            self.hit_targets.add(target)
                            self.add_hit(target.x, target.y + target.height / 2)
            elif self.active == "wave" and self.progress >= .35 and not self.wave_launched:
                self.waves.append(SwordWave(
                    p.x + self.direction * 48, p.y + 42,
                    self.direction, self.cast_damage, self.cast_scale,
                ))
                self.wave_launched = True
            if self.progress >= 1.0:
                self.cancel_cast()

        # 이미 발사한 검기는 캐릭터가 돌아서거나 피격돼도 계속 날아간다.
        for wave in self.waves:
            wave.update(dt, p, self)
        self.waves[:] = [wave for wave in self.waves if wave.alive]

    def add_hit(self, x, y):
        self.hit_effects.append([x, y, 0.0])

    def draw_sprite(self, name, x, y, width, height, direction=1):
        left, top, right, bottom = EFFECT_RECTS[name]
        sx, sy = self.image.w / 1774, self.image.h / 887
        left, right = round(left * sx), round(right * sx)
        top, bottom = round(top * sy), round(bottom * sy)
        args = (left, self.image.h - bottom, right - left, bottom - top)
        if direction == 1:
            self.image.clip_draw(*args, x, y, width, height)
        else:
            self.image.clip_composite_draw(*args, 0, 'h', x, y, width, height)

    def draw(self, camera_x):
        if self.active == "slash" and .20 <= self.progress < .80:
            x, y, width, height, _ = self.slash_geometry()
            self.draw_sprite("slash", x - camera_x, y, width, height, self.direction)
        for wave in self.waves:
            self.draw_sprite("wave", wave.x - camera_x, wave.y,
                             wave.width, wave.height, wave.direction)
        for x, y, elapsed in self.hit_effects:
            radius = 4 + elapsed * 90
            for dx, dy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                px, py = round(x - camera_x + dx * radius), round(y + dy * radius)
                draw_rectangle(px - 1, py - 1, px + 1, py + 1,
                               194, 248, 255, filled=True)
