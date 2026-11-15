"""단방향 발판 사이의 점프 경로. 월드 좌표로만 계산한다."""
import math
from collections import deque

JUMP = 600.0
GRAVITY = 1600.0
NAV_SPEED = 185.0
MARGIN = 26.0


class PlatformRoutes:
    def __init__(self, platforms):
        self.platforms = platforms
        self.cache = {}
        self.edges = {p: [] for p in platforms}
        for source in platforms:
            for target in platforms:
                if source is target:
                    continue
                dy = target.top - source.top
                if dy > 105:
                    continue
                # 양 끝에서 몸이 걸리지 않도록 안전 여백을 둔다.
                sl, sr = source.left + MARGIN, source.right - MARGIN
                tl, tr = target.left + MARGIN, target.right - MARGIN
                if sl > sr or tl > tr:
                    continue
                overlap_l, overlap_r = max(sl, tl), min(sr, tr)
                if overlap_l <= overlap_r:
                    takeoff = landing = (overlap_l + overlap_r) / 2
                elif sr < tl:
                    takeoff, landing = sr, tl
                else:
                    takeoff, landing = sl, tr
                time = (JUMP + math.sqrt(JUMP * JUMP - 2 * GRAVITY * dy)) / GRAVITY
                if abs(landing - takeoff) <= NAV_SPEED * time - 10:
                    drop = dy < -8 and abs(landing - takeoff) <= NAV_SPEED * math.sqrt(-2 * dy / GRAVITY) - 10
                    self.edges[source].append((target, takeoff, landing, drop))

    def locate(self, x, y):
        # 공중의 플레이어는 발 아래에서 가장 가까운 발판으로 추적한다.
        candidates = [p for p in self.platforms if p.left <= x <= p.right and p.top <= y + 8]
        return max(candidates, key=lambda p: p.top) if candidates else self.platforms[0]

    def next_step(self, source, target):
        if source is target:
            return None
        if (source, target) in self.cache:
            return self.cache[source, target]
        queue = deque([(source, None)])
        visited = {source}
        while queue:
            node, first = queue.popleft()
            for edge in self.edges[node]:
                nxt = edge[0]
                if nxt in visited:
                    continue
                step = first or edge
                if nxt is target:
                    self.cache[source, target] = step
                    return step
                visited.add(nxt)
                queue.append((nxt, step))
        return None
