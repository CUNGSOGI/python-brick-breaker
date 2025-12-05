import pygame, sys, random, json, os

# --- 설정 상수 ---
SCREEN_W, SCREEN_H = 825, 600
PADDLE_W, PADDLE_H = 100, 10
BALL_R, BRICK_W, BRICK_H = 10, 75, 20
BRICK_COLS = 10 
FPS, HEADER_H = 60, 60

# 색상 정의
WHITE, BLACK, RED = (255, 255, 255), (0, 0, 0), (255, 0, 0)
BLUE, GREEN, ORANGE = (0, 0, 255), (0, 255, 0), (255, 165, 0)
DARK_GRAY, SHADOW_GRAY = (50, 50, 50), (200, 200, 200)
HEADER_BG = (50, 50, 50)
P_COLORS = {'WIDE': (0,200,255), 'SLOW': (200,100,255), 'DBL': (255,200,0), 'LIFE': (255,100,100)}

INITIAL_LIVES, POWERUP_DURATION = 3, 300
HIGHSCORE_FILE = "highscore.json"
MAX_LEVEL = 10

# --- 메타데이터 ---
__title__ = 'Python Brick Breaker'
__version__ = '1.5.0' # 물리 엔진 전면 재작성(터널링/끼임 해결), 속도 밸런스 조정, 올클리어 버그 수정
__author__ = 'Python Developer'

# --- 클래스 정의 ---
class Paddle:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_W//2 - PADDLE_W//2, SCREEN_H - 40, PADDLE_W, PADDLE_H)
        self.speed = 8
    def move(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0: self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_W: self.rect.x += self.speed
    def draw(self, screen): pygame.draw.rect(screen, BLUE, self.rect)

class Ball:
    def __init__(self): self.reset(1)
    
    def reset(self, level):
        # 정밀 계산을 위해 float 좌표 사용
        self.x = SCREEN_W / 2
        self.y = SCREEN_H / 2
        self.rect = pygame.Rect(int(self.x), int(self.y), BALL_R*2, BALL_R*2)
        
        # 속도 설정
        base_speed = 4 + (level * 0.2)
        spd = min(base_speed, 10) 
        self.dx, self.dy = random.choice([-spd, spd]), -spd
        
    def draw(self, screen): 
        # rect를 그리기 전에 float 좌표를 rect에 동기화 (화면 표시용)
        self.rect.center = (int(self.x), int(self.y))
        pygame.draw.circle(screen, RED, self.rect.center, BALL_R)

class Brick:
    def __init__(self, x, y): self.rect, self.active = pygame.Rect(x, y, BRICK_W, BRICK_H), True
    def draw(self, screen):
        if self.active:
            pygame.draw.rect(screen, GREEN, self.rect)
            pygame.draw.rect(screen, BLACK, self.rect, 1)

class PowerUp:
    def __init__(self, x, y, p_type):
        self.rect, self.type, self.active = pygame.Rect(x, y, 20, 20), p_type, True
    def move(self):
        self.rect.y += 3
        if self.rect.top > SCREEN_H: self.active = False
    def draw(self, screen):
        if self.active:
            pygame.draw.rect(screen, P_COLORS[self.type], self.rect)
            pygame.draw.rect(screen, BLACK, self.rect, 2)

# --- 메인 게임 로직 ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(f"{__title__} v{__version__}")
    clock = pygame.time.Clock()
    
    fonts = {
        'T': pygame.font.SysFont(None, 80), 'L': pygame.font.SysFont('arial', 40, bold=True),
        'M': pygame.font.SysFont('arial', 30, bold=True), 'S': pygame.font.SysFont(None, 36),
        'SUB': pygame.font.SysFont(None, 40), 'KEY': pygame.font.SysFont('arial', 18, bold=True),
        'DESC': pygame.font.SysFont('arial', 22, bold=True), 'K': pygame.font.SysFont('malgungothic', 25)
    }

    paddle, ball = Paddle(), Ball()
    bricks, powerups = [], []
    score, level, lives, highscore = 0, 1, INITIAL_LIVES, 0
    state, menu_sel, pause_sel = 'MAIN_MENU', 0, 0
    timers = {'wide': 0, 'slow': 0, 'dbl': 0}
    score_mult = 1
    
    if os.path.exists(HIGHSCORE_FILE):
        try: highscore = json.load(open(HIGHSCORE_FILE))['highscore']
        except: pass

    def create_bricks_for_level(lvl):
        new_bricks = []
        rows = min(2 + lvl, 9) 
        total_w = BRICK_COLS * (BRICK_W + 5) - 5
        start_x = (SCREEN_W - total_w) // 2
        for r in range(rows):
            for c in range(BRICK_COLS):
                new_bricks.append(Brick(start_x + c*(BRICK_W+5), 80 + r*(BRICK_H+5)))
        return new_bricks

    def init_game(full_reset=False, keep_level=False):
        nonlocal score, level, lives, score_mult, timers
        if full_reset: score, level, lives = 0, 1, INITIAL_LIVES
        
        paddle.rect.width, paddle.rect.centerx = PADDLE_W, SCREEN_W // 2
        score_mult, timers = 1, {k: 0 for k in timers}
        powerups.clear()
        ball.reset(level)
        
        if not keep_level:
            bricks.clear()
            bricks.extend(create_bricks_for_level(level))

    def draw_text(text, f_key, color, center, shadow=False):
        if shadow:
            s = fonts[f_key].render(text, True, BLACK)
            screen.blit(s, s.get_rect(center=(center[0]+3, center[1]+3)))
        s = fonts[f_key].render(text, True, color)
        r = s.get_rect(center=center)
        screen.blit(s, r)
        return r

    def draw_keycap(key, action, color, rect_mid, align='left'):
        k_r = pygame.Rect(0, 0, 80 if len(key)>3 else 60, 40)
        if align == 'left': k_r.midright = rect_mid
        else: k_r.midleft = rect_mid
        
        pygame.draw.rect(screen, SHADOW_GRAY, k_r.move(0, 4), border_radius=8)
        pygame.draw.rect(screen, WHITE, k_r, border_radius=8)
        pygame.draw.rect(screen, DARK_GRAY, k_r, 2, border_radius=8)
        draw_text(key, 'KEY', DARK_GRAY, k_r.center)
        
        t_pos = (k_r.left - 15, k_r.centery) if align == 'left' else (k_r.right + 15, k_r.centery)
        s = fonts['DESC'].render(action, True, color)
        screen.blit(s, s.get_rect(midright=t_pos) if align == 'left' else s.get_rect(midleft=t_pos))

    init_game(True)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # UI 호버 로직
        if state == 'MAIN_MENU':
            for i in range(3):
                if pygame.Rect(SCREEN_W//2-200, SCREEN_H//2-50+i*75, 400, 60).collidepoint(mouse_pos): menu_sel = i
        elif state == 'PAUSE':
            for i in range(3):
                if pygame.Rect(SCREEN_W//2-100, SCREEN_H//2-40+i*60, 200, 40).collidepoint(mouse_pos): pause_sel = i

        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN:
                if state == 'MAIN_MENU':
                    if e.key == pygame.K_UP: menu_sel = (menu_sel - 1) % 3
                    elif e.key == pygame.K_DOWN: menu_sel = (menu_sel + 1) % 3
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if menu_sel == 0: state = 'START'
                        elif menu_sel == 1: state = 'INFO'
                        elif menu_sel == 2: sys.exit()
                elif state == 'INFO' and e.key == pygame.K_ESCAPE: state = 'MAIN_MENU'
                elif state == 'START' and e.key == pygame.K_SPACE: state = 'READY'
                
                elif state == 'READY':
                    if e.key == pygame.K_SPACE: state = 'PLAYING'
                    elif e.key == pygame.K_ESCAPE: state = 'PAUSE'

                elif state == 'PLAYING':
                    if e.key == pygame.K_ESCAPE: state = 'PAUSE'
                    elif e.key == pygame.K_c:
                         for b in bricks: b.active = False

                elif state == 'PAUSE':
                    if e.key == pygame.K_UP: pause_sel = (pause_sel - 1) % 3
                    elif e.key == pygame.K_DOWN: pause_sel = (pause_sel + 1) % 3
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if pause_sel == 0: state = 'PLAYING'
                        elif pause_sel == 1: init_game(True); state = 'MAIN_MENU'
                        elif pause_sel == 2: sys.exit()
                    elif e.key == pygame.K_ESCAPE: state = 'PLAYING'
                
                elif state in ['GAME_OVER', 'ALL_CLEAR']:
                    if e.key == pygame.K_SPACE: init_game(True); state = 'READY'
                    elif e.key == pygame.K_ESCAPE: init_game(True); state = 'MAIN_MENU'
            
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if state == 'MAIN_MENU':
                    for i, _ in enumerate(["START", "INFO", "QUIT"]):
                        if pygame.Rect(SCREEN_W//2-200, SCREEN_H//2-50+i*75, 400, 60).collidepoint(mouse_pos):
                            if i==0: state='START'
                            elif i==1: state='INFO'
                            else: sys.exit()
                elif state == 'PAUSE':
                    for i, _ in enumerate(["RESUME", "MENU", "QUIT"]):
                         if pygame.Rect(SCREEN_W//2-100, SCREEN_H//2-40+i*60, 200, 40).collidepoint(mouse_pos):
                            if i==0: state='PLAYING'
                            elif i==1: init_game(True); state='MAIN_MENU'
                            else: sys.exit()

        screen.fill(WHITE)

        if state == 'MAIN_MENU':
            draw_text("BRICK BREAKER", 'T', BLUE, (SCREEN_W//2, 150))
            for i, txt in enumerate(["START GAME", "INSTRUCTIONS", "QUIT GAME"]):
                col = ORANGE if i == menu_sel else DARK_GRAY
                r = draw_text(txt, 'SUB', col, (SCREEN_W//2, SCREEN_H//2 - 20 + i*75))
                if i == menu_sel: pygame.draw.rect(screen, ORANGE, r.inflate(40, 20), 3)

        elif state == 'INFO':
            screen.fill((245, 245, 250)); pygame.draw.rect(screen, HEADER_BG, (0,0,SCREEN_W, 110))
            draw_text("GAME INSTRUCTIONS", 'T', WHITE, (SCREEN_W//2, 55), True)
            y = 150
            draw_text("CONTROLS", 'M', ORANGE, (SCREEN_W//2, y))
            for t in ["Arrow Keys: Move", "SPACE: Launch", "ESC: Pause", "C: Cheat Clear"]:
                draw_text(t, 'K', DARK_GRAY, (SCREEN_W//2, y + 40)); y += 30
            y += 60
            draw_text("POWER-UPS", 'M', ORANGE, (SCREEN_W//2, y))
            for i, (k, d) in enumerate([('WIDE',"Paddle x1.5"), ('SLOW',"Speed x0.5 (Stacks)"), ('DBL',"Score x2"), ('LIFE',"+1 Life")]):
                py = y + 40 + i*40
                pygame.draw.rect(screen, P_COLORS[k], (SCREEN_W//2 - 150, py, 30, 30))
                draw_text(d, 'K', DARK_GRAY, (SCREEN_W//2 + 20, py + 15))

        elif state == 'START':
            draw_text("BRICK BREAKER", 'T', BLUE, (SCREEN_W//2, 200))
            draw_text("Press SPACE to Start", 'SUB', BLACK, (SCREEN_W//2, 300))
            draw_text(f"High Score: {highscore}", 'S', ORANGE, (SCREEN_W//2, 350))

        elif state in ['READY', 'PLAYING']:
            pygame.draw.rect(screen, HEADER_BG, (0,0,SCREEN_W, HEADER_H))
            draw_text(f"LEVEL: {level}/{MAX_LEVEL}", 'M', WHITE, (100, HEADER_H//2))
            draw_text(f"SCORE: {score}" + (" (x2)" if score_mult>1 else ""), 'L', WHITE, (SCREEN_W//2, HEADER_H//2))
            draw_text(f"♥ {lives}", 'M', RED, (SCREEN_W-60, HEADER_H//2))
            
            paddle.draw(screen); ball.draw(screen)
            for b in bricks: b.draw(screen)
            for p in powerups: p.draw(screen)

            if state == 'READY':
                ball.x = paddle.rect.centerx
                ball.y = paddle.rect.top - BALL_R
                draw_text("READY! Press SPACE", 'SUB', BLUE, (SCREEN_W//2, SCREEN_H//2 + 50))
            
            elif state == 'PLAYING':
                paddle.move()
                
                # --- [완전 재작성] 물리 엔진: 축 분리 이동 (Tunneling 방지) ---
                
                # 1. X축 이동
                ball.x += ball.dx
                ball.rect.centerx = int(ball.x)
                
                # X축 벽 충돌
                if ball.rect.left <= 0:
                    ball.x = BALL_R # 위치 보정
                    ball.dx = abs(ball.dx)
                elif ball.rect.right >= SCREEN_W:
                    ball.x = SCREEN_W - BALL_R # 위치 보정
                    ball.dx = -abs(ball.dx)
                ball.rect.centerx = int(ball.x) # Rect 동기화

                # X축 벽돌 충돌
                hit_idx = ball.rect.collidelist([b.rect for b in bricks if b.active])
                if hit_idx != -1:
                    b = [b for b in bricks if b.active][hit_idx]
                    b.active = False
                    
                    # 충돌 위치 보정 (Snapping) 및 반사
                    if ball.dx > 0: # 오른쪽으로 가다 맞음 -> 벽돌 왼쪽 면에 스냅
                        ball.x = b.rect.left - BALL_R
                    else: # 왼쪽으로 가다 맞음 -> 벽돌 오른쪽 면에 스냅
                        ball.x = b.rect.right + BALL_R
                    
                    ball.dx *= -1
                    ball.rect.centerx = int(ball.x) # Rect 즉시 동기화
                    
                    score += (10 + level*2) * score_mult
                    if random.random() < 0.2:
                        powerups.append(PowerUp(b.rect.centerx, b.rect.centery, random.choice(list(P_COLORS.keys()))))

                # 2. Y축 이동
                ball.y += ball.dy
                ball.rect.centery = int(ball.y)

                # Y축 벽 충돌 (천장)
                if ball.rect.top <= HEADER_H:
                    ball.y = HEADER_H + BALL_R # 위치 보정
                    ball.dy = abs(ball.dy)
                ball.rect.centery = int(ball.y) # Rect 동기화

                # 패들 충돌
                if ball.rect.colliderect(paddle.rect):
                    if ball.dy > 0: # 내려오다가 맞았을 때만
                        ball.y = paddle.rect.top - BALL_R # 패들 위로 보정
                        ball.dy *= -1
                        ball.rect.centery = int(ball.y)

                # Y축 벽돌 충돌
                hit_idx = ball.rect.collidelist([b.rect for b in bricks if b.active])
                if hit_idx != -1:
                    b = [b for b in bricks if b.active][hit_idx]
                    b.active = False
                    
                    # 충돌 위치 보정 (Snapping) 및 반사
                    if ball.dy > 0: # 내려오다 맞음 -> 벽돌 윗면에 스냅
                        ball.y = b.rect.top - BALL_R
                    else: # 올라가다 맞음 -> 벽돌 아랫면에 스냅
                        ball.y = b.rect.bottom + BALL_R
                    
                    ball.dy *= -1
                    ball.rect.centery = int(ball.y) # Rect 즉시 동기화

                    score += (10 + level*2) * score_mult
                    if random.random() < 0.2:
                        powerups.append(PowerUp(b.rect.centerx, b.rect.centery, random.choice(list(P_COLORS.keys()))))

                # 바닥 사망 체크
                if ball.rect.top > SCREEN_H:
                    lives -= 1
                    powerups.clear()
                    state = 'GAME_OVER' if lives <= 0 else 'READY'

                # --------------------------------------------------------

                if not any(b.active for b in bricks) and state == 'PLAYING':
                    screen.fill(WHITE)
                    draw_text(f"STAGE {level} CLEAR!", 'T', BLUE, (SCREEN_W//2, SCREEN_H//2))
                    pygame.display.flip()
                    
                    wait_start = pygame.time.get_ticks()
                    while pygame.time.get_ticks() - wait_start < 2000:
                        for e in pygame.event.get():
                            if e.type == pygame.QUIT: sys.exit()
                        clock.tick(FPS)
                    
                    if level >= MAX_LEVEL:
                        state = 'ALL_CLEAR'
                    else:
                        level += 1
                        init_game(False, False)
                        state = 'READY'

                for p in powerups[:]:
                    p.move()
                    if not p.active: powerups.remove(p)
                    elif p.rect.colliderect(paddle.rect):
                        if p.type == 'WIDE': paddle.rect.width = int(PADDLE_W * 1.5); timers['wide'] = POWERUP_DURATION
                        elif p.type == 'SLOW': 
                            if timers['slow'] == 0: ball.dx *= 0.5; ball.dy *= 0.5
                            timers['slow'] += POWERUP_DURATION 
                        elif p.type == 'DBL': score_mult = 2; timers['dbl'] = POWERUP_DURATION
                        elif p.type == 'LIFE': lives += 1
                        p.active = False; powerups.remove(p)

                if timers['wide'] > 0:
                    timers['wide'] -= 1
                    if timers['wide'] == 0: paddle.rect.width = PADDLE_W
                if timers['slow'] > 0:
                    timers['slow'] -= 1
                    if timers['slow'] == 0: ball.dx /= 0.5; ball.dy /= 0.5
                if timers['dbl'] > 0:
                    timers['dbl'] -= 1
                    if timers['dbl'] == 0: score_mult = 1

        elif state == 'PAUSE':
            s = pygame.Surface((SCREEN_W, SCREEN_H)); s.set_alpha(150); s.fill(BLACK); screen.blit(s, (0,0))
            draw_text("PAUSED", 'T', ORANGE, (SCREEN_W//2, SCREEN_H//2 - 100))
            for i, txt in enumerate(["RESUME", "MAIN MENU", "QUIT GAME"]):
                col = ORANGE if i == pause_sel else WHITE
                r = draw_text(txt, 'SUB', col, (SCREEN_W//2, SCREEN_H//2 - 20 + i*60))
                if i == pause_sel: pygame.draw.rect(screen, ORANGE, r.inflate(40, 20), 2)

        elif state == 'GAME_OVER':
            if score > highscore: highscore = score; json.dump({'highscore': score}, open(HIGHSCORE_FILE, 'w'))
            
            draw_text("GAME OVER", 'T', RED, (SCREEN_W//2, SCREEN_H//2 - 80))
            draw_text(f"Final Score: {score}", 'SUB', BLACK, (SCREEN_W//2, SCREEN_H//2 - 10))
            draw_text(f"High Score: {highscore}", 'SUB', ORANGE, (SCREEN_W//2, SCREEN_H//2 + 30))
            
            gy = SCREEN_H // 2 + 110
            draw_keycap("SPACE", "RESTART", BLUE, (SCREEN_W//2 - 20, gy), 'left')
            draw_keycap("ESC", "MENU", ORANGE, (SCREEN_W//2 + 20, gy), 'right')

        elif state == 'ALL_CLEAR':
            if score > highscore: highscore = score; json.dump({'highscore': score}, open(HIGHSCORE_FILE, 'w'))
            
            draw_text("CONGRATULATIONS!", 'T', BLUE, (SCREEN_W//2, SCREEN_H//2 - 100))
            draw_text("ALL LEVELS CLEARED!", 'L', ORANGE, (SCREEN_W//2, SCREEN_H//2 - 30))
            draw_text(f"Final Score: {score}", 'SUB', BLACK, (SCREEN_W//2, SCREEN_H//2 + 40))
            
            gy = SCREEN_H // 2 + 140
            draw_keycap("SPACE", "RESTART", BLUE, (SCREEN_W//2 - 20, gy), 'left')
            draw_keycap("ESC", "MENU", ORANGE, (SCREEN_W//2 + 20, gy), 'right')

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__": main()