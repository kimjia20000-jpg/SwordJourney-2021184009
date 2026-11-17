from pathlib import Path

from pico2d import draw_rectangle, load_image
from enemy_projectiles import RockProjectile

FRAMES=((157,181,493,501),(748,207,1182,506),(157,665,502,1073),(750,770,1227,1073))
ANCHORS=(325,970,325,1000)

MOVE_SPEED = 34.0
PATROL_RADIUS = 140.0
DETECT_X, DETECT_Y = 320.0, 150.0
LOSE_X, LOSE_Y = 380.0, 180.0



class StoneMonster:
    walk_image = None

    def __init__(self,stage,platform,x,index):
        self.stage,self.platform,self.image=stage,platform,stage.stone_image
        self.x,self.y=float(x),float(platform.top)
        self.width,self.height=76,72
        self.hp=self.max_hp=75
        self.exp_reward,self.contact_damage=20,8
        self.alive=True
        self.show_health_bar=False
        self.direction=-1
        self.state='PATROL'
        self.timer=.65+index*.27
        self.hurt_remaining=0
        self.knockback=0
        self.target=(x,self.y)
        # 발판 가장자리와 생성 위치 주변으로 순찰 범위를 제한한다.
        self.left_limit=max(platform.left+42, x-PATROL_RADIUS)
        self.right_limit=min(platform.right-42, x+PATROL_RADIUS)
        if self.left_limit>self.right_limit:
            self.left_limit=self.right_limit=(platform.left+platform.right)/2
        self.x=max(self.left_limit,min(self.right_limit,self.x))
        if StoneMonster.walk_image is None:
            StoneMonster.walk_image=load_image(str(
                Path(__file__).resolve().parent/'assets'/'images'/'stone_walk_sheet.png'))
        self.walk_frame=0.0
        self.walking=False

    def get_body_box(self):
        return self.x-29,self.y,self.x+29,self.y+62

    def take_damage(self,damage,attack_direction=None):
        if not self.alive or damage<=0:return False
        self.hp=max(0,self.hp-damage)
        self.show_health_bar=True
        self.alive=self.hp>0
        self.hurt_remaining=.2
        self.knockback=(attack_direction or 1)*135
        self.state='WAIT';self.timer=.65
        return True

    def player_in_range(self,player,range_x,range_y):
        # 거리 기반 감지이며 장애물 시야 차단은 적용하지 않는다.
        return (getattr(player,'hp',1)>0
                and abs(player.x-self.x)<=range_x
                and abs(player.y-self.y)<=range_y)

    def patrol(self,dt):
        if self.right_limit<=self.left_limit:return
        old_x=self.x
        self.x+=self.direction*MOVE_SPEED*dt
        if self.x<=self.left_limit:
            self.x=self.left_limit
            self.direction=1
        elif self.x>=self.right_limit:
            self.x=self.right_limit
            self.direction=-1
        distance=abs(self.x-old_x)
        self.walking=distance>0
        self.walk_frame=(self.walk_frame+distance/34.0*6.0)%6

    def update(self,dt,player):
        if not self.alive:return
        self.walking=False
        if self.hurt_remaining>0:
            self.hurt_remaining=max(0,self.hurt_remaining-dt)
            self.x+=self.knockback*dt
            self.knockback*=max(0,1-10*dt)
            self.x=max(self.left_limit,min(self.right_limit,self.x))
            return
        self.timer=max(0,self.timer-dt)
        nearby=self.player_in_range(player,DETECT_X,DETECT_Y)
        retained=self.player_in_range(player,LOSE_X,LOSE_Y)

        if self.state=='PATROL':
            if nearby:
                self.state='WAIT'
            else:
                self.patrol(dt)
                return

        # 감지/해제 범위를 다르게 해 경계에서 행동이 반복 전환되지 않게 한다.
        if self.state in ('WAIT','PICK','AIM') and not retained:
            self.state='PATROL'
            self.timer=max(self.timer,.4)
            self.patrol(dt)
            return

        if self.state=='WAIT':
            if player.x!=self.x:
                self.direction=1 if player.x>self.x else -1
            if self.timer<=0:
                self.state='PICK';self.timer=.40
        elif self.state=='PICK' and self.timer<=0:
            self.state='AIM';self.timer=.55
            # 조준 순간의 위치로 던지므로 플레이어가 피할 수 있다.
            self.target=(player.x,player.y+30)
            self.direction=1 if player.x>=self.x else -1
        elif self.state=='AIM' and self.timer<=0:
            self.state='THROW';self.timer=.25
            self.stage.projectiles.append(RockProjectile(
                self.x+self.direction*30,self.y+78,*self.target))
        elif self.state=='THROW' and self.timer<=0:
            self.state='WAIT' if retained else 'PATROL'
            self.timer=1.8

    def draw(self,camera_x=0):
        if not self.alive:return
        if self.hurt_remaining>0 and int(self.hurt_remaining*40)%2:return
        if self.walking:
            # 3열 x 2행. 프레임마다 몸 중심과 발바닥 높이를 정렬한다.
            image=StoneMonster.walk_image
            frame=int(self.walk_frame)%6
            col,row=frame%3,frame//3
            cw,ch=image.w//3,image.h//2
            anchors=(270,263,256,262,266,266)
            baselines=(410,410,410,415,415,415)
            scale=72.0/310.0
            offset=(256-anchors[frame])*scale
            center=self.x+(offset if self.direction==-1 else -offset)
            center_y=self.y+(baselines[frame]-256)*scale
            image.clip_composite_draw(col*cw,(1-row)*ch,cw,ch,
                0,'' if self.direction==-1 else 'h',center-camera_x,center_y,
                512*scale,512*scale)
            return
        frame={'PATROL':0,'WAIT':0,'PICK':1,'AIM':2,'THROW':3}[self.state]
        l,t,r,b=FRAMES[frame]
        sx,sy=self.image.w/1312,self.image.h/1199
        # 모든 자세에서 동일 배율과 몸 중심을 유지한다.
        scale=.225
        center=self.x+(1 if self.direction==-1 else -1)*((l+r)/2-ANCHORS[frame])*scale
        w,h=(r-l)*scale,(b-t)*scale
        self.image.clip_composite_draw(round(l*sx),self.image.h-round(b*sy),round((r-l)*sx),round((b-t)*sy),
                                      0,'' if self.direction==-1 else 'h',center-camera_x,self.y+h/2,w,h)

    def draw_health_bar(self,camera_x=0):
        if not self.alive or not self.show_health_bar:return
        x,y=round(self.x-camera_x-23),round(self.y+100)
        draw_rectangle(x-1,y-1,x+47,y+5,24,28,40,filled=True)
        draw_rectangle(x,y,x+46,y+4,65,71,88,filled=True)
        draw_rectangle(x,y,x+round(46*self.hp/self.max_hp),y+4,222,174,95,filled=True)
