import pygame
import sys
import random
import json
import os

# --- 메타데이터 ---
__title__ = 'Python Brick Breaker'
__version__ = '1.3.3'  #시작화면과 설명화면 추가
__author__ = 'Python Developer'

# --- 설정 상수 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 10
BALL_RADIUS = 10
BRICK_WIDTH = 75
BRICK_HEIGHT = 20
BRICK_ROWS = 5
BRICK_COLS = 10
FPS = 60

# 색상 (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
DARK_GRAY = (50, 50, 50)
ORANGE = (255, 165, 0)  # 밝은 주황색 (노란색보다 가시성 좋음)

# 게임 설정
INITIAL_LIVES = 3
HIGHSCORE_FILE = "highscore.json"

# 파워업 타입
POWERUP_TYPES = ['WIDE_PADDLE', 'SLOW_BALL', 'DOUBLE_SCORE', 'EXTRA_LIFE']
POWERUP_COLORS = {
    'WIDE_PADDLE': (0, 200, 255),   # 밝은 파란색
    'SLOW_BALL': (200, 100, 255),   # 보라색
    'DOUBLE_SCORE': (255, 200, 0),  # 주황색
    'EXTRA_LIFE': (255, 100, 100)   # 분홍색
}
POWERUP_DURATION = 300  # 10초 (60 FPS 기준)

# --- 헬퍼 함수 ---

def create_bricks():
    """초기 벽돌 배치를 생성하여 리스트로 반환합니다."""
    new_bricks = []
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLS):
            brick_x = 15 + col * (BRICK_WIDTH + 5)
            brick_y = 15 + row * (BRICK_HEIGHT + 5)
            new_bricks.append(Brick(brick_x, brick_y))
    return new_bricks

def load_highscore():
    """저장된 하이스코어를 불러옥니다."""
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('highscore', 0)
        except:
            return 0
    return 0

def save_highscore(score):
    """하이스코어를 저장합니다."""
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump({'highscore': score}, f)
    except:
        pass

# --- 클래스 정의 ---

class Paddle:
    def __init__(self):
        self.rect = pygame.Rect(
            SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2,
            SCREEN_HEIGHT - 40,
            PADDLE_WIDTH,
            PADDLE_HEIGHT
        )
        self.speed = 8

    def move(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, self.rect)

class Ball:
    def __init__(self):
        self.reset(1)

    def reset(self, level):
        self.rect = pygame.Rect(
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            BALL_RADIUS * 2,
            BALL_RADIUS * 2
        )
        # 물리 계산을 위한 이전 프레임 위치 저장
        self.prev_rect = self.rect.copy()
        
        # 속도 설정 (최대 속도를 6으로 제한하여 터널링 방지)
        base_speed = min(4 + level, 6)
        self.dx = random.choice([-base_speed, base_speed]) 
        self.dy = -base_speed 

    def move(self):
        # 이동 전 현재 위치 저장
        self.prev_rect = self.rect.copy()
        
        self.rect.x += self.dx
        self.rect.y += self.dy
        
        # 벽 충돌 처리 (위치 보정 추가)
        if self.rect.left <= 0:
            self.dx *= -1
            self.rect.left = 0  # 위치 보정
        elif self.rect.right >= SCREEN_WIDTH:
            self.dx *= -1
            self.rect.right = SCREEN_WIDTH  # 위치 보정
        
        if self.rect.top <= 0:
            self.dy *= -1
            self.rect.top = 0  # 위치 보정
            
        # 바닥 충돌 (게임 오버)
        if self.rect.bottom >= SCREEN_HEIGHT:
            return False 
        return True 

    def draw(self, screen):
        pygame.draw.circle(screen, RED, self.rect.center, BALL_RADIUS)

class Brick:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
        self.active = True

    def draw(self, screen):
        if self.active:
            pygame.draw.rect(screen, GREEN, self.rect)
            pygame.draw.rect(screen, BLACK, self.rect, 1)

class PowerUp:
    def __init__(self, x, y, powerup_type):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.powerup_type = powerup_type
        self.color = POWERUP_COLORS[powerup_type]
        self.speed = 3
        self.active = True
    
    def move(self):
        self.rect.y += self.speed
        # 화면 아래로 나가면 제거
        if self.rect.top > SCREEN_HEIGHT:
            self.active = False
    
    def draw(self, screen):
        if self.active:
            pygame.draw.rect(screen, self.color, self.rect)
            pygame.draw.rect(screen, BLACK, self.rect, 2)

# --- 메인 게임 함수 ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"{__title__} v{__version__}")
    clock = pygame.time.Clock()

    # 폰트 설정
    score_font = pygame.font.SysFont(None, 36)
    title_font = pygame.font.SysFont(None, 80)
    sub_font = pygame.font.SysFont(None, 40)

    # 객체 생성
    paddle = Paddle()
    ball = Ball()
    bricks = create_bricks() # 함수 분리로 깔끔해짐
    
    score = 0
    level = 1
    lives = INITIAL_LIVES
    highscore = load_highscore()  # 하이스코어 로드
    game_state = 'MAIN_MENU'  # MAIN_MENU, INSTRUCTIONS, START, READY, PLAYING, PAUSE, GAME_OVER
    menu_selection = 0  # 0: 게임시작, 1: 게임설명
    
    # 파워업 관련 변수
    powerups = []
    paddle_width = PADDLE_WIDTH
    score_multiplier = 1
    paddle_width_timer = 0
    slow_ball_timer = 0  # 느린 공 지속시간
    score_multiplier_timer = 0  # 점수 배수 지속시간

    running = True
    while running:
        # 1. 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if game_state == 'MAIN_MENU':
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        menu_selection = 0
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        menu_selection = 1
                    elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        if menu_selection == 0:
                            game_state = 'START'
                        elif menu_selection == 1:
                            game_state = 'INSTRUCTIONS'
                
                elif game_state == 'INSTRUCTIONS':
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        game_state = 'MAIN_MENU'
                        menu_selection = 0
                
                elif game_state == 'START':
                    if event.key == pygame.K_SPACE:
                        game_state = 'READY'
                    elif event.key == pygame.K_ESCAPE:
                        game_state = 'MAIN_MENU'
                        menu_selection = 0
                
                elif game_state == 'READY':
                    if event.key == pygame.K_SPACE:
                        game_state = 'PLAYING'
                
                elif game_state == 'PLAYING':
                    if event.key == pygame.K_c: # 개발자 치트키
                         for brick in bricks: brick.active = False
                    elif event.key == pygame.K_ESCAPE: # 일시정지
                         game_state = 'PAUSE'
                
                elif game_state == 'PAUSE':
                    if event.key == pygame.K_ESCAPE: # 일시정지 해제
                         game_state = 'PLAYING'
                
                elif game_state == 'GAME_OVER':
                    if event.key == pygame.K_SPACE:
                        score = 0
                        level = 1
                        lives = INITIAL_LIVES
                        paddle.rect.width = PADDLE_WIDTH  # 패들 크기 초기화
                        score_multiplier = 1  # 점수 배수 초기화
                        powerups = []  # 파워업 리스트 초기화
                        paddle_width_timer = 0
                        slow_ball_timer = 0  # 느린 공 타이머 초기화
                        score_multiplier_timer = 0  # 점수 배수 타이머 초기화
                        ball.reset(level)
                        bricks = create_bricks()
                        game_state = 'MAIN_MENU'
                        menu_selection = 0

        screen.fill(WHITE)

        # 2. 상태별 로직 및 그리기
        if game_state == 'MAIN_MENU':
            # 메인 메뉴 화면
            title_text = title_font.render("BRICK BREAKER", True, BLUE)
            screen.blit(title_text, title_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 120)))
            
            # 메뉴 항목 렌더링
            menu_items = ["START GAME", "INSTRUCTIONS"]
            menu_y_positions = [SCREEN_HEIGHT/2 - 20, SCREEN_HEIGHT/2 + 40]
            
            for i, item in enumerate(menu_items):
                color = ORANGE if i == menu_selection else DARK_GRAY
                prefix = "▶ " if i == menu_selection else "  "
                menu_text = sub_font.render(prefix + item, True, color)
                screen.blit(menu_text, menu_text.get_rect(center=(SCREEN_WIDTH/2, menu_y_positions[i])))
            
            hint_text = score_font.render("↑↓ 선택, SPACE 확인", True, DARK_GRAY)
            screen.blit(hint_text, hint_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT - 60)))

        elif game_state == 'INSTRUCTIONS':
            # 게임설명 화면
            title_text = title_font.render("GAME INSTRUCTIONS", True, BLUE)
            screen.blit(title_text, title_text.get_rect(center=(SCREEN_WIDTH/2, 30)))
            
            # 텍스트 위치 설정
            start_y = 80
            line_height = 35
            current_y = start_y
            
            # 조작법 섹션
            control_title = score_font.render("KEYBOARD CONTROLS", True, BLUE)
            screen.blit(control_title, (20, current_y))
            current_y += line_height + 5
            
            controls = [
                "← LEFT ARROW: 패들 왼쪽 이동",
                "→ RIGHT ARROW: 패들 오른쪽 이동",
                "ESC: 게임 일시정지"
            ]
            
            for control in controls:
                control_text = score_font.render(control, True, DARK_GRAY)
                screen.blit(control_text, (40, current_y))
                current_y += line_height
            
            current_y += 10
            
            # 파워업 섹션
            powerup_title = score_font.render("POWER-UPS", True, BLUE)
            screen.blit(powerup_title, (20, current_y))
            current_y += line_height + 5
            
            # 파워업 정보
            powerup_info = [
                ('WIDE_PADDLE', "패들을 1.5배 확대 (10초)"),
                ('SLOW_BALL', "공의 속도를 0.7배 감소 (10초)"),
                ('DOUBLE_SCORE', "점수 2배 획득 (10초)"),
                ('EXTRA_LIFE', "생명력 1개 증가")
            ]
            
            for powerup_type, description in powerup_info:
                color = POWERUP_COLORS[powerup_type]
                # 색상 박스 그리기
                pygame.draw.rect(screen, color, (40, current_y, 20, 20))
                pygame.draw.rect(screen, BLACK, (40, current_y, 20, 20), 2)
                
                # 설명 텍스트
                desc_text = score_font.render(description, True, DARK_GRAY)
                screen.blit(desc_text, (70, current_y))
                current_y += line_height
            
            # 돌아가기 안내
            hint_text = score_font.render("ESC 또는 SPACE로 메뉴로 돌아가기", True, ORANGE)
            screen.blit(hint_text, hint_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT - 30)))

        elif game_state == 'START':
            # START 상태에서 파워업 없음
            powerups.clear()
            
            title_text = title_font.render("BRICK BREAKER", True, BLUE)
            start_text = sub_font.render("Press SPACE to Start", True, BLACK)
            lives_text = score_font.render(f"Lives: {INITIAL_LIVES}", True, RED)
            highscore_text = score_font.render(f"High Score: {highscore}", True, ORANGE)
            menu_hint_text = score_font.render("ESC: 메뉴로 돌아가기", True, DARK_GRAY)
            screen.blit(title_text, title_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50)))
            screen.blit(start_text, start_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 20)))
            screen.blit(lives_text, lives_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 80)))
            screen.blit(highscore_text, highscore_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 120)))
            screen.blit(menu_hint_text, menu_hint_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT - 30)))

        elif game_state == 'READY':
            # 공이 패들 위에 고정된 상태에서 대기
            paddle.move()
            
            # 공을 항상 패들 위의 중앙에 유지
            ball.rect.centerx = paddle.rect.centerx
            ball.rect.bottom = paddle.rect.top
            
            ready_text = sub_font.render("READY! Press SPACE", True, BLUE)
            screen.blit(ready_text, ready_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 100)))
            
            # 화면 그리기
            paddle.draw(screen)
            ball.draw(screen)
            for brick in bricks: brick.draw(screen)
            for powerup in powerups: powerup.draw(screen)  # READY 상태에서도 파워업 표시
            score_text = score_font.render(f"Score: {score}  Level: {level}  Lives: {lives}", True, DARK_GRAY)
            screen.blit(score_text, (10, 10))

        elif game_state == 'PLAYING':
            paddle.move()
            
            if not ball.move():
                lives -= 1
                if lives <= 0:
                    game_state = 'GAME_OVER'
                else:
                    # 공을 패들 위에 고정
                    ball.rect.centerx = paddle.rect.centerx
                    ball.rect.bottom = paddle.rect.top
                    ball.prev_rect = ball.rect.copy()
                    game_state = 'READY' 
            
            # --- 패들 충돌 처리 ---
            if ball.rect.colliderect(paddle.rect):
                # 이전 프레임 위치를 확인하여 터널링 방지
                if not ball.prev_rect.colliderect(paddle.rect):
                    # 공이 위에서 내려올 때 (y축 중심 비교)
                    if ball.rect.centery < paddle.rect.centery:
                        ball.dy = -abs(ball.dy) # 무조건 위로 반사
                        ball.rect.bottom = paddle.rect.top 
                    else:
                        # 옆면 충돌
                        ball.dx *= -1
                        if ball.rect.centerx < paddle.rect.centerx:
                             ball.rect.right = paddle.rect.left
                        else:
                             ball.rect.left = paddle.rect.right

            # --- 벽돌 충돌 처리 ---
            collided_bricks = []
            for brick in bricks:
                if brick.active and ball.rect.colliderect(brick.rect):
                    # 이미 처리된 벽돌이거나, 이전 프레임부터 겹쳐있던 경우 무시
                    if brick in collided_bricks:
                        continue
                    if ball.prev_rect.colliderect(brick.rect):
                        continue
                    
                    brick.active = False
                    collided_bricks.append(brick)
                    score += (10 + (level * 2)) * score_multiplier  # 점수 배수 적용
                    
                    # 20% 확률로 파워업 드롭
                    if random.random() < 0.2:
                        powerup_type = random.choice(POWERUP_TYPES)
                        powerups.append(PowerUp(brick.rect.centerx, brick.rect.centery, powerup_type))
                    
                    # 겹침 깊이(penetration depth) 계산으로 정확한 충돌 면 판정
                    overlap_top = ball.rect.bottom - brick.rect.top
                    overlap_bottom = brick.rect.bottom - ball.rect.top
                    overlap_left = ball.rect.right - brick.rect.left
                    overlap_right = brick.rect.right - ball.rect.left
                    
                    min_overlap = min(overlap_top, overlap_bottom, overlap_left, overlap_right)
                    
                    if min_overlap == overlap_top and ball.dy > 0:
                        ball.dy *= -1
                        ball.rect.bottom = brick.rect.top
                    elif min_overlap == overlap_bottom and ball.dy < 0:
                        ball.dy *= -1
                        ball.rect.top = brick.rect.bottom
                    elif min_overlap == overlap_left and ball.dx > 0:
                        ball.dx *= -1
                        ball.rect.right = brick.rect.left
                    elif min_overlap == overlap_right and ball.dx < 0:
                        ball.dx *= -1
                        ball.rect.left = brick.rect.right

            # 스테이지 클리어 체크
            if all(not brick.active for brick in bricks):
                screen.fill(WHITE)
                clear_text = title_font.render(f"STAGE {level} CLEAR!", True, BLUE)
                screen.blit(clear_text, clear_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)))
                pygame.display.flip()
                
                pygame.time.delay(2000)
                
                level += 1
                ball.reset(level)
                bricks = create_bricks()
            
            # --- 파워업 처리 ---
            for powerup in powerups[:]:
                powerup.move()
                if not powerup.active:
                    powerups.remove(powerup)
                    continue
                
                # 패들과 충돌
                if powerup.rect.colliderect(paddle.rect):
                    if powerup.powerup_type == 'WIDE_PADDLE':
                        paddle.rect.width = int(PADDLE_WIDTH * 1.5)
                        paddle_width_timer = POWERUP_DURATION
                    elif powerup.powerup_type == 'SLOW_BALL':
                        ball.dx *= 0.7
                        ball.dy *= 0.7
                        slow_ball_timer = POWERUP_DURATION  # 10초 지속
                    elif powerup.powerup_type == 'DOUBLE_SCORE':
                        # 10초 동안 벽돌 점수 2배
                        score_multiplier = 2
                        score_multiplier_timer = POWERUP_DURATION
                    elif powerup.powerup_type == 'EXTRA_LIFE':
                        lives += 1
                    
                    powerup.active = False
                    powerups.remove(powerup)
            
            # 파워업 타이머 감소
            
            if paddle_width_timer > 0:
                paddle_width_timer -= 1
                if paddle_width_timer == 0:
                    paddle.rect.width = PADDLE_WIDTH
            
            if slow_ball_timer > 0:
                slow_ball_timer -= 1
                if slow_ball_timer == 0:
                    # 느린 공 효과 해제 (원래 속도로 복구)
                    ball.dx /= 0.7
                    ball.dy /= 0.7
            
            if score_multiplier_timer > 0:
                score_multiplier_timer -= 1
                if score_multiplier_timer == 0:
                    score_multiplier = 1  # 점수 배수 해제

            # 화면 그리기
            paddle.draw(screen)
            ball.draw(screen)
            for brick in bricks: brick.draw(screen)
            for powerup in powerups: powerup.draw(screen)  # 파워업 그리기
            
            # 점수 배수 활성화 상태 표시
            multiplier_text = ""
            if score_multiplier == 2:
                multiplier_text = " [x2 SCORE]"
                multiplier_seconds = (score_multiplier_timer + 29) // 30  # 30fps 기준
            
            score_text = score_font.render(f"Score: {score}  Level: {level}  Lives: {lives}{multiplier_text}", True, DARK_GRAY)
            screen.blit(score_text, (10, 10))
            
            # 점수 배수 남은 시간 표시
            if score_multiplier == 2:
                timer_text = score_font.render(f"x2 Score: {multiplier_seconds}s", True, (255, 165, 0))  # 오렌지색
                screen.blit(timer_text, (10, 50))

        elif game_state == 'PAUSE':
            # 게임 일시정지 화면
            pause_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            pause_overlay.set_alpha(128)
            pause_overlay.fill(BLACK)
            screen.blit(pause_overlay, (0, 0))
            
            pause_text = title_font.render("PAUSED", True, ORANGE)
            resume_text = sub_font.render("Press ESC to Resume", True, WHITE)
            screen.blit(pause_text, pause_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 60)))
            screen.blit(resume_text, resume_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 40)))

        elif game_state == 'GAME_OVER':
            # 현재 스코어가 하이스코어보다 크면 업데이트
            if score > highscore:
                highscore = score
                save_highscore(highscore)
            
            over_text = title_font.render("GAME OVER", True, RED)
            score_msg = sub_font.render(f"Final Score: {score}", True, BLACK)
            highscore_msg = score_font.render(f"High Score: {highscore}", True, ORANGE)
            lives_msg = score_font.render(f"Lives Remaining: {lives}", True, RED)
            retry_text = sub_font.render("Press SPACE to Start", True, DARK_GRAY)
            screen.blit(over_text, over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 80)))
            screen.blit(score_msg, score_msg.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 10)))
            screen.blit(highscore_msg, highscore_msg.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30)))
            screen.blit(lives_msg, lives_msg.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 70)))
            screen.blit(retry_text, retry_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 120)))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()