from pico2d import load_image, draw_rectangle
from stage import Stage, Platform, IMAGE_DIR
from stone_monster import StoneMonster
from golem import Golem
from ui_theme import panel, text, WHITE


class CavePlatform(Platform):
    def draw(self,image,camera):
        if not camera.visible(self.left,self.right):return
        l=max(0,self.left-camera.x);r=min(camera.width,self.right-camera.x)
        y=self.top
        draw_rectangle(round(l),round(y-self.thickness),round(r),round(y),47,49,70,filled=True)
        draw_rectangle(round(l),round(y-6),round(r),round(y),134,143,166,filled=True)
        draw_rectangle(round(l),round(y-11),round(r),round(y-6),76,85,113,filled=True)
        for x in range(int(self.left),int(self.right),90):
            sx=round(x-camera.x)
            if 0<=sx<=camera.width:
                draw_rectangle(sx,round(y-self.thickness),sx+2,round(y-12),30,35,53,filled=True)


class CaveStage(Stage):
    def __init__(self):
        super().__init__()
        self.number=3
        self.width=3840
        self.background=load_image(str(IMAGE_DIR/'cave_background.png'))
        self.stone_image=load_image(str(IMAGE_DIR/'stone_sheet.png'))
        self.golem_image=load_image(str(IMAGE_DIR/'golem_sheet.png'))
        self.zones=((0,1280,'수정 동굴 입구'),(1280,2560,'바위 수호자의 길'),(2560,3840,'고대 골렘의 방'))
        self.arena_left=2560
        self.arena_started=False
        self.victory_time=0.0
        self.projectiles=[]
        self.platforms=[CavePlatform(0,self.width,80,80)]
        self.platforms.extend(CavePlatform(*v) for v in (
            (370,630,165),(800,1110,165),(1000,1270,250),
            (1430,1660,165),(1640,1930,250),(1880,2120,335),
            (2150,2420,165),(2690,2870,165),(3540,3750,165)))
        locations=((0,660),(2,950),(0,1320),(5,1780),(0,2050),(7,2290),(8,2780),(9,3660))
        self.monsters=[StoneMonster(self,self.platforms[index],x,i) for i,(index,x) in enumerate(locations)]
        self.boss=Golem(self)
        self.monsters.append(self.boss)
        self.initial_monster_count=len(self.monsters)
        self.trees=[]

    def update(self,dt,player=None):
        if self.cleared:
            self.victory_time+=dt
            return
        if player is None:return
        if not self.arena_started and player.x>=self.arena_left+45:
            self.arena_started=True
            self.projectiles.clear()
            self.boss.awaken()
            player.invincible_remaining=max(player.invincible_remaining,1.0)
        for monster in self.monsters:
            if self.arena_started and monster is not self.boss and monster.x<self.arena_left:
                continue
            monster.update(dt,player)
        for projectile in self.projectiles:
            if projectile.alive:projectile.update(dt,player,self)
        self.projectiles[:]=[p for p in self.projectiles if p.alive]

    def constrain_player(self,player):
        if self.arena_started and not self.cleared:
            player.x=max(self.arena_left+38,min(self.width-player.half_width,player.x))

    def begin_clear(self):
        if self.cleared:return
        self.cleared=True
        self.victory_time=0
        self.projectiles.clear()
        # 보스 사망 순간 남아 있는 일반 적도 비활성화한다.
        for monster in self.monsters:
            if monster is not self.boss:monster.alive=False

    def resolve_clear(self,player):
        if self.cleared:
            player.cancel_attack()
            player.skills.clear_on_death()
            player.inventory.close()
            player.left_pressed=player.right_pressed=player.attack_pressed=False
            player.hurt_remaining=player.invincible_remaining=0
            player.notice_remaining=player.level_notice_remaining=0
            player.motion='IDLE';player.frame=0
        return False

    def handle_portal_event(self,event,player):
        return False

    def draw(self,camera):
        self.draw_background(camera)
        for platform in self.platforms:platform.draw(None,camera)
        for x in (320,750,1250,1600,2040,2470,2700,3780):
            sx=round(x-camera.x)
            if 0<sx<1280:
                draw_rectangle(sx-8,80,sx+8,113,71,133,195,filled=True)
                draw_rectangle(sx-3,87,sx+3,121,147,225,245,filled=True)
        if self.arena_started and not self.cleared:
            x=round(self.arena_left-camera.x)
            draw_rectangle(x,80,x+13,340,52,105,145,filled=True)
            draw_rectangle(x+5,80,x+8,340,117,207,235,filled=True)
        self.boss.draw_warning(camera.x)
        for monster in self.monsters:
            if monster is not self.boss and camera.visible(monster.x-100,monster.x+100):
                monster.draw(camera.x)
        if camera.visible(self.boss.x-240,self.boss.x+240):self.boss.draw(camera.x)
        for projectile in self.projectiles:projectile.draw(camera.x)

    def draw_status(self,player,normal_font,title_font):
        if not self.cleared:return
        if self.victory_time<2.2:
            panel(465,360,815,421,dark=True)
            text(normal_font,522,390,'고대 수정 골렘 처치!',(255,225,145))
        else:
            panel(370,240,910,485,dark=True)
            title_font.draw(478,435,'검의 여정 완료',(255,225,145))
            text(normal_font,478,386,'동굴의 수호자 골렘을 쓰러뜨렸습니다.',WHITE)
            text(normal_font,493,351,f'최종 레벨 {player.level} · 세 지역 정복 완료',(151,219,247))
            text(normal_font,483,296,'Enter 처음부터 다시 시작   /   ESC 종료',WHITE)
