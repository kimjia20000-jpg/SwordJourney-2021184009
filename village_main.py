from pico2d import (
    open_canvas,
    close_canvas,
    clear_canvas,
    update_canvas,
    get_events,
    get_time,
    delay,
    load_image,
    SDL_QUIT,
    SDL_KEYDOWN,
    SDLK_ESCAPE,
    SDLK_RETURN,
    SDLK_F6,
    SDLK_UP,
    SDLK_e,
)

import main as original_game

from camera import Camera
from hud import (
    draw_player_status,
    draw_skill_bar,
    draw_messages,
    draw_level_effect,
    draw_skill_window,
)
from minimap import Minimap
from player import Player
from portal import Portal
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GROUND_Y
from stage import Stage, Platform, IMAGE_DIR
from stage2 import DeepForestStage
from stage3 import CaveStage
from ui_theme import panel, rect, text, GOLD, WHITE


# True일 때 F6으로 현재 의뢰 지역을 건너뛸 수 있다.
# 정상적인 퀘스트 흐름을 확인할 때는 False로 둔다.
DEBUG_STAGE_SKIP = False


QUESTS = {
    1: {
        "title": "초원 길을 열어 줘",
        "destination": "슬라임 지대",
        "dialogue": (
            "마을 밖 풀밭에 슬라임이 잔뜩 모였단다.",
            "아이들이 다시 다닐 수 있게 슬라임을 모두 물리쳐 주겠니?",
        ),
        "departure": "첫 번째 의뢰 · 초원의 슬라임을 모두 처치하세요.",
    },
    2: {
        "title": "깊은 숲의 늑대 떼",
        "destination": "깊은 숲",
        "dialogue": (
            "덕분에 아이들이 다시 풀밭에서 놀 수 있게 됐단다.",
            "이번엔 나무꾼들이 돌아올 수 있게 숲길의 늑대 떼를 부탁하마.",
        ),
        "departure": "두 번째 의뢰 · 깊은 숲의 늑대 떼를 처치하세요.",
    },
    3: {
        "title": "동굴에서 들리는 소리",
        "destination": "골렘 동굴",
        "dialogue": (
            "숲길을 열어 줘서 고맙구나. 그런데 밤마다 땅이 울리는구나.",
            "숲 너머 동굴로 가서 안쪽의 골렘을 쓰러뜨려 주겠니?",
        ),
        "departure": "마지막 의뢰 · 동굴 안쪽의 골렘을 쓰러뜨리세요.",
    },
}


def draw_house(center_x, ground_y, roof_color):
    """마을 배경에 목조 주택 한 채를 그린다."""
    x = center_x
    y = ground_y

    wood = (92, 65, 49)
    wall = (238, 210, 158)
    window = (255, 224, 143)

    # 집의 외벽과 나무 기둥
    rect(x - 87, y, x + 87, y + 108, wood)
    rect(x - 80, y + 6, x + 80, y + 103, wall)

    for offset in (-72, 0, 65):
        rect(x + offset, y + 6, x + offset + 7, y + 104, wood)

    # 굴뚝을 먼저 그려서 아래쪽이 지붕에 가려지도록 한다.
    rect(x + 42, y + 110, x + 60, y + 168, (132, 94, 77))
    rect(x + 39, y + 164, x + 63, y + 172, (100, 76, 67))

    # 계단처럼 폭이 줄어드는 픽셀 지붕
    for row in range(10):
        half_width = 103 - row * 8
        bottom = y + 101 + row * 6
        rect(x - half_width, bottom, x + half_width, bottom + 6, roof_color)

    # 현관과 손잡이
    rect(x - 19, y, x + 17, y + 63, wood)
    rect(x - 13, y + 3, x + 12, y + 58, (137, 94, 61))
    rect(x + 5, y + 28, x + 9, y + 32, GOLD)

    # 양쪽 창문
    for offset in (-54, 46):
        wx = x + offset
        rect(wx - 14, y + 44, wx + 14, y + 76, wood)
        rect(wx - 10, y + 48, wx + 10, y + 72, window)
        rect(wx - 2, y + 47, wx + 2, y + 73, wood)
        rect(wx - 10, y + 58, wx + 10, y + 62, wood)


def draw_elder(x, y):
    """새 이미지 파일 없이 흰 수염과 지팡이를 가진 촌장을 그린다."""
    boots = (77, 58, 46)
    robe = (61, 101, 104)
    skin = (229, 181, 136)
    hair = (228, 225, 206)

    rect(x - 15, y, x - 4, y + 22, boots)
    rect(x + 3, y, x + 14, y + 22, boots)

    rect(x - 19, y + 14, x + 19, y + 54, robe)
    rect(x - 5, y + 14, x + 2, y + 53, (170, 159, 100))
    rect(x - 19, y + 30, x + 19, y + 35, (100, 74, 51))

    rect(x - 12, y + 51, x + 13, y + 74, skin)
    rect(x - 15, y + 70, x + 15, y + 79, hair)
    rect(x - 14, y + 63, x - 9, y + 73, hair)
    rect(x + 9, y + 63, x + 14, y + 73, hair)
    rect(x - 7, y + 64, x - 4, y + 67, boots)
    rect(x + 4, y + 64, x + 7, y + 67, boots)
    rect(x - 9, y + 50, x + 10, y + 59, hair)
    rect(x - 5, y + 46, x + 6, y + 53, hair)

    rect(x + 23, y, x + 27, y + 56, (108, 75, 47))
    rect(x + 19, y + 53, x + 27, y + 59, (108, 75, 47))
    rect(x + 16, y + 38, x + 25, y + 45, skin)


class Village(Stage):
    """몬스터가 없는 시작 마을. 의뢰를 받으면 출구 포탈이 열린다."""

    def __init__(self, quest_number=1):
        # Stage.__init__()는 슬라임과 전투 발판도 생성한다.
        # 마을에서는 필요한 지형과 포탈만 직접 준비한다.
        self.number = 0
        self.quest_number = quest_number
        self.quest = QUESTS[quest_number]
        self.accepted = False
        self.next_stage_requested = False

        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.elder_x = 602

        # 첫 시작은 마을 입구, 의뢰를 끝내고 돌아오면 촌장 근처.
        self.spawn_x = 210 if quest_number == 1 else self.elder_x - 74
        self.spawn_y = GROUND_Y

        self.background = load_image(str(IMAGE_DIR / "stage1_background.png"))
        self.platform_image = load_image(str(IMAGE_DIR / "grass_platform.png"))
        self.platforms = [Platform(0, self.width, GROUND_Y, GROUND_Y)]
        self.monsters = []
        self.portal = Portal(self.width - 140, GROUND_Y)

    def near_elder(self, player):
        return player.on_ground and abs(player.x - self.elder_x) <= 100

    def handle_portal_event(self, event, player):
        if event.type == SDL_KEYDOWN and event.key == SDLK_e:
            if self.near_elder(player) and not self.accepted:
                self.accepted = True
                self.portal.activate()
                player.show_notice("의뢰를 받았습니다. 오른쪽 포탈로 출발하세요.")
            return

        if self.portal.handle_event(event, player):
            self.next_stage_requested = True
        elif (
            event.type == SDL_KEYDOWN
            and event.key == SDLK_UP
            and self.portal.nearby(player)
            and not self.accepted
        ):
            player.show_notice("먼저 마을 가운데 촌장에게 의뢰를 받아 주세요.")

    def resolve_clear(self, player):
        # 마을에는 처치할 몬스터가 없다.
        # 전투 스테이지의 자동 클리어 처리를 사용하지 않는다.
        return False

    def update(self, dt, player=None):
        self.portal.update(dt)

    def draw(self, camera):
        self.draw_background(camera)

        for x, roof_color in (
            (215, (161, 78, 57)),
            (467, (78, 116, 109)),
            (850, (145, 88, 69)),
        ):
            draw_house(x - camera.x, GROUND_Y, roof_color)

        self.platforms[0].draw(self.platform_image, camera)
        draw_elder(self.elder_x - camera.x, GROUND_Y)
        self.portal.draw(camera)

    def draw_village_ui(self, player, camera, font):
        # 화면 위쪽에 현재 의뢰와 목적지를 표시한다.
        panel(452, 645, 828, 704, dark=True)
        text(font, 471, 682, "새싹 마을", GOLD)
        text(font, 570, 682, self.quest["title"], WHITE)

        if self.accepted:
            objective = "오른쪽 포탈 → " + self.quest["destination"]
        else:
            objective = "마을 가운데 촌장에게 말을 걸어 보세요."
        text(font, 471, 659, objective, WHITE)

        npc_x = self.elder_x - camera.x
        text(font, npc_x - 34, GROUND_Y + 101, "마을 촌장", WHITE)

        if not self.accepted:
            text(font, npc_x - 3, GROUND_Y + 124, "!", GOLD)

        if self.near_elder(player):
            panel(296, 206, 984, 332, dark=True)
            text(font, 320, 305, "마을 촌장", GOLD)

            if self.accepted:
                text(font, 320, 271, "준비가 되면 오른쪽 포탈로 가 보렴.", WHITE)
                text(font, 320, 237, "목적지 · " + self.quest["destination"], GOLD)
            else:
                first_line, second_line = self.quest["dialogue"]
                text(font, 320, 277, first_line, WHITE)
                text(font, 320, 252, second_line, WHITE)
                text(font, 320, 225, "[E] 의뢰 수락", GOLD)

        elif self.portal.nearby(player):
            panel(385, 207, 895, 253, dark=True)
            if self.accepted:
                message = "[↑] " + self.quest["destination"] + " 입장"
            else:
                message = "촌장에게 의뢰를 받으면 포탈이 열립니다."
            text(font, 408, 231, message, WHITE)


def draw_village_map(stage, player, font):
    """한 화면 크기의 마을에서 나, 촌장, 출구 위치를 표시한다."""
    left = SCREEN_WIDTH - 300
    right = SCREEN_WIDTH - 16
    bottom = SCREEN_HEIGHT - 132
    top = SCREEN_HEIGHT - 16

    panel(left, bottom, right, top)
    text(font, left + 18, top - 22, "새싹 마을 · 마을 지도", (47, 54, 72))

    line_left = left + 22
    line_right = right - 22
    line_y = bottom + 44

    rect(line_left, line_y, line_right, line_y + 3, (135, 117, 86))

    exit_color = (79, 177, 204) if stage.accepted else (145, 145, 145)
    markers = (
        (stage.elder_x, GOLD),
        (stage.portal.x, exit_color),
        (player.x, (62, 173, 92)),
    )

    for world_x, color in markers:
        x = line_left + world_x / stage.width * (line_right - line_left)
        rect(x - 4, line_y - 3, x + 4, line_y + 7, color)

    text(font, left + 18, bottom + 17, "초록 · 나     금색 · 촌장     오른쪽 · 출구", (75, 75, 83))


def draw_village_frame(stage, player, camera, font):
    clear_canvas()

    stage.draw(camera)
    player.draw(camera.x)
    player.skills.draw(camera.x)
    draw_level_effect(player, camera.x)
    player.inventory.draw_feedback(camera.x, font)

    draw_player_status(player, stage, font)
    draw_skill_bar(player, font)
    stage.draw_village_ui(player, camera, font)
    draw_village_map(stage, player, font)
    draw_messages(player, font)
    draw_skill_window(player, font)
    player.inventory.draw(font)

    update_canvas()


def make_camera(stage, player):
    camera = Camera(stage.width)
    camera.update(player.x, 0.0, snap=True)
    return camera


def start_new_game():
    stage = Village(quest_number=1)
    player = Player(stage)
    camera = make_camera(stage, player)
    return stage, player, camera


def change_area(stage, player):
    if stage.number == 0:
        stage_types = {
            1: Stage,
            2: DeepForestStage,
            3: CaveStage,
        }
        next_stage = stage_types[stage.quest_number]()
        message = stage.quest["departure"]

    elif stage.number in (1, 2):
        next_stage = Village(quest_number=stage.number + 1)
        message = "새싹 마을로 돌아왔습니다. 촌장에게 말을 걸어 보세요."

    else:
        raise ValueError("골렘 동굴은 마지막 지역입니다.")

    # 원본의 맵 이동 처리를 사용해 장비, 레벨, 포션을 이어 간다.
    player.enter_stage(next_stage)
    player.show_notice(message)
    return next_stage, make_camera(next_stage, player)


def handle_events(stage, player):
    action = "continue"

    for event in get_events():
        if event.type == SDL_QUIT:
            return "quit"

        if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            return "quit"

        if not player.alive:
            if event.type == SDL_KEYDOWN and event.key == SDLK_RETURN:
                return "restart"
            continue

        if stage.number == 3 and stage.cleared:
            if (
                event.type == SDL_KEYDOWN
                and event.key == SDLK_RETURN
                and stage.victory_time >= 2.2
            ):
                return "restart"
            continue

        if (
            DEBUG_STAGE_SKIP
            and event.type == SDL_KEYDOWN
            and event.key == SDLK_F6
            and not getattr(event, "repeat", False)
            and stage.number < 3
        ):
            action = "change_area"
            continue

        stage.handle_portal_event(event, player)
        player.handle_event(event)

    if stage.number < 3 and stage.next_stage_requested:
        action = "change_area"

    return action


def main():
    open_canvas(SCREEN_WIDTH, SCREEN_HEIGHT)

    try:
        normal_font, title_font = original_game.load_ui_fonts()
        minimap = Minimap()
        stage, player, camera = start_new_game()
        previous_time = get_time()

        while True:
            current_time = get_time()
            frame_time = max(0.0, min(current_time - previous_time, 0.1))
            previous_time = current_time

            action = handle_events(stage, player)

            if action == "quit":
                break

            if action == "restart":
                stage, player, camera = start_new_game()
                previous_time = get_time()
                frame_time = 0.0

            elif action == "change_area":
                stage, camera = change_area(stage, player)
                previous_time = get_time()
                frame_time = 0.0

            original_game.update(stage, player, frame_time)

            if player.alive:
                if stage.number == 3 and stage.arena_started:
                    camera.x = stage.arena_left
                else:
                    camera.update(player.x, frame_time)

            if stage.number == 0:
                draw_village_frame(stage, player, camera, normal_font)
            else:
                original_game.draw(
                    stage,
                    player,
                    camera,
                    minimap,
                    normal_font,
                    title_font,
                )

            delay(0.01)

    finally:
        close_canvas()


if __name__ == "__main__":
    main()