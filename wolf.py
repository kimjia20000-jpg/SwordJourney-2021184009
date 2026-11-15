import math
from pico2d import draw_rectangle
from navigation import JUMP, GRAVITY

# 원본 1536x1024에서 실제 몸만 잘라낸 좌표. 이미지 자체는 수정하지 않는다.
FRAMES = ((18,82,470,422), (510,121,991,420), (1038,121,1508,420),
          (18,628,504,890), (525,644,1006,922), (1065,636,1484,923))


class WolfPack:
    def __init__(self, stage, platform, center):
        self.stage, self.home_platform, self.center = stage, platform, center
        self.mode = 'PATROL'
        self.memory = 0.0
        self.elapsed = 0.0
        self.members = [Wolf(self, center + offset, index) for index, offset in enumerate((-95, 0, 95))]

    def alert(self):
        self.mode = 'CHASE'
        self.memory = 2.5

    def update(self, dt, player):
        self.elapsed += dt
        living = [wolf for wolf in self.members if wolf.alive]
        if not living:
            return
        in_territory = player.alive and abs(player.x - self.center) <= 820
        sees = in_territory and any(abs(w.x - player.x) <= 280 and abs(w.y - player.y) <= 110 for w in living)
        if sees:
            self.alert()
        elif self.mode == 'CHASE':
            self.memory = max(0, self.memory - dt)
            if not in_territory or self.memory <= 0:
                self.mode = 'RETURN'
        elif self.mode == 'RETURN':
            if all(w.on_ground and w.platform is self.home_platform and abs(w.x - w.home_x) < 14 for w in living):
                self.mode = 'PATROL'
        for wolf in living:
            wolf.update(dt, player)


class Wolf:
    def __init__(self, pack, x, index):
        self.pack, self.stage, self.index = pack, pack.stage, index
        self.image = self.stage.wolf_image
        self.home_x = self.x = float(x)
        self.platform = pack.home_platform
        self.y = float(self.platform.top)
        self.width, self.height = 88, 58
        self.max_hp = self.hp = 60
        self.exp_reward, self.contact_damage = 20, 15
        self.alive, self.show_health_bar = True, False
        self.direction = 1
        self.on_ground = True
        self.velocity_y = self.velocity_x = 0.0
        self.hurt_remaining = 0.0
        self.attack_time = self.attack_cooldown = 0.0
        self.elapsed = 0.0
        self.air_target = self.x
        self.ignore_platform = None
        self.ignore_time = 0.0
        self.moving = False

    def get_body_box(self):
        return self.x - 32, self.y, self.x + 32, self.y + 48

    def take_damage(self, damage, attack_direction=None):
        if not self.alive or damage <= 0:
            return False
        self.pack.alert()
        self.hp = max(0, self.hp - damage)
        self.show_health_bar = True
        if self.hp == 0:
            self.alive = False
            return True
        self.hurt_remaining = .24
        self.attack_time = 0.0
        self.velocity_x = (1 if (attack_direction or -self.direction) > 0 else -1) * 240
        self.velocity_y = 145.0
        self.on_ground = False
        self.air_target = self.x + self.velocity_x * .12
        return True

    def move_toward(self, x, speed, dt):
        delta = x - self.x
        if abs(delta) > 2:
            self.direction = 1 if delta > 0 else -1
            step = min(abs(delta), speed * dt)
            self.x += self.direction * step
            self.moving = True

    def update(self, dt, player):
        if not self.alive:
            return
        self.elapsed += dt
        self.moving = False
        self.attack_time = max(0, self.attack_time - dt)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.ignore_time = max(0, self.ignore_time - dt)
        if self.ignore_time <= 0:
            self.ignore_platform = None
        if self.hurt_remaining > 0:
            self.hurt_remaining = max(0, self.hurt_remaining - dt)
            self.x += self.velocity_x * dt
            self.velocity_x *= max(0, 1 - 9 * dt)
        elif not self.on_ground:
            self.move_toward(self.air_target, 185, dt)
        else:
            self.navigate(player, dt)
        self.x = max(44, min(self.stage.width - 44, self.x))
        old_y = self.y
        self.y += self.velocity_y * dt - .5 * GRAVITY * dt * dt
        self.velocity_y -= GRAVITY * dt
        self.on_ground = False
        if self.velocity_y <= 0:
            landing = self.stage.find_landing(self.x, 12, old_y, self.y, self.ignore_platform)
            if landing is not None:
                self.y = float(landing.top)
                self.velocity_y = 0
                self.on_ground = True
                self.platform = landing
        # 공중에서도 해당 지형에 실제로 닿아야 착지한다.

    def navigate(self, player, dt):
        mode = self.pack.mode
        if mode == 'PATROL':
            target_platform = self.pack.home_platform
            offset = math.sin(self.pack.elapsed * .55) * 75
            target_x = self.home_x + offset
            speed = 62
        elif mode == 'RETURN':
            target_platform, target_x, speed = self.pack.home_platform, self.home_x, 125
        else:
            target_platform = self.stage.routes.locate(player.x, player.y)
            # 각 개체가 조금 다른 간격으로 접근한다. 접촉 직전에는 모두 물기 거리까지 접근.
            distance = abs(player.x - self.x)
            side = 1 if self.x > player.x else -1
            target_x = player.x + side * (20 + self.index * 32)
            speed = 185 + self.index * 8
            if distance < 110 and abs(player.y - self.y) < 35 and self.attack_cooldown <= 0:
                self.attack_time = .30
                self.attack_cooldown = 1.0 + self.index * .12
            if self.attack_time > 0:
                target_x = player.x
                speed = 225
        target_x = max(target_platform.left + 28, min(target_platform.right - 28, target_x))
        if self.platform is target_platform:
            self.move_toward(target_x, speed, dt)
            return
        step = self.stage.routes.next_step(self.platform, target_platform)
        if step is None:
            return
        nxt, takeoff, landing_x, drop = step
        # 같은 높이에서 이어진 발판은 점프하지 않고 경계를 걸어서 넘는다.
        if abs(nxt.top - self.platform.top) < 1 and nxt.left <= self.platform.right and nxt.right >= self.platform.left:
            self.move_toward((nxt.left + nxt.right) / 2, speed, dt)
            return
        if abs(self.x - takeoff) > 4:
            self.move_toward(takeoff, speed, dt)
            return
        self.air_target = landing_x
        self.velocity_y = -45 if drop else JUMP
        if drop:
            self.ignore_platform = self.platform
            self.ignore_time = .35
        self.on_ground = False

    def draw(self, camera_x=0):
        if not self.alive:
            return
        index = 5 if self.hurt_remaining > 0 else 4 if self.attack_time > 0 else (1 + int(self.elapsed * 10) % 3) if self.moving or not self.on_ground else 0
        left, top, right, bottom = FRAMES[index]
        sx, sy = self.image.w / 1536, self.image.h / 1024
        left, right, top, bottom = round(left*sx), round(right*sx), round(top*sy), round(bottom*sy)
        width = 88
        height = width * (bottom-top) / (right-left)
        self.image.clip_composite_draw(left, self.image.h-bottom, right-left, bottom-top,
            0, '' if self.direction == 1 else 'h', self.x-camera_x, self.y+height/2, width, height)
        if self.pack.mode == 'CHASE' and self.hurt_remaining <= 0:
            x, y = round(self.x-camera_x), round(self.y+height+12)
            draw_rectangle(x-1,y,x+1,y+7,255,184,87,filled=True)
            draw_rectangle(x-1,y-4,x+1,y-2,255,184,87,filled=True)

    def draw_health_bar(self, camera_x=0):
        if not self.alive or not self.show_health_bar:
            return
        x, y = round(self.x-camera_x-22), round(self.y+77)
        draw_rectangle(x-1,y-1,x+45,y+5,23,28,40,filled=True)
        draw_rectangle(x,y,x+44,y+4,74,72,80,filled=True)
        if self.hp:
            draw_rectangle(x,y,x+round(44*self.hp/self.max_hp),y+4,224,91,94,filled=True)
