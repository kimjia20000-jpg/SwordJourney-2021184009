from pico2d import draw_rectangle
from enemy_projectiles import RockProjectile, Shockwave
from ui_theme import panel, text, meter, WHITE

FRAMES=((92,121,400,487),(500,185,973,487),(1105,14,1439,487),
        (68,561,435,975),(524,680,959,975),(1044,722,1475,969))
ANCHORS=(245,805,1260,245,750,1270)


class Golem:
    def __init__(self,stage):
        self.stage,self.image=stage,stage.golem_image
        self.x,self.y=3470.0,80.0
        self.width,self.height=190,225
        self.hp=self.max_hp=900
        self.exp_reward=0
        self.alive=True
        self.active=False
        self.show_health_bar=False
        self.state='SLEEP'
        self.timer=0
        self.elapsed=0
        self.direction=-1
        self.pattern_index=0
        self.target=(0,80)
        self.hit_flash=0

    @property
    def contact_damage(self):
        return 22 if self.state=='CHARGE' and self.active else 0

    def get_contact_box(self):
        # 돌진은 무릎 높이의 판정을 사용해 점프로 피할 수 있다.
        return self.x-74,self.y,self.x+74,self.y+60

    def get_body_box(self):
        return self.x-73,self.y,self.x+73,self.y+210

    def take_damage(self,damage,attack_direction=None):
        if not self.active or not self.alive or damage<=0:return False
        self.hp=max(0,self.hp-damage)
        self.hit_flash=.12
        if self.hp==0:
            self.alive=False
            self.state='DEAD'
            self.stage.begin_clear()
        return True

    def awaken(self):
        self.active=True
        self.state='REST'
        self.timer=2.0

    def start_pattern(self,player):
        patterns=('CHARGE_READY','ROCK_READY','QUAKE_READY')
        self.state=patterns[self.pattern_index%3]
        self.pattern_index+=1
        self.direction=1 if player.x>self.x else -1
        self.target=(player.x,player.y+28)
        self.timer={'CHARGE_READY':1.0,'ROCK_READY':1.15,'QUAKE_READY':1.3}[self.state]

    def update(self,dt,player):
        if not self.alive or not self.active:return
        self.elapsed+=dt
        self.hit_flash=max(0,self.hit_flash-dt)
        self.timer-=dt
        if self.state=='CHARGE':
            self.x+=self.direction*460*dt
            self.x=max(self.stage.arena_left+110,min(self.stage.width-110,self.x))
        if self.timer>0:return
        if self.state=='REST':
            self.start_pattern(player)
        elif self.state=='CHARGE_READY':
            self.state='CHARGE';self.timer=1.0
        elif self.state=='ROCK_READY':
            self.state='ROCK';self.timer=.4
            self.stage.projectiles.append(RockProjectile(self.x+self.direction*70,self.y+245,*self.target,
                                                         damage=20,size=38,flight=1.1))
        elif self.state=='QUAKE_READY':
            self.state='QUAKE';self.timer=.4
            self.stage.projectiles.extend((Shockwave(self.x,-1),Shockwave(self.x,1)))
        else:
            self.state='REST'
            self.timer=1.0 if self.hp<=self.max_hp/2 else 1.5

    def draw(self,camera_x=0):
        if not self.alive and self.stage.victory_time>1.5:return
        if not self.alive:index=5
        elif self.state in ('CHARGE_READY','CHARGE'):index=1
        elif self.state=='ROCK_READY':index=2
        elif self.state=='QUAKE_READY':index=3
        elif self.state in ('QUAKE','ROCK'):index=4
        else:index=0
        l,t,r,b=FRAMES[index]
        sx,sy=self.image.w/1536,self.image.h/1024
        scale=.62
        if not self.alive:scale*=max(.65,1-self.stage.victory_time*.15)
        flip=self.direction==1
        center=self.x+(-1 if flip else 1)*((l+r)/2-ANCHORS[index])*scale
        w,h=(r-l)*scale,(b-t)*scale
        if self.hit_flash>0 and int(self.hit_flash*50)%2:return
        self.image.clip_composite_draw(round(l*sx),self.image.h-round(b*sy),round((r-l)*sx),round((b-t)*sy),
                                      0,'h' if flip else '',center-camera_x,self.y+h/2,w,h)

    def draw_warning(self,camera_x):
        if not self.alive:return
        if self.state=='CHARGE_READY':
            x=self.x-camera_x
            for d in range(110,550,45):
                point=round(x+self.direction*d)
                if 0<point<1280:
                    draw_rectangle(point-13,82,point+13,87,246,139,83,filled=True)
        elif self.state=='ROCK_READY':
            x=round(self.target[0]-camera_x)
            y=round(self.target[1]-28)
            draw_rectangle(x-35,y+2,x+35,y+6,247,167,86,filled=True)
            draw_rectangle(x-2,y+6,x+2,y+22,247,167,86,filled=True)
        elif self.state=='QUAKE_READY':
            for x in range(round(self.stage.arena_left-camera_x),1280,60):
                draw_rectangle(x,81,x+38,85,119,218,255,filled=True)

    def draw_health_bar(self,camera_x=0):
        pass  # 작은 몬스터 체력바 대신 상단 전용 UI를 사용한다.

    def draw_hud(self,font):
        if not self.active or (not self.alive and self.stage.victory_time>.6):return
        panel(370,633,962,704,dark=True)
        # 첫 자세에서 얼굴을 잘라 보스 초상화로 표시한다.
        sx,sy=self.image.w/1536,self.image.h/1024
        self.image.clip_draw(round(177*sx),self.image.h-round(202*sy),round(98*sx),round(85*sy),410,670,51,45)
        text(font,449,685,'고대 수정 골렘',WHITE)
        if self.hp<=self.max_hp/2 and self.alive:
            text(font,795,685,'핵 과열 · 2단계',(134,218,255))
        meter(449,649,495,23,self.hp,self.max_hp,(165,66,94))
        text(font,641,661,f'{self.hp} / {self.max_hp}',WHITE)
        hints={'CHARGE_READY':'몸을 낮춘다! 점프로 돌진을 피하세요.',
               'ROCK_READY':'바위를 들어 올린다! 표시된 위치에서 이동하세요.',
               'QUAKE_READY':'땅이 울린다! 충격파를 점프로 피하세요.',
               'REST':'공격 후 빈틈 · 지금 반격하세요.'}
        if self.state in hints:
            panel(408,588,932,624,dark=True)
            text(font,425,606,hints[self.state],(237,220,171))
