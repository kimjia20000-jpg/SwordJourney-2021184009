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


# 테스트할 때만 True로 바꾸면 F6으로 현재 지역을 건너뛸 수 있다.
DEBUG_STAGE_SKIP = False

VILLAGE_IMAGE_PATH = IMAGE_DIR / "village_sprites.png"

# 원본 이미지 크기는 1254 × 1254.
# 각 영역은 pico2d의 왼쪽 아래 기준 (x, y, 너비, 높이).
VILLAGE_SPRITES = {
    "red_house": (55, 676, 519, 499),
    "green_house": (676, 675, 529, 508),
    "straw_house": (26, 46, 575, 518),
    "elder": (725, 36, 398, 551),
}

# 이미지 이름, 마을 안의 가로 위치, 게임 화면에 그릴 높이
HOUSES = (
    ("red_house", 190, 216),
    ("green_house", 477, 204),
    ("straw_house", 878, 237),
)

QUESTS = {
    1: {
        "title": "초원 길을 열어 줘",
        "destination": "슬라임 지대",
        "lines": (
            "마을 밖 풀밭에 슬라임이 잔뜩 모였단다.",
            "아이들이 다시 다닐 수 있게 슬라임을 모두 물리쳐 주겠니?",
        ),
        "departure": "첫 번째 의뢰 · 초원의 슬라임을 모두 처치하세요.",
    },
    2: {
        "title": "깊은 숲의 늑대 떼",
        "destination": "깊은 숲",
        "lines": (
            "덕분에 아이들이 다시 풀밭에서 놀 수 있게 됐단다.",
            "이번엔 나무꾼들이 돌아올 수 있게 숲길의 늑대 떼를 부탁하마.",
        ),
        "departure": "두 번째 의뢰 · 깊은 숲의 늑대 떼를 처치하세요.",
    },
    3: {
        "title": "동굴에서 들리는 소리",
        "destination": "골렘 동굴",
        "lines": (
            "숲길을 열어 줘서 고맙구나. 그런데 밤마다 땅이 울리는구나.",
            "숲 너머 동굴로 가서 안쪽의 골렘을 쓰러뜨려 주겠니?",
        ),
        "departure": "마지막 의뢰 · 동굴 안쪽의 골렘을 쓰러뜨리세요.",
    },
}

COMBAT_STAGES = {
    1: Stage,
    2: DeepForestStage,
    3: CaveStage,
}


class Village(Stage):
    """게임 시작 및 전투 지역 사이에 방문하는 새싹 마을."""

    def __init__(self, quest_number=1):
        # 원본 Stage 생성자는 슬라임까지 생성하므로
        # 마을에 필요한 지형, 이미지, 포탈만 준비한다.
        self.number = 0
        self.quest_number = quest_number
        self.quest = QUESTS[quest_number]
        self.accepted = False
        self.next_stage_requested = False

        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.elder_x = 648

        # 처음에는 왼쪽 집 앞, 귀환할 때는 촌장 옆에서 시작.
        self.spawn_x = 210 if quest_number == 1 else self.elder_x - 74
        self.spawn_y = GROUND_Y

        self.platforms = [
            Platform(0, self.width, GROUND_Y, GROUND_Y)
        ]
        self.monsters = []

        self.background = load_image(
            str(IMAGE_DIR / "stage1_background.png")
        )
        self.platform_image = load_image(
            str(IMAGE_DIR / "grass_platform.png")
        )

        if not VILLAGE_IMAGE_PATH.is_file():
            raise FileNotFoundError(
                "마을 이미지 파일을 찾지 못했습니다.\n"
                f"이미지를 다음 위치에 저장해 주세요:\n{VILLAGE_IMAGE_PATH}"
            )

        self.sprite_sheet = load_image(str(VILLAGE_IMAGE_PATH))
        self.portal = Portal(self.width - 140, GROUND_Y)

    def near_elder(self, player):
        return (
            player.on_ground
            and abs(player.x - self.elder_x) <= 100
        )

    def handle_portal_event(self, event, player):
        if event.type == SDL_KEYDOWN and event.key == SDLK_e:
            if self.near_elder(player) and not self.accepted:
                self.accepted = True
                self.portal.activate()
                player.show_notice(
                    "의뢰를 받았습니다. 오른쪽 포탈로 출발하세요."
                )
            return

        if self.portal.handle_event(event, player):
            self.next_stage_requested = True
            return

        if (
            event.type == SDL_KEYDOWN
            and event.key == SDLK_UP
            and self.portal.nearby(player)
            and not self.accepted
        ):
            player.show_notice(
                "먼저 마을 가운데 촌장에게 의뢰를 받아 주세요."
            )

    def resolve_clear(self, player):
        # 몬스터가 없는 마을에 전투 지역 클리어 처리를 적용하지 않는다.
        return False

    def update(self, dt, player=None):
        self.portal.update(dt)

    def draw_sprite(self, sprite_name, screen_x, ground_y, display_height):
        left, bottom, width, height = VILLAGE_SPRITES[sprite_name]

        # 같은 이미지를 다른 해상도로 저장한 경우에도 영역을 맞춘다.
        scale_x = self.sprite_sheet.w / 1254
        scale_y = self.sprite_sheet.h / 1254

        source_left = round(left * scale_x)
        source_bottom = round(bottom * scale_y)
        source_right = round((left + width) * scale_x)
        source_top = round((bottom + height) * scale_y)

        display_width = round(display_height * width / height)

        self.sprite_sheet.clip_draw(
            source_left,
            source_bottom,
            source_right - source_left,
            source_top - source_bottom,
            round(screen_x),
            round(ground_y + display_height / 2),
            display_width,
            display_height,
        )

    def draw(self, camera):
        self.draw_background(camera)

        for sprite_name, world_x, height in HOUSES:
            self.draw_sprite(
                sprite_name,
                world_x - camera.x,
                GROUND_Y,
                height,
            )

        self.platforms[0].draw(self.platform_image, camera)

        # 주인공 높이 96에 맞춰 촌장의 표시 높이는 92로 설정.
        self.draw_sprite(
            "elder",
            self.elder_x - camera.x,
            GROUND_Y,
            92,
        )

        self.portal.draw(camera)

    def draw_village_ui(self, player, camera, font):
        # 상단 의뢰 안내
        panel(452, 645, 828, 704, dark=True)
        text(font, 470, 682, "새싹 마을", GOLD)
        text(font, 565, 682, self.quest["title"], WHITE)

        if self.accepted:
            objective = "오른쪽 포탈 → " + self.quest["destination"]
        else:
            objective = "마을 가운데 촌장에게 말을 걸어 보세요."

        text(font, 470, 658, objective, WHITE)

        # 촌장 이름과 의뢰 표시
        npc_x = self.elder_x - camera.x
        text(font, npc_x - 35, GROUND_Y + 108, "마을 촌장", WHITE)

        if not self.accepted:
            text(font, npc_x - 3, GROUND_Y + 132, "!", GOLD)

        # 촌장 근처에서는 대화창을 열고, 멀어지면 자동으로 닫는다.
        if self.near_elder(player):
            panel(296, 224, 984, 350, dark=True)
            text(font, 320, 324, "마을 촌장", GOLD)

            if self.accepted:
                text(
                    font, 320, 289,
                    "준비가 되면 오른쪽 포탈로 가 보렴.",
                    WHITE,
                )
                text(
                    font, 320, 252,
                    "목적지 · " + self.quest["destination"],
                    GOLD,
                )
            else:
                first_line, second_line = self.quest["lines"]
                text(font, 320, 295, first_line, WHITE)
                text(font, 320, 270, second_line, WHITE)
                text(font, 320, 244, "[E] 의뢰 수락", GOLD)

        elif self.portal.nearby(player):
            panel(385, 208, 895, 254, dark=True)

            if self.accepted:
                message = "[↑] " + self.quest["destination"] + " 입장"
            else:
                message = "촌장에게 의뢰를 받으면 포탈이 열립니다."

            text(font, 408, 232, message, WHITE)


def draw_village_map(stage, player, font):
    left = SCREEN_WIDTH - 300
    right = SCREEN_WIDTH - 16
    bottom = SCREEN_HEIGHT - 140
    top = SCREEN_HEIGHT - 16

    panel(left, bottom, right, top)
    text(font, left + 18, top - 23, "새싹 마을 · 지도", (47, 54, 72))

    line_left = left + 22
    line_right = right - 22
    line_y = bottom + 47
    rect(line_left, line_y, line_right, line_y + 3, (138, 115, 86))

    exit_color = (79, 177, 204) if stage.accepted else (145, 145, 145)

    markers = (
        (stage.elder_x, GOLD),
        (stage.portal.x, exit_color),
        (player.x, (62, 173, 92)),
    )

    for world_x, color in markers:
        x = line_left + world_x / stage.width * (line_right - line_left)
        rect(x - 4, line_y - 3, x + 4, line_y + 7, color)

    text(
        font, left + 16, bottom + 18,
        "초록 · 나     금색 · 촌장     오른쪽 · 출구",
        (75, 75, 83),
    )


def draw_village_frame(stage, player, camera, normal_font):
    clear_canvas()

    stage.draw(camera)
    player.draw(camera.x)
    player.skills.draw(camera.x)

    draw_level_effect(player, camera.x)
    player.inventory.draw_feedback(camera.x, normal_font)

    draw_player_status(player, stage, normal_font)
    draw_skill_bar(player, normal_font)
    stage.draw_village_ui(player, camera, normal_font)
    draw_village_map(stage, player, normal_font)
    draw_messages(player, normal_font)
    draw_skill_window(player, normal_font)
    player.inventory.draw(normal_font)

    update_canvas()


def make_camera(stage, player):
    camera = Camera(stage.width)
    camera.update(player.x, 0.0, snap=True)
    return camera


def start_new_game():
    stage = Village(quest_number=1)
    player = Player(stage)
    return stage, player, make_camera(stage, player)


def change_area(stage, player):
    if stage.number == 0:
        stage_type = COMBAT_STAGES[stage.quest_number]
        next_stage = stage_type()
        message = stage.quest["departure"]

    elif stage.number in (1, 2):
        next_stage = Village(quest_number=stage.number + 1)
        message = "새싹 마을로 돌아왔습니다. 촌장에게 말을 걸어 보세요."

    else:
        raise ValueError("골렘 동굴은 마지막 지역입니다.")

    # 같은 Player를 이동시켜 레벨, 장비, 포션을 이어 간다.
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