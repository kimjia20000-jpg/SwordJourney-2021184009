from pico2d import draw_rectangle
from enemy_projectiles import RockProjectile

FRAMES=((157,181,493,501),(748,207,1182,506),(157,665,502,1073),(750,770,1227,1073))
ANCHORS=(325,970,325,1000)


class StoneMonster:
    def __init__(self,stage,platform,x,index):
        self.stage,self.platform,self.image=stage,platform,stage.stone_image
        self.x,self.y=float(x),float(platform.top)
        self.width,self.height=76,72
        self.hp=self.max_hp=75
        self.exp_reward,self.contact_damage=20,8
        self.alive=True
        self.show_health_bar=False
        self.direction=-1
        self.state='WAIT'
        self.timer=.65+index*.27
        self.hurt_remaining=0
        self.knockback=0
        self.target=(x,self.y)

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

    def update(self,dt,player):
        if not self.alive:return
        if self.hurt_remaining>0:
            self.hurt_remaining=max(0,self.hurt_remaining-dt)
            self.x+=self.knockback*dt
            self.knockback*=max(0,1-10*dt)
            self.x=max(self.platform.left+40,min(self.platform.right-40,self.x))
            return
        self.timer-=dt
        if self.state=='WAIT':
            if self.timer<=0 and abs(player.x-self.x)<520 and abs(player.y-self.y)<230:
                self.direction=1 if player.x>self.x else -1
                self.state='PICK';self.timer=.40
        elif self.state=='PICK' and self.timer<=0:
            self.state='AIM';self.timer=.55
            self.target=(player.x,player.y+30)
        elif self.state=='AIM' and self.timer<=0:
            self.state='THROW';self.timer=.25
            self.stage.projectiles.append(RockProjectile(self.x+self.direction*30,self.y+78,*self.target))
        elif self.state=='THROW' and self.timer<=0:
            self.state='WAIT';self.timer=1.8

    def draw(self,camera_x=0):
        if not self.alive:return
        frame={'WAIT':0,'PICK':1,'AIM':2,'THROW':3}[self.state]
        l,t,r,b=FRAMES[frame]
        sx,sy=self.image.w/1312,self.image.h/1199
        # 모든 자세에서 동일 배율과 몸 중심을 유지한다.
        scale=.225
        center=self.x+(1 if self.direction==-1 else -1)*((l+r)/2-ANCHORS[frame])*scale
        w,h=(r-l)*scale,(b-t)*scale
        if self.hurt_remaining>0 and int(self.hurt_remaining*40)%2:return
        self.image.clip_composite_draw(round(l*sx),self.image.h-round(b*sy),round((r-l)*sx),round((b-t)*sy),
                                      0,'' if self.direction==-1 else 'h',center-camera_x,self.y+h/2,w,h)

    def draw_health_bar(self,camera_x=0):
        if not self.alive or not self.show_health_bar:return
        x,y=round(self.x-camera_x-23),round(self.y+100)
        draw_rectangle(x-1,y-1,x+47,y+5,24,28,40,filled=True)
        draw_rectangle(x,y,x+46,y+4,65,71,88,filled=True)
        draw_rectangle(x,y,x+round(46*self.hp/self.max_hp),y+4,222,174,95,filled=True)
