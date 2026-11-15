from pico2d import draw_rectangle
from skills import overlap


class RockProjectile:
    def __init__(self, x, y, target_x, target_y, damage=12, size=18, flight=.9):
        self.x,self.y = x,y
        self.old_x,self.old_y = x,y
        self.gravity = 950.0
        self.vx = (target_x-x)/flight
        self.vy = (target_y-y+.5*self.gravity*flight*flight)/flight
        self.damage,self.size = damage,size
        self.alive = True
        self.life = 3.0

    def update(self,dt,player,stage):
        self.life -= dt
        ox,oy=self.x,self.y
        self.x += self.vx*dt
        self.y += self.vy*dt-.5*self.gravity*dt*dt
        self.vy -= self.gravity*dt
        radius=self.size/2
        box=(min(ox,self.x)-radius,min(oy,self.y)-radius,
             max(ox,self.x)+radius,max(oy,self.y)+radius)
        if overlap(box,player.get_body_box()):
            player.take_damage(self.damage,source_x=ox)
            self.alive=False
        # 바닥과 실제 발판에 닿으면 부서진다. 위쪽으로 던질 때는 통과한다.
        if self.vy <= 0 and stage.find_landing(self.x,radius,oy-radius,self.y-radius) is not None:
            self.alive=False
        if self.life<=0 or self.y<60 or not -60<self.x<stage.width+60:
            self.alive=False

    def draw(self,camera_x):
        if not self.alive:return
        x,y,r=round(self.x-camera_x),round(self.y),self.size/2
        for dx,dy,w,h,color in ((0,0,r,r,(34,38,54)),(0,0,r-2,r-2,(131,139,160)),
                              (-r*.22,r*.25,r*.5,r*.35,(183,193,205)),(r*.3,-r*.35,r*.4,r*.24,(82,89,112))):
            draw_rectangle(round(x+dx-w),round(y+dy-h),round(x+dx+w),round(y+dy+h),*color,filled=True)


class Shockwave:
    def __init__(self,x,direction):
        self.x=x
        self.direction=direction
        self.alive=True
        self.life=2.8

    def update(self,dt,player,stage):
        old=self.x
        self.x+=self.direction*360*dt
        self.life-=dt
        box=(min(old,self.x)-25,80,max(old,self.x)+25,113)
        if overlap(box,player.get_body_box()):
            player.take_damage(26,source_x=old)
        if self.life<=0 or not stage.arena_left<=self.x<=stage.width:
            self.alive=False

    def draw(self,camera_x):
        x=round(self.x-camera_x)
        for offset,height in ((-18,13),(0,30),(18,18)):
            draw_rectangle(x+offset-7,80,x+offset+7,80+height,105,177,222,filled=True)
            draw_rectangle(x+offset-3,80,x+offset+3,77+height,204,237,252,filled=True)
