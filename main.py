import os
from pathlib import Path

from pico2d import (
    open_canvas,
    close_canvas,
    clear_canvas,
    update_canvas,
    get_events,
    get_time,
    delay,
    load_font,
    draw_rectangle,
    SDL_QUIT,
    SDL_KEYDOWN,
    SDLK_ESCAPE,
    SDLK_RETURN,
)

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from player import Player
from stage import Stage
from camera import Camera
from minimap import Minimap
from hud import draw_player_status, draw_skill_bar, draw_messages, draw_level_effect


def load_ui_fonts():
    windows_directory = Path(
        os.environ.get("WINDIR", r"C:\Windows")
    )

    font_path = windows_directory / "Fonts" / "malgun.ttf"

    if not font_path.is_file():
        raise FileNotFoundError(
            f"한글 표시용 글꼴을 찾지 못했습니다: {font_path}"
        )

    normal_font = load_font(str(font_path), 20)
    title_font = load_font(str(font_path), 38)

    return normal_font, title_font


def handle_events(player):
    action = "continue"

    for event in get_events():
        if event.type == SDL_QUIT:
            return "quit"

        if (
            event.type == SDL_KEYDOWN
            and event.key == SDLK_ESCAPE
        ):
            return "quit"

        if not player.alive:
            if (
                event.type == SDL_KEYDOWN
                and event.key == SDLK_RETURN
            ):
                action = "restart"

        else:
            player.stage.handle_portal_event(event, player)
            player.handle_event(event)

    return action


def update(stage, player, frame_time):
    # 게임 오버 상태에서는 몬스터를 포함해 진행을 멈춘다.
    if not player.alive:
        return

    remaining_time = frame_time
    max_step = 1.0 / 120.0

    while remaining_time > 0:
        step = min(remaining_time, max_step)

        stage.update(step)
        player.update(step)

        # 공격 판정이 끝난 뒤 처치된 슬라임을 제거한다.
        stage.slimes[:] = [
            slime
            for slime in stage.slimes
            if slime.alive
        ]

        if not player.alive:
            break

        stage.resolve_clear()

        remaining_time -= step


def draw_game_over(normal_font, title_font):
    center_x = SCREEN_WIDTH / 2
    center_y = SCREEN_HEIGHT / 2

    draw_rectangle(
        center_x - 240,
        center_y - 105,
        center_x + 240,
        center_y + 105,
        25, 30, 35,
        filled=True
    )

    draw_rectangle(
        center_x - 240,
        center_y - 105,
        center_x + 240,
        center_y + 105,
        220, 200, 130
    )

    title_font.draw(
        center_x - 90,
        center_y + 40,
        "게임 오버",
        (255, 220, 160)
    )

    normal_font.draw(
        center_x - 110,
        center_y - 15,
        "Enter : 처음부터 다시 시작",
        (255, 255, 255)
    )

    normal_font.draw(
        center_x - 65,
        center_y - 55,
        "ESC : 게임 종료",
        (210, 210, 210)
    )


def draw(stage, player, camera, minimap, normal_font, title_font):
    clear_canvas()

    stage.draw(camera)
    player.draw(camera.x)
    player.skills.draw(camera.x)
    draw_level_effect(player, camera.x)

    # 몬스터 체력바.
    for slime in stage.slimes:
        if camera.visible(slime.x - slime.width, slime.x + slime.width):
            slime.draw_health_bar(camera.x)

    draw_player_status(player, stage, normal_font)
    draw_skill_bar(player, normal_font)
    draw_messages(player, normal_font)
    draw_rectangle(430, SCREEN_HEIGHT - 50, 850, SCREEN_HEIGHT - 15,
                   27, 36, 31, filled=True)
    normal_font.draw(446, SCREEN_HEIGHT - 39,
                     f"1스테이지  ·  {stage.zone_name(player.x)}", (240, 240, 220))
    minimap.draw(stage, player, camera, normal_font)

    stage.draw_status(player, normal_font, title_font)

    if not player.alive:
        draw_game_over(normal_font, title_font)

    update_canvas()


def main():
    open_canvas(SCREEN_WIDTH, SCREEN_HEIGHT)

    try:
        normal_font, title_font = load_ui_fonts()

        stage = Stage()
        player = Player(stage)
        camera = Camera(stage.width)
        camera.update(player.x, 0.0, snap=True)
        minimap = Minimap()

        previous_time = get_time()

        while True:
            current_time = get_time()
            frame_time = current_time - previous_time
            previous_time = current_time

            frame_time = max(
                0.0,
                min(frame_time, 0.1)
            )

            action = handle_events(player)

            if action == "quit":
                break

            if action == "restart":
                # 맵과 몬스터, 플레이어를 새로 생성한다.
                stage = Stage()
                player = Player(stage)
                camera = Camera(stage.width)
                camera.update(player.x, 0.0, snap=True)

                # 재시작 로딩 시간을 게임 시간에 포함하지 않는다.
                previous_time = get_time()
                frame_time = 0.0

            update(stage, player, frame_time)
            if player.alive:
                camera.update(player.x, frame_time)

            draw(
                stage,
                player,
                camera,
                minimap,
                normal_font,
                title_font
            )

            delay(0.01)

    finally:
        close_canvas()


if __name__ == "__main__":
    main()