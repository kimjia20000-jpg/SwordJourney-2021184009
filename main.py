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

from player import Player
from stage import Stage


CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600


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


def update(player, frame_time):
    # 물리 계산을 작은 시간 단위로 나눠
    # 발판 착지 판정을 자주 확인한다.
    remaining_time = frame_time
    max_step = 1.0 / 120.0

    while remaining_time > 0:
        step = min(remaining_time, max_step)
        player.update(step)
        remaining_time -= step


def draw(stage, player):
    clear_canvas()

    # 지형 다음에 캐릭터를 그린다.
    stage.draw()
    player.draw()

    update_canvas()


def main():
    open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)

    try:
        stage = Stage()
        player = Player(stage)

        previous_time = get_time()

        while True:
            current_time = get_time()
            frame_time = current_time - previous_time
            previous_time = current_time

            # 디버거 정지나 창 이동 뒤의 큰 시간 차를 제한.
            frame_time = max(0.0, min(frame_time, 0.1))

            if not handle_events(player):
                break

            update(player, frame_time)
            draw(stage, player)

            delay(0.01)

    finally:
        close_canvas()


if __name__ == "__main__":
    main()