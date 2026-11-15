from pico2d import load_image, draw_rectangle
from stage import Stage, Platform, IMAGE_DIR
from portal import Portal
from navigation import PlatformRoutes
from wolf import WolfPack


class DeepForestStage(Stage):
    def __init__(self):
        super().__init__()
        self.number = 2
        self.width = 5120
        self.background = load_image(str(IMAGE_DIR / 'stage2_background.png'))
        self.wolf_image = load_image(str(IMAGE_DIR / 'wolf_sheet.png'))
        self.zones = ((0,1280,'그늘진 숲 입구'), (1280,2560,'얽힌 뿌리길'),
                      (2560,3840,'늑대의 사냥터'), (3840,5120,'고목의 안쪽'))
        # 바닥 우회로 + 중간 갈림길 + 위쪽 가지 길. 최대 높이 505.
        layouts = [(350,650,165),(550,950,250),(850,1200,335),(1050,1400,420),
            (1250,1500,250),(1400,1700,165),(1100,1370,165),
            (1600,1850,165),(1800,2200,250),(2030,2300,335),(2200,2600,420),
            (2340,2700,505),(2500,2800,250),(2700,2950,165),
            (2850,3100,165),(3060,3350,250),(3260,3600,335),(3470,3850,420),
            (3700,4050,250),(3880,4100,165),(3350,3630,165),
            (4050,4300,165),(4220,4580,250),(4380,4730,335),
            (4570,4950,420),(4830,5075,335),(4900,5120,250)]
        self.platforms = [Platform(0,self.width,80,80)] + [Platform(*p) for p in layouts]
        self.routes = PlatformRoutes(self.platforms)
        self.packs = [WolfPack(self,self.platforms[0],760),
                      WolfPack(self,self.platforms[9],2000),
                      WolfPack(self,self.platforms[0],3180),
                      WolfPack(self,self.platforms[24],4540)]
        self.monsters = [wolf for pack in self.packs for wolf in pack.members]
        self.initial_monster_count = len(self.monsters)
        self.portal = Portal(self.width-110,self.platforms[-1].top)
        self.rewards = {'heavy_sword':1,'hp_potion':3,'mp_potion':3}
        self.reward_labels = (('heavy_sword','묵직한 대검 ×1'),('hp_potion','체력 포션 ×3'),('mp_potion','마나 포션 ×3'))
        self.reward_equip_hint = 'I 가방 → 대검 더블클릭 장착 · 오른쪽 출구 개방'
        self.trees = []

    def update(self, dt, player=None):
        self.clear_banner_remaining = max(0,self.clear_banner_remaining-dt)
        self.portal.update(dt)
        if player is not None:
            for pack in self.packs:
                pack.update(dt,player)

    def draw_plants(self, camera):
        for i,p in enumerate(self.platforms):
            if not camera.visible(p.left,p.right):
                continue
            l,r = max(0,p.left-camera.x),min(camera.width,p.right-camera.x)
            # 이끼가 덮인 윗면과 뿌리 장식. 충돌 높이는 발판 top과 일치한다.
            draw_rectangle(round(l),round(p.top-3),round(r),round(p.top),78,118,83,filled=True)
            for x in range(int(p.left+30),int(p.right-15),165):
                if not camera.visible(x-10,x+10):
                    continue
                sx,y=round(x-camera.x),round(p.top)
                draw_rectangle(sx-2,y,sx+1,y+7,111,167,147,filled=True)
                draw_rectangle(sx-7,y+6,sx+6,y+10,116,172,190,filled=True)
                if i%3==0:
                    draw_rectangle(sx+29,y-18,sx+32,y-7,79,66,65,filled=True)
