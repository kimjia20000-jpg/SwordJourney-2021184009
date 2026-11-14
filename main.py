from pico2d import (
    open_canvas,
    close_canvas,
    clear_canvas,
    update_canvas,
    get_events,
    get_time,
    delay,
    SDL_QUIT,
    SDL_KEYDOWN,
    SDLK_ESCAPE,
)

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from player import Player
from stage import Stage


def handle_events(player):
    running = True

    for event in get_events():
        if event.type == SDL_QUIT:
            running = False

        elif (
            event.type == SDL_KEYDOWN
            and event.key == SDLK_ESCAPE
        ):
            running = False

        else:
            player.handle_event(event)

    return running


def update(stage, player, frame_time):
    remaining_time = frame_time
    max_step = 1.0 / 120.0

    while remaining_time > 0:
        step = min(remaining_time, max_step)

        stage.update(step)
        player.update(step)

        # 공격 판정 순회가 끝난 뒤 처치된 슬라임을 제거한다.
        stage.slimes[:] = [
            slime
            for slime in stage.slimes
            if slime.alive
        ]

        remaining_time -= step


def draw(stage, player):
    clear_canvas()

    stage.draw()
    player.draw()

    # 체력바는 가장 나중에 그린다.
    # 슬라임의 피격 깜빡임과 관계없이 계속 표시한다.
    for slime in stage.slimes:
        slime.draw_health_bar()

    update_canvas()


def main():
    open_canvas(SCREEN_WIDTH, SCREEN_HEIGHT)

    try:
        stage = Stage()
        player = Player(stage)

        previous_time = get_time()

        while True:
            current_time = get_time()
            frame_time = current_time - previous_time
            previous_time = current_time

            frame_time = max(
                0.0,
                min(frame_time, 0.1)
            )

            if not handle_events(player):
                break

            update(stage, player, frame_time)
            draw(stage, player)

            delay(0.01)

    finally:
        close_canvas()


if __name__ == "__main__":
    main()