import pygame, sys, random, json, os, math

# --- 설정 상수 ---
SCREEN_W, SCREEN_H = 825, 600
PADDLE_W, PADDLE_H = 100, 10
BALL_R, BRICK_W, BRICK_H = 10, 75, 20
BRICK_COLS = 10 
FPS, HEADER_H = 60, 60

# 색상
WHITE, BLACK, RED = (255, 255, 255), (0, 0, 0), (255, 0, 0)
BLUE, GREEN, ORANGE = (0, 0, 255), (0, 255, 0), (255, 165, 0)
DARK_GRAY, SHADOW_GRAY = (50, 50, 50), (200, 200, 200)
HEADER_BG = (50, 50, 50)
P_COLORS = {'WIDE': (0,200,255), 'SLOW': (200,100,255), 'DBL': (255,200,0), 'LIFE': (255,100,100)}

INITIAL_LIVES, POWERUP_DURATION = 3, 300
HIGHSCORE_FILE = "highscore.json"
MAX_LEVEL = 10
SLOW_FACTOR = 0.7 

# --- 메타데이터 ---
__title__ = 'Python Brick Breaker'
__version__ = '1.6.4' # 최종 클리어 화면 수정
__author__ = 'Python Developer'

# --- 클래스 ---
class Paddle:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_W//2 - PADDLE_W//2, SCREEN_H - 40, PADDLE_W, PADDLE_H)
        self.speed = 8
    def move(self):
        k = pygame.key.get_pressed()
        if k[pygame.K_LEFT] and self.rect.left > 0: self.rect.x -= self.speed
        if k[pygame.K_RIGHT] and self.rect.right < SCREEN_W: self.rect.x += self.speed
    def draw(self, s): pygame.draw.rect(s, BLUE, self.rect)

class Ball:
    def __init__(self): self.reset(1)
    def reset(self, lv):
        self.x, self.y = SCREEN_W / 2, SCREEN_H / 2
        self.rect = pygame.Rect(int(self.x), int(self.y), BALL_R*2, BALL_R*2)
        spd = min(4 + (lv * 0.2), 10)
        self.dx, self.dy = random.choice([-spd, spd]), -spd
    def draw(self, s): 
        self.rect.center = (int(self.x), int(self.y))
        pygame.draw.circle(s, RED, self.rect.center, BALL_R)

class Brick:
    def __init__(self, x, y): self.rect, self.active = pygame.Rect(x, y, BRICK_W, BRICK_H), True
    def draw(self, s):
        if self.active: pygame.draw.rect(s, GREEN, self.rect); pygame.draw.rect(s, BLACK, self.rect, 1)

class PowerUp:
    def __init__(self, x, y, t): self.rect, self.type, self.active = pygame.Rect(x, y, 20, 20), t, True
    def move(self):
        self.rect.y += 3
        if self.rect.top > SCREEN_H: self.active = False
    def draw(self, s):
        if self.active: pygame.draw.rect(s, P_COLORS[self.type], self.rect); pygame.draw.rect(s, BLACK, self.rect, 2)

# --- 메인 ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Brick Breaker v1.6.6")
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
    
    try: highscore = json.load(open(HIGHSCORE_FILE))['highscore']
    except: pass

    def init_game(full_reset=False, keep_level=False):
        nonlocal score, level, lives, score_mult, timers
        if full_reset: score, level, lives = 0, 1, INITIAL_LIVES
        paddle.rect.width, paddle.rect.centerx = PADDLE_W, SCREEN_W // 2
        score_mult, timers = 1, {k: 0 for k in timers}
        powerups.clear(); ball.reset(level)
        if not keep_level:
            bricks.clear()
            rows = min(2 + level, 9)
            sx = (SCREEN_W - (BRICK_COLS * (BRICK_W + 5) - 5)) // 2
            for r in range(rows):
                for c in range(BRICK_COLS):
                    bricks.append(Brick(sx + c*(BRICK_W+5), 80 + r*(BRICK_H+5)))

    def draw_text(txt, fk, col, center, shadow=False):
        if shadow:
            s = fonts[fk].render(txt, True, BLACK)
            screen.blit(s, s.get_rect(center=(center[0]+3, center[1]+3)))
        s = fonts[fk].render(txt, True, col)
        r = s.get_rect(center=center)
        screen.blit(s, r)
        return r

    def draw_keycap(k, act, col, mid, align='left'):
        kr = pygame.Rect(0, 0, 120 if k=="SPACE" else 80, 40)
        if align == 'left': kr.midright = mid
        elif align == 'right': kr.midleft = mid
        else: kr.topleft = mid

        pygame.draw.rect(screen, SHADOW_GRAY, kr.move(0, 4), border_radius=8)
        pygame.draw.rect(screen, WHITE, kr, border_radius=8)
        pygame.draw.rect(screen, DARK_GRAY, kr, 2, border_radius=8)
        draw_text(k, 'KEY', DARK_GRAY, kr.center)
        
        t_pos = (kr.left - 15, kr.centery) if align == 'left' else (kr.right + 15, kr.centery)
        if align == 'custom': t_pos = (kr.right + 20, kr.centery)
        
        s = fonts['K' if align == 'custom' else 'DESC'].render(act, True, DARK_GRAY if align == 'custom' else col)
        r = s.get_rect(midleft=t_pos) if align in ['right', 'custom'] else s.get_rect(midright=t_pos)
        screen.blit(s, r)

    def draw_menu_buttons(items, sel_idx, start_y):
        for i, txt in enumerate(items):
            col = ORANGE if i == sel_idx else DARK_GRAY
            r = draw_text(txt, 'SUB', col, (SCREEN_W//2, start_y + i*75))
            if i == sel_idx: pygame.draw.rect(screen, ORANGE, r.inflate(40, 20), 3)

    def draw_end_screen(title, msg, col):
        draw_text(title, 'T', col, (SCREEN_W//2, SCREEN_H//2 - 120))
        if msg: draw_text(msg, 'L', ORANGE, (SCREEN_W//2, SCREEN_H//2 - 50))
        draw_text(f"Final Score: {score}", 'SUB', BLACK, (SCREEN_W//2, SCREEN_H//2 + 10))
        
        # [수정 1] ALL_CLEAR 상태에서도 High Score 표시되도록 조건 변경
        if state in ['GAME_OVER', 'ALL_CLEAR']: 
            draw_text(f"High Score: {highscore}", 'SUB', ORANGE, (SCREEN_W//2, SCREEN_H//2 + 50))
            
        gy = SCREEN_H // 2 + 130
        draw_keycap("SPACE", "RESTART", BLUE, (SCREEN_W//2 - 20, gy), 'left')
        draw_keycap("ESC", "MENU", ORANGE, (SCREEN_W//2 + 20, gy), 'right')

    init_game(True)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        events = pygame.event.get()

        if state == 'MAIN_MENU':
            for i in range(3):
                if pygame.Rect(SCREEN_W//2-200, 280+i*75, 400, 60).collidepoint(mouse_pos): menu_sel = i
        elif state == 'PAUSE':
            for i in range(3):
                if pygame.Rect(SCREEN_W//2-100, 260+i*60, 200, 40).collidepoint(mouse_pos): pause_sel = i

        for e in events:
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
                    if menu_sel == 0: state = 'START'
                    elif menu_sel == 1: state = 'INFO'
                    else: sys.exit()
                elif state == 'PAUSE':
                    if pause_sel == 0: state = 'PLAYING'
                    elif pause_sel == 1: init_game(True); state = 'MAIN_MENU'
                    else: sys.exit()

        screen.fill(WHITE)

        if state == 'MAIN_MENU':
            draw_text("BRICK BREAKER", 'T', BLUE, (SCREEN_W//2, 150))
            draw_menu_buttons(["START GAME", "INSTRUCTIONS", "QUIT GAME"], menu_sel, 280)

        elif state == 'INFO':
            screen.fill((245, 245, 250)); pygame.draw.rect(screen, HEADER_BG, (0,0,SCREEN_W, 110))
            draw_text("GAME INSTRUCTIONS", 'T', WHITE, (SCREEN_W//2, 55), True)
            
            draw_text("CONTROLS", 'M', ORANGE, (SCREEN_W//2, 150))
            draw_keycap("SPACE", "Launch", WHITE, (SCREEN_W//2 - 150, 190), 'custom')
            draw_keycap("ESC", "Pause", WHITE, (SCREEN_W//2 - 150, 245), 'custom')
            draw_keycap("← / →", "Move", WHITE, (SCREEN_W//2 - 150, 300), 'custom')

            draw_text("POWER-UPS", 'M', ORANGE, (SCREEN_W//2, 370))
            for i, (k, d) in enumerate([('WIDE',"Paddle x2.0"), ('SLOW',"Speed x0.7 (Stacks)"), ('DBL',"Score x2"), ('LIFE',"+1 Life")]):
                py = 410 + i*40
                pygame.draw.rect(screen, P_COLORS[k], (SCREEN_W//2 - 150, py, 30, 30))
                draw_text(d, 'K', DARK_GRAY, (SCREEN_W//2 + 20, py + 15))

        elif state == 'START':
            draw_text("BRICK BREAKER", 'T', BLUE, (SCREEN_W//2, 200))
            draw_text("Press SPACE to Start", 'SUB', BLACK, (SCREEN_W//2, 300))
            draw_text(f"High Score: {highscore}", 'S', ORANGE, (SCREEN_W//2, 350))

        elif state in ['READY', 'PLAYING']:
            pygame.draw.rect(screen, HEADER_BG, (0,0,SCREEN_W, HEADER_H))
            sc = WHITE
            if timers['dbl']>0: sc=P_COLORS['DBL']
            elif timers['slow']>0: sc=P_COLORS['SLOW']
            elif timers['wide']>0: sc=P_COLORS['WIDE']

            draw_text(f"LEVEL: {level}/{MAX_LEVEL}", 'M', WHITE, (100, HEADER_H//2))
            draw_text(f"SCORE: {score}"+(" (x2)" if score_mult>1 else ""), 'L', sc, (SCREEN_W//2, HEADER_H//2))
            draw_text(f"♥ {lives}", 'M', RED, (SCREEN_W-60, HEADER_H//2))
            
            paddle.draw(screen); ball.draw(screen)
            for b in bricks: b.draw(screen)
            for p in powerups: p.draw(screen)

            if state == 'READY':
                ball.x, ball.y = paddle.rect.centerx, paddle.rect.top - BALL_R
                draw_text("READY! Press SPACE", 'SUB', BLUE, (SCREEN_W//2, SCREEN_H//2 + 50))
            
            elif state == 'PLAYING':
                paddle.move()
                ball.x += ball.dx; ball.rect.centerx = int(ball.x)
                if ball.rect.left <= 0: ball.x, ball.dx = BALL_R, abs(ball.dx)
                elif ball.rect.right >= SCREEN_W: ball.x, ball.dx = SCREEN_W - BALL_R, -abs(ball.dx)
                ball.rect.centerx = int(ball.x)

                hit = ball.rect.collidelist([b.rect for b in bricks if b.active])
                if hit != -1:
                    b = [b for b in bricks if b.active][hit]; b.active = False
                    ball.x = b.rect.left - BALL_R if ball.dx > 0 else b.rect.right + BALL_R
                    ball.dx *= -1; ball.rect.centerx = int(ball.x)
                    score += (10+level*2)*score_mult
                    if random.random() < 0.2: powerups.append(PowerUp(b.rect.centerx, b.rect.centery, random.choice(list(P_COLORS.keys()))))

                ball.y += ball.dy; ball.rect.centery = int(ball.y)
                if ball.rect.top <= HEADER_H: ball.y, ball.dy = HEADER_H + BALL_R, abs(ball.dy)
                ball.rect.centery = int(ball.y)

                if ball.rect.colliderect(paddle.rect) and ball.dy > 0:
                    ball.y = paddle.rect.top - BALL_R
                    ball.rect.centery = int(ball.y)
                    ball.dy *= -1
                    hit_pos = max(-1, min(1, (ball.rect.centerx - paddle.rect.centerx)/(paddle.rect.width/2)))
                    cur_spd = math.hypot(ball.dx, ball.dy)
                    ball.dx += hit_pos * 3.0
                    new_spd = math.hypot(ball.dx, ball.dy)
                    ball.dx, ball.dy = (ball.dx/new_spd)*cur_spd, (ball.dy/new_spd)*cur_spd

                hit = ball.rect.collidelist([b.rect for b in bricks if b.active])
                if hit != -1:
                    b = [b for b in bricks if b.active][hit]; b.active = False
                    ball.y = b.rect.top - BALL_R if ball.dy > 0 else b.rect.bottom + BALL_R
                    ball.dy *= -1; ball.rect.centery = int(ball.y)
                    score += (10+level*2)*score_mult
                    if random.random() < 0.2: powerups.append(PowerUp(b.rect.centerx, b.rect.centery, random.choice(list(P_COLORS.keys()))))

                if ball.rect.top > SCREEN_H:
                    lives -= 1; powerups.clear(); state = 'GAME_OVER' if lives <= 0 else 'READY'

                if not any(b.active for b in bricks):
                    screen.fill(WHITE); draw_text(f"STAGE {level} CLEAR!", 'T', BLUE, (SCREEN_W//2, SCREEN_H//2))
                    pygame.display.flip()
                    pygame.time.wait(2000)
                    # [수정 2] 대기 시간 동안 쌓인 키 입력(스페이스바 등) 제거 -> 자동 시작 방지
                    pygame.event.clear() 
                    
                    if level >= MAX_LEVEL: state = 'ALL_CLEAR'
                    else: level += 1; init_game(False, False); state = 'READY'

                for p in powerups[:]:
                    p.move()
                    if not p.active: powerups.remove(p)
                    elif p.rect.colliderect(paddle.rect):
                        if p.type == 'WIDE': 
                            pc = paddle.rect.centerx
                            paddle.rect.width = int(PADDLE_W * 2.0); paddle.rect.centerx = pc
                            timers['wide'] = POWERUP_DURATION
                        elif p.type == 'SLOW': 
                            if timers['slow'] == 0: ball.dx *= SLOW_FACTOR; ball.dy *= SLOW_FACTOR
                            timers['slow'] += POWERUP_DURATION 
                        elif p.type == 'DBL': score_mult = 2; timers['dbl'] = POWERUP_DURATION
                        elif p.type == 'LIFE': lives += 1
                        p.active = False; powerups.remove(p)

                if timers['wide'] > 0:
                    timers['wide'] -= 1
                    if timers['wide'] == 0: pc = paddle.rect.centerx; paddle.rect.width = PADDLE_W; paddle.rect.centerx = pc
                if timers['slow'] > 0:
                    timers['slow'] -= 1
                    if timers['slow'] == 0: ball.dx /= SLOW_FACTOR; ball.dy /= SLOW_FACTOR
                if timers['dbl'] > 0:
                    timers['dbl'] -= 1
                    if timers['dbl'] == 0: score_mult = 1

        elif state == 'PAUSE':
            s = pygame.Surface((SCREEN_W, SCREEN_H)); s.set_alpha(150); s.fill(BLACK); screen.blit(s, (0,0))
            draw_text("PAUSED", 'T', ORANGE, (SCREEN_W//2, SCREEN_H//2 - 100))
            draw_menu_buttons(["RESUME", "MAIN MENU", "QUIT GAME"], pause_sel, 260)

        elif state == 'GAME_OVER':
            if score > highscore: highscore = score; json.dump({'highscore': score}, open(HIGHSCORE_FILE, 'w'))
            draw_end_screen("GAME OVER", None, RED)

        elif state == 'ALL_CLEAR':
            if score > highscore: highscore = score; json.dump({'highscore': score}, open(HIGHSCORE_FILE, 'w'))
            draw_end_screen("CONGRATULATIONS!", "ALL LEVELS CLEARED!", BLUE)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__": main()