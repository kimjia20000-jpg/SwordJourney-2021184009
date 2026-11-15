import math

from settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    """월드 좌표는 유지하고, 그릴 때만 카메라 위치를 뺀다."""

    def __init__(self, world_width):
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.world_width = world_width
        self.x = 0.0

    def update(self, player_x, dt, snap=False):
        target = max(0.0, min(
            self.world_width - self.width,
            player_x - self.width / 2,
        ))
        if snap:
            self.x = target
        else:
            self.x += (target - self.x) * (1.0 - math.exp(-10.0 * dt))
        self.x = max(0.0, min(self.world_width - self.width, self.x))

    def visible(self, left, right, margin=0):
        return right >= self.x - margin and left <= self.x + self.width + margin
