from pico2d import *


def main():
    # 800 × 600 크기의 게임 창 열기
    open_canvas(800, 600)

    running = True

    while running:
        # 키보드 입력과 창 닫기 이벤트 처리
        events = get_events()

        for event in events:
            if event.type == SDL_QUIT:
                running = False

            elif event.type == SDL_KEYDOWN:
                if event.key == SDLK_ESCAPE:
                    running = False

        # 종료 요청이 있으면 반복문을 빠져나가기
        if not running:
            break

        # 화면을 지우고 새 화면 표시
        clear_canvas()
        update_canvas()

        # 반복 속도를 조절해 CPU 사용량 줄이기
        delay(0.01)

    # 게임 창 정리
    close_canvas()


if __name__ == "__main__":
    main()