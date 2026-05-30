import pygame
import random
import copy

# --- 常量 ---
CELL_SIZE = 30
COLS = 10
ROWS = 20
SIDE_PANEL = 200
WIDTH = COLS * CELL_SIZE + SIDE_PANEL
HEIGHT = ROWS * CELL_SIZE
FPS = 60
BASE_FALL_INTERVAL = 800  # 毫秒

# 颜色定义
COLORS = {
    'I': (0, 240, 240),   # 青色
    'O': (240, 240, 0),   # 黄色
    'T': (160, 0, 240),   # 紫色
    'S': (0, 240, 0),     # 绿色
    'Z': (240, 0, 0),     # 红色
    'J': (0, 0, 240),     # 蓝色
    'L': (240, 160, 0),   # 橙色
}
BG_COLOR = (20, 20, 30)
GRID_COLOR = (40, 40, 55)
PANEL_BG = (30, 30, 45)
TEXT_COLOR = (220, 220, 220)
BORDER_COLOR = (80, 80, 100)

# 七种方块形状（4个旋转状态）
SHAPES = {
    'I': [[(0, 0), (0, 1), (0, 2), (0, 3)],
          [(0, 0), (1, 0), (2, 0), (3, 0)],
          [(0, 0), (0, 1), (0, 2), (0, 3)],
          [(0, 0), (1, 0), (2, 0), (3, 0)]],
    'O': [[(0, 0), (0, 1), (1, 0), (1, 1)],
          [(0, 0), (0, 1), (1, 0), (1, 1)],
          [(0, 0), (0, 1), (1, 0), (1, 1)],
          [(0, 0), (0, 1), (1, 0), (1, 1)]],
    'T': [[(0, 0), (0, 1), (0, 2), (1, 1)],
          [(0, 0), (1, 0), (2, 0), (1, 1)],
          [(1, 0), (0, 1), (1, 1), (1, 2)],
          [(1, 0), (0, 1), (1, 1), (2, 1)]],
    'S': [[(1, 0), (1, 1), (0, 1), (0, 2)],
          [(0, 0), (1, 0), (1, 1), (2, 1)],
          [(1, 0), (1, 1), (0, 1), (0, 2)],
          [(0, 0), (1, 0), (1, 1), (2, 1)]],
    'Z': [[(0, 0), (0, 1), (1, 1), (1, 2)],
          [(1, 0), (0, 1), (1, 1), (0, 2)],
          [(0, 0), (0, 1), (1, 1), (1, 2)],
          [(1, 0), (0, 1), (1, 1), (0, 2)]],
    'J': [[(0, 0), (1, 0), (1, 1), (1, 2)],
          [(0, 0), (0, 1), (1, 0), (2, 0)],
          [(0, 0), (0, 1), (0, 2), (1, 2)],
          [(2, 0), (0, 1), (1, 1), (2, 1)]],
    'L': [[(1, 0), (0, 0), (0, 1), (0, 2)],
          [(0, 0), (1, 0), (2, 0), (2, 1)],
          [(1, 0), (1, 1), (1, 2), (0, 2)],
          [(0, 0), (0, 1), (1, 1), (2, 1)]],
}

# SRS 踢墙数据 (Wall Kick Data)
# JLSTZ 踢墙: (rot_from, rot_to) -> [(dx, dy), ...]
KICK_JLSTZ = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (0, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
}

# I 方块踢墙
KICK_I = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
}

# 按键重复参数 (毫秒)
DAS_DELAY = 170   # 按住多久后开始连续移动
ARR_DELAY = 50    # 连续移动间隔


class Tetris:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("俄罗斯方块 - Tetris")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simhei", 22)
        self.small_font = pygame.font.SysFont("simhei", 16)

        # 按键计时器 (替代 pygame.time.wait)
        self.key_timers = {'left': 0, 'right': 0, 'down': 0}
        self.key_held = {'left': False, 'right': False, 'down': False}

        self.reset_game()

    def reset_game(self):
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.board_color = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False
        self.fall_interval = BASE_FALL_INTERVAL
        self.fall_timer = 0
        self.lock_delay = 500  # 锁定延迟 (ms)
        self.lock_timer = 0
        self.lock_moves = 0   # 锁定期间移动次数
        self.max_lock_moves = 15
        self.current_piece = None
        self.next_piece = None
        self._spawn_piece()

    def _spawn_piece(self):
        if self.next_piece is None:
            self.next_piece = self._random_piece()
        self.current_piece = self.next_piece
        self.next_piece = self._random_piece()

        piece_cols = max(c for _, c in self.current_piece['shape']) + 1
        self.piece_x = (COLS - piece_cols) // 2
        self.piece_y = 0
        self.piece_rot = 0
        self.lock_timer = 0
        self.lock_moves = 0

        if self._collides(self.current_piece['shape'], self.piece_x, self.piece_y):
            self.game_over = True

    def _random_piece(self):
        name = random.choice(list(SHAPES.keys()))
        return {'name': name, 'shape': copy.deepcopy(SHAPES[name][0]), 'color': COLORS[name]}

    def _collides(self, shape, px, py):
        for r, c in shape:
            br, bc = py + r, px + c
            if bc < 0 or bc >= COLS or br >= ROWS:
                return True
            if br >= 0 and self.board[br][bc] is not None:
                return True
        return False

    def _get_kicks(self, old_rot, new_rot):
        """获取 SRS 踢墙偏移量"""
        name = self.current_piece['name']
        if name == 'I':
            return KICK_I.get((old_rot, new_rot), [(0, 0)])
        elif name == 'O':
            return [(0, 0)]
        else:
            return KICK_JLSTZ.get((old_rot, new_rot), [(0, 0)])

    def _try_rotate(self):
        """尝试旋转，使用 SRS 踢墙"""
        name = self.current_piece['name']
        new_rot = (self.piece_rot + 1) % 4
        new_shape = SHAPES[name][new_rot]

        kicks = self._get_kicks(self.piece_rot, new_rot)
        for dx, dy in kicks:
            if not self._collides(new_shape, self.piece_x + dx, self.piece_y - dy):
                self.current_piece['shape'] = copy.deepcopy(new_shape)
                self.piece_rot = new_rot
                self.piece_x += dx
                self.piece_y -= dy
                self._on_piece_move()
                return True
        return False

    def _on_piece_move(self):
        """方块移动或旋转后调用，处理锁延迟"""
        if self.lock_timer > 0 or self._is_on_ground():
            self.lock_moves += 1
            if self.lock_moves > self.max_lock_moves:
                self._lock_piece()
            else:
                self.lock_timer = 0

    def _is_on_ground(self):
        """检查方块是否着地"""
        return self._collides(self.current_piece['shape'], self.piece_x, self.piece_y + 1)

    def _lock_piece(self):
        """将当前方块固定到棋盘上"""
        shape = self.current_piece['shape']
        color = self.current_piece['color']
        for r, c in shape:
            br, bc = self.piece_y + r, self.piece_x + c
            if 0 <= br < ROWS and 0 <= bc < COLS:
                self.board[br][bc] = True
                self.board_color[br][bc] = color
        self._clear_lines()
        self._spawn_piece()

    def _clear_lines(self):
        cleared = 0
        r = ROWS - 1
        while r >= 0:
            if all(self.board[r][c] is not None for c in range(COLS)):
                del self.board[r]
                del self.board_color[r]
                self.board.insert(0, [None for _ in range(COLS)])
                self.board_color.insert(0, [None for _ in range(COLS)])
                cleared += 1
            else:
                r -= 1

        if cleared:
            self.lines_cleared += cleared
            scores = [0, 100, 300, 500, 800]
            self.score += scores[cleared] * self.level
            self.level = self.lines_cleared // 10 + 1
            self.fall_interval = max(50, BASE_FALL_INTERVAL - (self.level - 1) * 70)

    def _hard_drop(self):
        """直接落到底部"""
        drop_distance = 0
        while not self._collides(self.current_piece['shape'], self.piece_x, self.piece_y + 1):
            self.piece_y += 1
            drop_distance += 1
        self.score += drop_distance * 2
        self._lock_piece()

    def _ghost_y(self):
        """计算投影 (ghost piece) 的Y坐标"""
        gy = self.piece_y
        while not self._collides(self.current_piece['shape'], self.piece_x, gy + 1):
            gy += 1
        return gy

    def handle_events(self):
        dt = self.clock.get_time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                # 全局按键
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    continue

                if event.key == pygame.K_p:
                    self.paused = not self.paused
                    continue

                if self.paused:
                    continue

                # 游戏中的单次按键
                if event.key == pygame.K_UP:
                    self._try_rotate()

                elif event.key == pygame.K_SPACE:
                    self._hard_drop()

                # 左右键：开始计时
                elif event.key == pygame.K_LEFT:
                    self.key_timers['left'] = 0
                    self.key_held['left'] = True
                    if not self._collides(self.current_piece['shape'], self.piece_x - 1, self.piece_y):
                        self.piece_x -= 1
                        self._on_piece_move()

                elif event.key == pygame.K_RIGHT:
                    self.key_timers['right'] = 0
                    self.key_held['right'] = True
                    if not self._collides(self.current_piece['shape'], self.piece_x + 1, self.piece_y):
                        self.piece_x += 1
                        self._on_piece_move()

                elif event.key == pygame.K_DOWN:
                    self.key_timers['down'] = 0
                    self.key_held['down'] = True
                    if not self._collides(self.current_piece['shape'], self.piece_x, self.piece_y + 1):
                        self.piece_y += 1
                        self.score += 1

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    self.key_held['left'] = False
                    self.key_timers['left'] = 0
                elif event.key == pygame.K_RIGHT:
                    self.key_held['right'] = False
                    self.key_timers['right'] = 0
                elif event.key == pygame.K_DOWN:
                    self.key_held['down'] = False
                    self.key_timers['down'] = 0

        return True

    def _handle_held_keys(self, dt):
        """处理按住按键的重复移动 (DAS/ARR)"""
        if self.game_over or self.paused:
            return

        for key, direction in [('left', -1), ('right', 1)]:
            if self.key_held[key]:
                self.key_timers[key] += dt
                delay = DAS_DELAY if self.key_timers[key] < DAS_DELAY + ARR_DELAY else ARR_DELAY
                if self.key_timers[key] >= DAS_DELAY:
                    while self.key_timers[key] >= delay:
                        self.key_timers[key] -= ARR_DELAY
                        if not self._collides(self.current_piece['shape'], self.piece_x + direction, self.piece_y):
                            self.piece_x += direction
                            self._on_piece_move()

        if self.key_held['down']:
            self.key_timers['down'] += dt
            while self.key_timers['down'] >= max(30, ARR_DELAY // 2):
                self.key_timers['down'] -= max(30, ARR_DELAY // 2)
                if not self._collides(self.current_piece['shape'], self.piece_x, self.piece_y + 1):
                    self.piece_y += 1
                    self.score += 1

    def update(self, dt):
        if self.game_over or self.paused:
            return

        # 处理按键重复
        self._handle_held_keys(dt)

        # 处理下落
        self.fall_timer += dt
        if self.fall_timer >= self.fall_interval:
            self.fall_timer = 0
            if not self._collides(self.current_piece['shape'], self.piece_x, self.piece_y + 1):
                self.piece_y += 1
                self.lock_timer = 0
                self.lock_moves = 0
            else:
                # 着地了，开始锁延迟倒计时
                self.lock_timer += self.fall_interval
                if self.lock_timer >= self.lock_delay:
                    self._lock_piece()

    def draw(self):
        self.screen.fill(BG_COLOR)

        # 绘制网格线
        for r in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, GRID_COLOR, rect, 1)

        # 绘制已固定的方块
        for r in range(ROWS):
            for c in range(COLS):
                if self.board[r][c] is not None:
                    self._draw_cell(r, c, self.board_color[r][c])

        # 绘制投影 (ghost piece)
        if self.current_piece and not self.game_over and not self.paused:
            gy = self._ghost_y()
            if gy != self.piece_y:
                shape = self.current_piece['shape']
                color = self.current_piece['color']
                for r, c in shape:
                    br, bc = gy + r, self.piece_x + c
                    if 0 <= br < ROWS and 0 <= bc < COLS:
                        self._draw_ghost_cell(br, bc, color)

        # 绘制当前方块
        if self.current_piece and not self.game_over:
            shape = self.current_piece['shape']
            color = self.current_piece['color']
            for r, c in shape:
                br, bc = self.piece_y + r, self.piece_x + c
                if 0 <= br < ROWS:
                    self._draw_cell(br, bc, color)

        # 右侧信息面板
        panel_x = COLS * CELL_SIZE
        pygame.draw.rect(self.screen, PANEL_BG, (panel_x, 0, SIDE_PANEL, HEIGHT))
        pygame.draw.line(self.screen, BORDER_COLOR, (panel_x, 0), (panel_x, HEIGHT), 2)

        x = panel_x + 15
        y = 20

        def draw_text(text, y_pos, font=None, color=TEXT_COLOR):
            f = font or self.font
            surf = f.render(text, True, color)
            self.screen.blit(surf, (x, y_pos))
            return y_pos + surf.get_height() + 10

        y = draw_text("俄罗斯方块", y)
        y += 10
        y = draw_text(f"分数: {self.score}", y)
        y = draw_text(f"等级: {self.level}", y)
        y = draw_text(f"行数: {self.lines_cleared}", y)
        y += 20

        # 下一方块预览
        y = draw_text("下一方块:", y, self.small_font, (150, 150, 150))
        if self.next_piece:
            preview_shape = SHAPES[self.next_piece['name']][0]
            preview_color = self.next_piece['color']
            min_r = min(r for r, _ in preview_shape)
            min_c = min(c for _, c in preview_shape)
            max_r = max(r for r, _ in preview_shape)
            max_c = max(c for _, c in preview_shape)
            pw = (max_c - min_c + 1) * 22
            ph = (max_r - min_r + 1) * 22
            px_start = panel_x + (SIDE_PANEL - pw) // 2
            py_start = y + 5

            for r, c in preview_shape:
                rx = px_start + (c - min_c) * 22
                ry = py_start + (r - min_r) * 22
                inner = pygame.Rect(rx + 2, ry + 2, 18, 18)
                pygame.draw.rect(self.screen, preview_color, inner)
                # 修复: 确保是 tuple 而非 generator
                highlight = tuple(min(c + 50, 255) for c in preview_color)
                pygame.draw.rect(self.screen, highlight, inner.inflate(-4, -4))
                pygame.draw.rect(self.screen, (0, 0, 0), inner, 1)

        y = py_start + ph + 30

        # 操作提示
        y = draw_text("操作:", y, self.small_font, (150, 150, 150))
        tips = [
            "← →  左右移动",
            "↑     旋转",
            "↓     加速下落",
            "空格  直接落底",
            "P     暂停",
            "R     重新开始",
        ]
        for tip in tips:
            y = draw_text(tip, y, self.small_font)

        # 游戏结束 / 暂停 提示
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            go_text = self.font.render("游戏结束", True, (255, 80, 80))
            restart_text = self.small_font.render("按 R 重新开始", True, TEXT_COLOR)
            self.screen.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2 - 40))
            self.screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))

        elif self.paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            pause_text = self.font.render("暂停中", True, TEXT_COLOR)
            tip_text = self.small_font.render("按 P 继续", True, (150, 150, 150))
            self.screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 30))
            self.screen.blit(tip_text, (WIDTH // 2 - tip_text.get_width() // 2, HEIGHT // 2 + 10))

        pygame.display.flip()

    def _draw_cell(self, row, col, color):
        x = col * CELL_SIZE
        y = row * CELL_SIZE
        inner = pygame.Rect(x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2)
        pygame.draw.rect(self.screen, color, inner)
        # 高光效果
        highlight = tuple(min(c + 60, 255) for c in color)
        pygame.draw.rect(self.screen, highlight, inner.inflate(-6, -6))
        pygame.draw.rect(self.screen, (0, 0, 0), inner, 1)

    def _draw_ghost_cell(self, row, col, color):
        x = col * CELL_SIZE
        y = row * CELL_SIZE
        # 使用更亮的幽灵色：半透明效果
        ghost_color = tuple(min(c + 100, 255) for c in color)
        inner = pygame.Rect(x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2)
        pygame.draw.rect(self.screen, ghost_color, inner, 2)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            running = self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()


if __name__ == "__main__":
    game = Tetris()
    game.run()
