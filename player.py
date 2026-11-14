from pathlib import Path

from pico2d import load_image


# player.py가 있는 폴더를 기준으로 이미지 경로를 만든다.
BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "assets" / "images" / "player_preview.png"


class Player:
    def __init__(self):
        # 이번 단계에서는 캐릭터를 화면 중앙에 표시한다.
        self.x = 400
        self.y = 300

        self.image = load_image(str(IMAGE_PATH))

        # 시안의 비율을 유지하면서 높이 160픽셀로 표시한다.
        self.draw_height = 160
        self.draw_width = round(
            self.image.w * self.draw_height / self.image.h
        )

    def handle_event(self, event):
        # 다음 단계에서 이동 입력을 추가한다.
        pass

    def update(self, frame_time):
        # 다음 단계에서 경과 시간에 따른 이동을 추가한다.
        pass

    def draw(self):
        self.image.draw(
            self.x,
            self.y,
            self.draw_width,
            self.draw_height
        )