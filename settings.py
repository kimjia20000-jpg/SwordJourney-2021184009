# 화면 크기.
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# 캐릭터 크기.
# 원본 대기 프레임 높이 311픽셀을 기준으로 배율 계산.
PLAYER_HEIGHT = 96.0
PLAYER_DRAW_SCALE = PLAYER_HEIGHT / 311.0

# 발판 착지에 사용하는 발 주변 영역의 절반 너비.
PLAYER_FOOT_HALF_WIDTH = 9.0

# 이동과 점프.
MOVE_SPEED = 260.0
JUMP_SPEED = 600.0
GRAVITY = 1600.0

# 지형.
GROUND_Y = 80.0
PLATFORM_THICKNESS = 20

# 애니메이션.
IDLE_FPS = 4.0
RUN_FPS = 10.0

# 첫 번째 검의 임시 공격 시간.
ATTACK_DURATION = 0.48

# 이후 슬라임을 만들 때 사용할 표시 크기.
# 아직 슬라임 생성이나 충돌에는 사용하지 않는다.
SLIME_WIDTH = 64
SLIME_HEIGHT = 48