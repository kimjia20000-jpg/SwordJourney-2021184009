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


CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600


def handle_events(player):
    """종료 입력을 처리하고, 나머지 입력은 캐릭터에게 전달한다."""
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
    """게임 객체의 상태를 갱신한다."""
    player.update(frame_time)


def draw(player):
    """현재 게임 상태를 화면에 그린다."""
    clear_canvas()

    player.draw()

    update_canvas()


def main():
    open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)

    try:
        # 이미지 로딩은 캔버스를 연 다음 수행한다.
        player = Player()

        # 리소스 로딩이 끝난 시점부터 시간을 측정한다.
        previous_time = get_time()

        while True:
            current_time = get_time()
            frame_time = current_time - previous_time
            previous_time = current_time

            if not handle_events(player):
                break

            update(player, frame_time)
            draw(player)

            # 불필요하게 빠른 반복을 줄이기 위한 짧은 대기.
            # 이동 속도는 다음 단계에서 frame_time으로 계산한다.
            delay(0.01)

    finally:
        # 실행 중 오류가 발생하더라도 캔버스를 정리한다.
        close_canvas()


if __name__ == "__main__":
    main()