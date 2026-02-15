import pygame
import random
import math
import sys
from srs_data import *

# --- CONFIG ---
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20 # Visible height. Usually there is buffer.
BUFFER_HEIGHT = 20 # Extra height for spawning
TOTAL_HEIGHT = GRID_HEIGHT + BUFFER_HEIGHT
SCREEN_WIDTH = 1200  # Dual player layout (600 x 2)
SCREEN_HEIGHT = 850
FPS = 60

# Actions
ACTION_NONE = 0
ACTION_LEFT = 1
ACTION_RIGHT = 2
ACTION_DOWN = 3 # Soft drop
ACTION_DROP = 4 # Hard drop
ACTION_ROTATE_R = 5
ACTION_ROTATE_L = 6
ACTION_HOLD = 7

class TetrisGame:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(TOTAL_HEIGHT)]
        self.bag = []
        self.current_piece = None
        self.hold_piece = None
        self.hold_used = False
        self.score = 0
        self.game_over = False
        self.combo = -1
        self.back_to_back = False
        
        # Current Piece State
        self.piece_x = 0
        self.piece_y = 0
        self.piece_rot = 0
        self.piece_type = 0
        
        # Animation State
        self.clearing_lines = []   
        self.clear_timer = 0       
        self.clear_anim_duration = 500 # ms
        self.in_clear_anim = False
        self.is_perfect_clear = False # New state for Perfect Clear
        self.last_move_rotate = False # For T-Spin detection
        self.is_tspin = 0 # 0=None, 1=Mini, 2=Normal
        self.show_b2b = False # Display flag for Back-to-Back

        self._fill_bag()
        self._spawn_piece()

    def _fill_bag(self):
        new_bag = [MINO_I, MINO_J, MINO_L, MINO_O, MINO_S, MINO_T, MINO_Z]
        random.shuffle(new_bag)
        self.bag.extend(new_bag)

    def _spawn_piece(self):
        if len(self.bag) < 7:
            self._fill_bag()
        
        self.piece_type = self.bag.pop(0)
        self.piece_rot = ROT_0
        self.piece_x = 3 # Standard spawn x
        self.piece_y = 18 # Spawn just above visible area (index 20 starts visible)
        
        # Check collision immediately (Game Over condition)
        if self._check_collision(self.piece_x, self.piece_y, self.piece_rot, self.piece_type):
            self.game_over = True

        self.hold_used = False

    def update(self, dt):
        """Update game state (animation progress). Returns True if animation finished this frame."""
        if self.in_clear_anim:
            self.clear_timer += dt
            if self.clear_timer >= self.clear_anim_duration:
                self._finalize_clear()
                self.in_clear_anim = False
                self._spawn_piece()
                self.hold_used = False # Reset hold on new spawn
                return True
        return False

    def _finalize_clear(self):
        # Actually remove lines from grid
        new_grid = [row for i, row in enumerate(self.grid) if i not in self.clearing_lines]
        # Add empty lines at top
        for _ in range(len(self.clearing_lines)):
            new_grid.insert(0, [0 for _ in range(GRID_WIDTH)])
        self.grid = new_grid
        self.clearing_lines = []

    def _get_blocks(self, x, y, rot, p_type):
        """Returns the absolute coordinates of the 4 blocks of a piece."""
        # Using the standard shapes for now (simplified shapes can be defined in srs_data)
        # We need to map the shape definitions (which are usually 0-3 based) to board coords
        # This part requires interpreting the SHAPES structure from srs_data correctly.
        # Let's assume SHAPES stores relative offsets or local grid coords.
        
        # Simple definition: SHAPES[type][rot] returns list of (lx, ly)
        # Actual board x = x + lx, y = y + ly
        
        local_coords = SHAPES[p_type][rot]
        world_coords = []
        for lx, ly in local_coords:
            world_coords.append((x + lx, y + ly))
        return world_coords

    def _check_collision(self, x, y, rot, p_type):
        blocks = self._get_blocks(x, y, rot, p_type)
        for bx, by in blocks:
            if bx < 0 or bx >= GRID_WIDTH:
                # print(f"DEBUG: Collision Wall x={bx}")
                return True
            if by >= TOTAL_HEIGHT:
                # print(f"DEBUG: Collision Floor y={by}")
                return True
            if by >= 0 and self.grid[by][bx] != 0:
                # print(f"DEBUG: Collision Block at ({bx}, {by})")
                return True
        return False

    def _rotate(self, direction):
        """
        direction: 1 for CW (Right), -1 for CCW (Left)
        """
        if self.piece_type == 0: return

        old_rot = self.piece_rot
        new_rot = (self.piece_rot + direction) % 4
        
        # SRS Wall Kicks
        if self.piece_type == MINO_O:
            return 
        
        table = SRS_I if self.piece_type == MINO_I else SRS_JLSTZ
        # Get kicks from table, default to basic rotation [(0,0)] if not found
        kick_tests = table.get((old_rot, new_rot), [(0, 0)])
        
        for i, (dx, dy) in enumerate(kick_tests):
            test_x = self.piece_x + dx
            test_y = self.piece_y + dy 
            
            if not self._check_collision(test_x, test_y, new_rot, self.piece_type):
                self.piece_x = test_x
                self.piece_y = test_y
                self.piece_rot = new_rot
                return True
        
        return False

    def _lock_piece(self):
        # Check T-Spin before locking
        self.is_tspin = self._check_tspin()
        
        blocks = self._get_blocks(self.piece_x, self.piece_y, self.piece_rot, self.piece_type)
        for bx, by in blocks:
             if 0 <= by < TOTAL_HEIGHT:
                 self.grid[by][bx] = self.piece_type
        
        self._check_and_start_clear()
        
        # Only spawn if NO clear happened.
        if not self.in_clear_anim:
             self._spawn_piece()
             self.hold_used = False

    def _check_and_start_clear(self):
        lines_to_clear = []
        y = TOTAL_HEIGHT - 1
        while y >= 0:
            if all(self.grid[y]):
                lines_to_clear.append(y)
            y -= 1
        
        # T-Spin Zero? (No lines cleared but T-Spin performed)
        # We can award points but animation waits for clear...
        # For simplicity, handle T-Spin Zero immediately here if no lines to clear
        if not lines_to_clear and self.is_tspin:
            self.score += 400 * (self.combo + 1) # T-Spin Zero
            # Maybe show small text effect?
            self.combo = -1
        
        if lines_to_clear:
            self.clearing_lines = lines_to_clear
            self.in_clear_anim = True
            self.clear_timer = 0
            
            # Check for Perfect Clear
            self.is_perfect_clear = True
            for r in range(TOTAL_HEIGHT):
                if r not in lines_to_clear:
                    if any(self.grid[r]):
                        self.is_perfect_clear = False
                        break
            
            # Update Score
            count = len(lines_to_clear)
            self.combo += 1
            
            # Determine if this is a "difficult" clear (Tetris or T-Spin)
            is_difficult = (count == 4) or self.is_tspin
            
            # Base Scores
            if self.is_tspin:
                # T-Spin Scoring
                tspin_scores = {1: 800, 2: 1200, 3: 1600}
                score_add = tspin_scores.get(count, 0) * (self.combo + 1)
            else:
                # Standard Scoring
                base_scores = {1: 100, 2: 300, 3: 500, 4: 800} 
                score_add = base_scores.get(count, 0) * (self.combo + 1)
            
            # Back-to-Back Bonus (only if ALREADY in B2B state)
            b2b_active = False
            if is_difficult and self.back_to_back:
                score_add = int(score_add * 1.5) # B2B multiplier
                b2b_active = True
            
            # Perfect Clear Bonus
            if self.is_perfect_clear:
                score_add += 3000
                
            self.score += score_add
            
            # Update Back-to-Back state for NEXT clear
            if is_difficult:
                self.back_to_back = True
            else:
                self.back_to_back = False
            
            # Store B2B display flag (for rendering)
            self.show_b2b = b2b_active
        else:
            if not self.is_tspin: # Combo breaks unless T-Spin Zero (some rules preserve combo on spin)
                self.combo = -1

    def _hard_drop(self):
        while not self._check_collision(self.piece_x, self.piece_y + 1, self.piece_rot, self.piece_type):
            self.piece_y += 1
        self._lock_piece()

    def _hold(self):
        if self.hold_used: return
        
        if self.hold_piece is None:
            self.hold_piece = self.piece_type
            self._spawn_piece()
        else:
            self.hold_piece, self.piece_type = self.piece_type, self.hold_piece
            self.piece_x = 3
            self.piece_y = 18
            self.piece_rot = ROT_0
        
        self.hold_used = True

    def get_ghost_y(self):
        ghost_y = self.piece_y
        while not self._check_collision(self.piece_x, ghost_y + 1, self.piece_rot, self.piece_type):
            ghost_y += 1
        return ghost_y

    def step(self, action):
        if self.game_over or self.in_clear_anim: return

        # Reset rotation flag on HORIZONTAL movement only (not soft drop)
        if action in [ACTION_LEFT, ACTION_RIGHT]:
             self.last_move_rotate = False
        
        # Action processing
        if action == ACTION_LEFT:
            if not self._check_collision(self.piece_x - 1, self.piece_y, self.piece_rot, self.piece_type):
                self.piece_x -= 1
        elif action == ACTION_RIGHT:
            if not self._check_collision(self.piece_x + 1, self.piece_y, self.piece_rot, self.piece_type):
                self.piece_x += 1
        elif action == ACTION_DOWN:
            if not self._check_collision(self.piece_x, self.piece_y + 1, self.piece_rot, self.piece_type):
                self.piece_y += 1
        elif action == ACTION_DROP:
            self._hard_drop()
            # self.last_move_rotate = False # Drop doesn't count as rotation? Actually hard drop locks immediately
        elif action == ACTION_ROTATE_R:
            if self._rotate(1):
                self.last_move_rotate = True # Mark rotation
        elif action == ACTION_ROTATE_L:
            if self._rotate(-1):
                self.last_move_rotate = True # Mark rotation
        elif action == ACTION_HOLD:
            self._hold()
            self.last_move_rotate = False # Hold resets T-spin status

    def _check_tspin(self):
        """Returns 0 (None), 1 (Mini), 2 (Normal) based on 3-corner rule."""
        if self.piece_type != MINO_T or not self.last_move_rotate:
            return 0
        
        # 3-Corner Rule
        corners = [(0,0), (2,0), (0,2), (2,2)]
        occupied = 0
        
        for dx, dy in corners:
            ck_x = self.piece_x + dx
            ck_y = self.piece_y + dy
            # Check if block exists or out of bounds (walls count as occupied for T-spin)
            if ck_x < 0 or ck_x >= GRID_WIDTH or ck_y >= TOTAL_HEIGHT:
                occupied += 1
            elif ck_y >= 0 and self.grid[ck_y][ck_x] > 0:
                occupied += 1
        
        if occupied >= 3:
            return 2 # T-Spin Normal
        return 0

# --- PYGAME RENDERER ---
def draw_block(screen, x, y, color):
    """Draws a single block with a glossy, jewel-like effect."""
    rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
    
    # 1. Base color (slightly darker for depth)
    base_color = (max(0, color[0]-40), max(0, color[1]-40), max(0, color[2]-40))
    pygame.draw.rect(screen, base_color, rect)
    
    # 2. Gradient/Bevel effect (Top-Left Light)
    # We simulate gradient by drawing smaller rects or lines
    
    # Top and Left edges (Bright Highlight)
    pygame.draw.line(screen, (min(255, color[0]+100), min(255, color[1]+100), min(255, color[2]+100)), (x, y), (x+BLOCK_SIZE-1, y), 2)
    pygame.draw.line(screen, (min(255, color[0]+100), min(255, color[1]+100), min(255, color[2]+100)), (x, y), (x, y+BLOCK_SIZE-1), 2)

    # Bottom and Right edges (Dark Shadow)
    pygame.draw.line(screen, (max(0, color[0]-80), max(0, color[1]-80), max(0, color[2]-80)), (x+BLOCK_SIZE-1, y), (x+BLOCK_SIZE-1, y+BLOCK_SIZE-1), 2)
    pygame.draw.line(screen, (max(0, color[0]-80), max(0, color[1]-80), max(0, color[2]-80)), (x, y+BLOCK_SIZE-1), (x+BLOCK_SIZE-1, y+BLOCK_SIZE-1), 2)

    # 3. Inner Face (Original Color, slightly inset)
    inner_rect = pygame.Rect(x+3, y+3, BLOCK_SIZE-6, BLOCK_SIZE-6)
    pygame.draw.rect(screen, color, inner_rect)
    
    # 4. Glossy Highlight (Top-Left of inner face) - giving it that "shiny plastic/glass" look
    # Create a small surface for alpha blending if we wanted, but simple shapes work too
    # Draw a small white-ish triangle or rect at top left
    gloss_points = [(x+3, y+3), (x+15, y+3), (x+3, y+15)]
    pygame.draw.polygon(screen, (min(255, color[0]+150), min(255, color[1]+150), min(255, color[2]+150)), gloss_points)
    
    # 5. Center Glow (subtle)
    center_rect = pygame.Rect(x+8, y+8, BLOCK_SIZE-16, BLOCK_SIZE-16)
    pygame.draw.rect(screen, (min(255, color[0]+30), min(255, color[1]+30), min(255, color[2]+30)), center_rect)

def draw_piece_preview(screen, piece_type, x, y, size=20):
    if piece_type == 0: return
    blocks = SHAPES[piece_type][ROT_0]
    
    # Calculate dimensions to center the piece
    min_x = min(b[0] for b in blocks)
    max_x = max(b[0] for b in blocks)
    min_y = min(b[1] for b in blocks)
    max_y = max(b[1] for b in blocks)
    
    w = (max_x - min_x + 1) * size
    h = (max_y - min_y + 1) * size
    
    start_x = x - w // 2 
    start_y = y - h // 2 

    for lx, ly in blocks:
        px = start_x + (lx - min_x) * size
        py = start_y + (ly - min_y) * size
        
        rect = pygame.Rect(px, py, size, size)
        color = COLORS[piece_type]
        
        # Base
        pygame.draw.rect(screen, (max(0, color[0]-40), max(0, color[1]-40), max(0, color[2]-40)), rect)
        
        # Highlights
        pygame.draw.line(screen, (min(255, color[0]+100), min(255, color[1]+100), min(255, color[2]+100)), (px, py), (px+size-1, py), 2)
        pygame.draw.line(screen, (min(255, color[0]+100), min(255, color[1]+100), min(255, color[2]+100)), (px, py), (px, py+size-1), 2)
        
        # Shadows
        pygame.draw.line(screen, (max(0, color[0]-80), max(0, color[1]-80), max(0, color[2]-80)), (px+size-1, py), (px+size-1, py+size-1), 2)
        pygame.draw.line(screen, (max(0, color[0]-80), max(0, color[1]-80), max(0, color[2]-80)), (px, py+size-1), (px+size-1, py+size-1), 2)
        
        # Inner
        inner_rect = pygame.Rect(px+2, py+2, size-4, size-4)
        pygame.draw.rect(screen, color, inner_rect)

def draw_grid(screen, game, das_val, arr_val, offset_x=0):
    # Layout Config - Puyo Tetris Style
    # Center the board, but ensure enough space for HOLD (Left)
    player_area_w = SCREEN_WIDTH // 2  # 500px per player
    board_w = GRID_WIDTH * BLOCK_SIZE  # 300px
    
    # Center board within player area
    board_x = offset_x + (player_area_w - board_w) // 2
    board_y = 50
    
    # Left Side: HOLD (closer to board)
    hold_x = board_x - 90
    
    # Right Side: NEXT
    next_x = board_x + board_w + 10
    
    # Draw Board Background/Border
    pygame.draw.rect(screen, (0, 0, 0), (board_x, board_y, board_w, GRID_HEIGHT * BLOCK_SIZE))
    pygame.draw.rect(screen, (255, 255, 255), (board_x - 4, board_y - 4, board_w + 8, GRID_HEIGHT * BLOCK_SIZE + 8), 3)

    # Draw Field
    for y in range(GRID_HEIGHT):
        real_y = y + BUFFER_HEIGHT
        is_clearing = game.in_clear_anim and (real_y in game.clearing_lines)
        
        for x in range(GRID_WIDTH):
            val = game.grid[real_y][x]
            if val > 0:
                draw_block(screen, board_x + x * BLOCK_SIZE, board_y + y * BLOCK_SIZE, COLORS[val])
                
                # Animation Effect: Sequential Flash (Left to Right)
                if is_clearing:
                    progress = game.clear_timer / game.clear_anim_duration
                    
                    # Sequential timing parameters
                    col_delay = 0.05
                    start_threshold = x * col_delay
                    flash_dur = 0.5 
                    
                    if progress >= start_threshold:
                        local_p = (progress - start_threshold) / flash_dur
                        
                        if local_p <= 1.0:
                            # 1.0 (White) -> 0.0 (Transparent)
                            intensity = 1.0 - local_p
                            alpha = int(255 * intensity)
                            
                            if alpha > 0:
                                flash_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                                flash_surf.fill((255, 255, 255, alpha))
                                screen.blit(flash_surf, (board_x + x * BLOCK_SIZE, board_y + y * BLOCK_SIZE))

            else:
                 # Subtle grid lines
                 rect = pygame.Rect(board_x + x * BLOCK_SIZE, board_y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                 pygame.draw.rect(screen, (25, 25, 35), rect, 1)



    if game.game_over:
        font = pygame.font.SysFont('Arial', 40, bold=True)
        text = font.render("GAME OVER", True, (255, 50, 50))
        text_rect = text.get_rect(center=(board_x + board_w//2, board_y + (GRID_HEIGHT * BLOCK_SIZE)//2))
        screen.blit(text, text_rect)
        return

    if not game.in_clear_anim:
        # Draw Ghost
        ghost_y = game.get_ghost_y()
        ghost_blocks = game._get_blocks(game.piece_x, ghost_y, game.piece_rot, game.piece_type)
        for bx, by in ghost_blocks:
            vis_y = by - BUFFER_HEIGHT
            if vis_y >= 0:
                rect = pygame.Rect(board_x + bx * BLOCK_SIZE, board_y + vis_y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(screen, (100, 100, 100), rect, 2)

        # Draw Current Piece
        piece_blocks = game._get_blocks(game.piece_x, game.piece_y, game.piece_rot, game.piece_type)
        for bx, by in piece_blocks:
            vis_y = by - BUFFER_HEIGHT
            if vis_y >= 0:
                 draw_block(screen, board_x + bx * BLOCK_SIZE, board_y + vis_y * BLOCK_SIZE, COLORS[game.piece_type])

    # Text Effect: "TETRIS"
    if game.in_clear_anim and len(game.clearing_lines) >= 4:
        # Puyo Tetris Style: Big Gold Text
        font_tetris = pygame.font.SysFont('Arial', 60, bold=True)
        text = "TETRIS"
        
        # Outline (Black)
        outline_surf = font_tetris.render(text, True, (0, 0, 0))
        # Fill (Gold)
        fill_surf = font_tetris.render(text, True, (255, 215, 0))
        
        # Calculate Center Y based on clearing lines
        if game.clearing_lines:
            min_line = min(game.clearing_lines)
            max_line = max(game.clearing_lines)
            center_line = (min_line + max_line) / 2
            visual_center_y = center_line - BUFFER_HEIGHT
            
            text_center_x = board_x + board_w // 2
            text_center_y = board_y + visual_center_y * BLOCK_SIZE + BLOCK_SIZE // 2
        else:
            text_center_x = board_x + board_w // 2
            text_center_y = board_y + (GRID_HEIGHT * BLOCK_SIZE) // 2
        
        # Draw outline with offset
        for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2)]:
             rect = outline_surf.get_rect(center=(text_center_x+dx, text_center_y+dy))
             screen.blit(outline_surf, rect)
             
        # Draw fill
        rect = fill_surf.get_rect(center=(text_center_x, text_center_y))
        screen.blit(fill_surf, rect)

    # Text Effect: "T-SPIN" (Side Display with Slide-in)
    if game.in_clear_anim and game.is_tspin and not game.is_perfect_clear:
         font_tsp = pygame.font.SysFont('Arial', 40, bold=True)
         
         lines = len(game.clearing_lines)
         msg = "T-SPIN"
         if lines == 1: msg = "T-SPIN SINGLE"
         elif lines == 2: msg = "T-SPIN DOUBLE"
         elif lines == 3: msg = "T-SPIN TRIPLE"
         
         # Color: Magenta/Purple
         color_tsp = (255, 0, 255)
         
         outline_surf = font_tsp.render(msg, True, (0, 0, 0))
         fill_surf = font_tsp.render(msg, True, color_tsp)
         
         # Animation: Slide in from right
         progress = game.clear_timer / game.clear_anim_duration
         
         # Slide-in phase (0.0 -> 0.2): Move from right
         # Hold phase (0.2 -> 0.8): Stay in place
         # Fade-out phase (0.8 -> 1.0): Fade away
         
         if progress < 0.2:
             slide_progress = progress / 0.2
             offset_x = int(200 * (1.0 - slide_progress))
             alpha_mult = 1.0
         elif progress < 0.8:
             offset_x = 0
             alpha_mult = 1.0
         else:
             offset_x = 0
             fade_progress = (progress - 0.8) / 0.2
             alpha_mult = 1.0 - fade_progress
         
         # Position: Right side, below NEXT
         tsp_x = next_x + 50 + offset_x
         tsp_y = board_y + 420
         
         # Apply alpha (fade)
         if alpha_mult < 1.0:
             outline_surf.set_alpha(int(255 * alpha_mult))
             fill_surf.set_alpha(int(255 * alpha_mult))

         # Outline
         for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2)]:
              rect = outline_surf.get_rect(center=(tsp_x+dx, tsp_y+dy))
              screen.blit(outline_surf, rect)
         # Fill
         rect = fill_surf.get_rect(center=(tsp_x, tsp_y))
         screen.blit(fill_surf, rect)
         
         # Back-to-Back indicator
         if game.show_b2b:
             font_b2b = pygame.font.SysFont('Arial', 20, bold=True)
             b2b_text = "BACK-TO-BACK"
             b2b_surf = font_b2b.render(b2b_text, True, (255, 255, 100)) # Yellow
             if alpha_mult < 1.0:
                 b2b_surf.set_alpha(int(255 * alpha_mult))
             b2b_rect = b2b_surf.get_rect(center=(tsp_x, tsp_y + 35))
             screen.blit(b2b_surf, b2b_rect)

    # Text Effect: "PERFECT CLEAR"
    if game.in_clear_anim and game.is_perfect_clear:
        font_pc = pygame.font.SysFont('Arial', 50, bold=True)
        text_pc = "PERFECT CLEAR!!"
        
        # Rainbow Colors? Or just bright Cyan/White
        # Let's do Cyan/White pulsating
        progress = game.clear_timer / game.clear_anim_duration
        val = int(255 * (0.5 + 0.5 * math.sin(progress * 10)))
        color_pc = (val, 255, 255) # Cyan pulsate
        
        outline_surf = font_pc.render(text_pc, True, (0, 0, 0))
        fill_surf = font_pc.render(text_pc, True, color_pc)
        
        pc_x = board_x + board_w // 2
        pc_y = board_y + (GRID_HEIGHT * BLOCK_SIZE) // 2
        
        # Outline
        for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2)]:
             rect = outline_surf.get_rect(center=(pc_x+dx, pc_y+dy))
             screen.blit(outline_surf, rect)
             
        # Fill
        rect = fill_surf.get_rect(center=(pc_x, pc_y))
        screen.blit(fill_surf, rect)

    # --- UI Section ---
    font_label = pygame.font.SysFont('Arial', 20, bold=True)
    font_score = pygame.font.SysFont('Consolas', 36, bold=True)
    font_small = pygame.font.SysFont('Consolas', 16)
    
    # HOLD (Left)
    screen.blit(font_label.render("HOLD", True, (255, 255, 255)), (hold_x + 25, board_y))
    pygame.draw.rect(screen, (0, 0, 0), (hold_x, board_y + 30, 100, 80)) 
    pygame.draw.rect(screen, (150, 150, 150), (hold_x, board_y + 30, 100, 80), 2)
    if game.hold_piece:
        draw_piece_preview(screen, game.hold_piece, hold_x + 50, board_y + 70)

    # NEXT (Right)
    screen.blit(font_label.render("NEXT", True, (255, 255, 255)), (next_x + 25, board_y))
    next_bg_h = 360
    pygame.draw.rect(screen, (0, 0, 0), (next_x, board_y + 30, 100, next_bg_h))
    pygame.draw.rect(screen, (150, 150, 150), (next_x, board_y + 30, 100, next_bg_h), 2)
    
    next_y = board_y + 70
    for p_type in game.bag[:5]:
        draw_piece_preview(screen, p_type, next_x + 50, next_y)
        next_y += 70

    # SCORE (Bottom)
    score_y = board_y + GRID_HEIGHT * BLOCK_SIZE + 20
    score_text = font_score.render(f'{game.score:07d}', True, (100, 255, 100))
    score_rect = score_text.get_rect(center=(board_x + board_w//2, score_y))
    screen.blit(score_text, score_rect)
    
    if game.combo > 0:
        combo_text = font_label.render(f'{game.combo} COMBO!', True, (255, 200, 50))
        combo_rect = combo_text.get_rect(center=(board_x + board_w//2, score_y + 40))
        screen.blit(combo_text, combo_rect)




# --- CONFIG UI ---
class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.dragging = False
        
        # Knob
        self.knob_rect = pygame.Rect(x, y - 5, 10, h + 10)
        self.update_knob()

    def update_knob(self):
        ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
        self.knob_rect.centerx = self.rect.x + self.rect.width * ratio

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.knob_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_val(event.pos[0])

    def update_val(self, mouse_x):
        rel_x = mouse_x - self.rect.x
        rel_x = max(0, min(rel_x, self.rect.width))
        ratio = rel_x / self.rect.width
        self.val = int(self.min_val + (self.max_val - self.min_val) * ratio)
        self.update_knob()

    def draw(self, screen, font):
        # Label
        label_surf = font.render(f"{self.label}: {self.val}", True, (255, 255, 255))
        screen.blit(label_surf, (self.rect.x, self.rect.y - 25))
        
        # Bar
        pygame.draw.rect(screen, (100, 100, 100), self.rect)
        pygame.draw.rect(screen, (50, 50, 50), self.rect, 2)
        
        # Knob
        pygame.draw.rect(screen, (200, 200, 255), self.knob_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.knob_rect, 2)

def draw_pause_menu(screen, sliders):
    # Overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200)) # Semi-transparent black
    screen.blit(overlay, (0, 0))
    
    # Menu Box
    menu_rect = pygame.Rect(50, 150, 400, 300)
    pygame.draw.rect(screen, (30, 30, 40), menu_rect)
    pygame.draw.rect(screen, (255, 255, 255), menu_rect, 2)
    
    font_title = pygame.font.SysFont('Arial', 32, bold=True)
    title = font_title.render("SETTINGS (PAUSED)", True, (255, 255, 255))
    screen.blit(title, (menu_rect.centerx - title.get_width()//2, menu_rect.y + 20))
    
    font_ui = pygame.font.SysFont('Arial', 24)
    for slider in sliders:
        slider.draw(screen, font_ui)
        
    instr = font_ui.render("Press ESC to Resume", True, (150, 150, 150))
    screen.blit(instr, (menu_rect.centerx - instr.get_width()//2, menu_rect.bottom - 40))

def main():
    pygame.init()
    
    # Virtual Resolution (Internal)
    VIRTUAL_W, VIRTUAL_H = SCREEN_WIDTH, SCREEN_HEIGHT
    
    # Physical Window (Resizable)
    screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H), pygame.RESIZABLE)
    virtual_screen = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    
    pygame.display.set_caption("Moca-Tris AI Environment - Dual Player")
    clock = pygame.time.Clock()
    
    # Dual Player Setup
    game1 = TetrisGame()  # Player 1 (Left)
    game2 = TetrisGame()  # Player 2 (Right)

    running = True
    paused = False # New state
    fall_time1 = 0
    fall_time2 = 0
    fall_speed = 800 

    # Input Constants (Modern Tetris Standard-ish)
    DAS = 100 
    ARR = 60 
    SDI = 50 
    ANIM_SPEED = 500 # Line Clear Animation Duration (ms)
    
    # Sliders
    das_slider = Slider(100, 250, 300, 10, 50, 300, DAS, "DAS (Delay)")
    arr_slider = Slider(100, 320, 300, 10, 0, 100, ARR, "ARR (Speed)")
    sdi_slider = Slider(100, 390, 300, 10, 0, 100, SDI, "SDI (Soft Drop)")
    anim_slider = Slider(100, 460, 300, 10, 0, 1000, ANIM_SPEED, "Anim Speed (0=OFF)")
    sliders = [das_slider, arr_slider, sdi_slider, anim_slider]

    # Input State Management - Player 1 (Arrow Keys)
    key_states_p1 = {
        pygame.K_LEFT:  {'pressed': False, 'das_timer': 0, 'arr_timer': 0},
        pygame.K_RIGHT: {'pressed': False, 'das_timer': 0, 'arr_timer': 0},
        pygame.K_DOWN:  {'pressed': False, 'das_timer': 0, 'arr_timer': 0}
    }
    
    # Input State Management - Player 2 (WASD)
    key_states_p2 = {
        pygame.K_a:  {'pressed': False, 'das_timer': 0, 'arr_timer': 0},
        pygame.K_d: {'pressed': False, 'das_timer': 0, 'arr_timer': 0},
        pygame.K_s:  {'pressed': False, 'das_timer': 0, 'arr_timer': 0}
    }

    while running:
        dt = clock.tick(FPS)
        
        # Update Game Logic (Animation) for both players
        game1.clear_anim_duration = ANIM_SPEED
        game1.update(dt)
        game2.clear_anim_duration = ANIM_SPEED
        game2.update(dt)
        
        if not paused:
            if not game1.in_clear_anim:
                fall_time1 += dt
            if not game2.in_clear_anim:
                fall_time2 += dt

        # Input Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Pass events to sliders if paused
            if paused:
                for slider in sliders:
                    slider.handle_event(event)
                # Apply values
                DAS = das_slider.val
                ARR = arr_slider.val
                SDI = sdi_slider.val
                ANIM_SPEED = anim_slider.val

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused # Toggle pause
                
                # Only process game input if NOT paused
                # Only process game input if NOT paused
                if not paused:
                    # Player 1 Controls (Arrow Keys, X, Z, Space, C)
                    if not game1.game_over:
                        if event.key == pygame.K_UP or event.key == pygame.K_x: 
                            game1.step(ACTION_ROTATE_R)
                        elif event.key == pygame.K_z: 
                            game1.step(ACTION_ROTATE_L)
                        elif event.key == pygame.K_SPACE: 
                            game1.step(ACTION_DROP)
                            fall_time1 = 0 
                        elif event.key == pygame.K_LSHIFT:
                            game1.step(ACTION_HOLD)
                        elif event.key == pygame.K_r: 
                            game1 = TetrisGame()
                            fall_time1 = 0

                        # DAS Setup for P1
                        if event.key in key_states_p1:
                            key_states_p1[event.key]['pressed'] = True
                            key_states_p1[event.key]['das_timer'] = 0
                            key_states_p1[event.key]['arr_timer'] = 0
                            if event.key == pygame.K_LEFT: game1.step(ACTION_LEFT)
                            elif event.key == pygame.K_RIGHT: game1.step(ACTION_RIGHT)
                            elif event.key == pygame.K_DOWN: game1.step(ACTION_DOWN)
                    
                    # Player 2 Controls (WASD, E, Q, F, Tab)
                    if not game2.game_over:
                        if event.key == pygame.K_w or event.key == pygame.K_e: 
                            game2.step(ACTION_ROTATE_R)
                        elif event.key == pygame.K_q: 
                            game2.step(ACTION_ROTATE_L)
                        elif event.key == pygame.K_f: 
                            game2.step(ACTION_DROP)
                            fall_time2 = 0 
                        elif event.key == pygame.K_TAB:
                            game2.step(ACTION_HOLD)

                        # DAS Setup for P2
                        if event.key in key_states_p2:
                            key_states_p2[event.key]['pressed'] = True
                            key_states_p2[event.key]['das_timer'] = 0
                            key_states_p2[event.key]['arr_timer'] = 0
                            if event.key == pygame.K_a: game2.step(ACTION_LEFT)
                            elif event.key == pygame.K_d: game2.step(ACTION_RIGHT)
                            elif event.key == pygame.K_s: game2.step(ACTION_DOWN)
            
            elif event.type == pygame.KEYUP:
                if event.key in key_states_p1:
                    key_states_p1[event.key]['pressed'] = False
                if event.key in key_states_p2:
                    key_states_p2[event.key]['pressed'] = False
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if paused:
                    for slider in sliders: slider.handle_event(event)
            elif event.type == pygame.MOUSEMOTION:
                if paused:
                    for slider in sliders: slider.handle_event(event)


        if not paused:
            # --- Continuous Input (DAS / ARR / SDI) for Player 1 ---
            if not game1.game_over:
                for key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN]:
                    if key_states_p1[key]['pressed']:
                        # Determine repeat rate
                        base_arr = SDI if key == pygame.K_DOWN else ARR
                        safe_arr = max(1, base_arr)

                        key_states_p1[key]['das_timer'] += dt
                        if key_states_p1[key]['das_timer'] >= DAS:
                            key_states_p1[key]['arr_timer'] += dt
                            if key_states_p1[key]['arr_timer'] >= safe_arr:
                                while key_states_p1[key]['arr_timer'] >= safe_arr:
                                    key_states_p1[key]['arr_timer'] -= safe_arr
                                    if key == pygame.K_LEFT: game1.step(ACTION_LEFT)
                                    elif key == pygame.K_RIGHT: game1.step(ACTION_RIGHT)
                                    elif key == pygame.K_DOWN: game1.step(ACTION_DOWN)
            
            # --- Continuous Input (DAS / ARR / SDI) for Player 2 ---
            if not game2.game_over:
                for key in [pygame.K_a, pygame.K_d, pygame.K_s]:
                    if key_states_p2[key]['pressed']:
                        # Determine repeat rate
                        base_arr = SDI if key == pygame.K_s else ARR
                        safe_arr = max(1, base_arr)

                        key_states_p2[key]['das_timer'] += dt
                        if key_states_p2[key]['das_timer'] >= DAS:
                            key_states_p2[key]['arr_timer'] += dt
                            if key_states_p2[key]['arr_timer'] >= safe_arr:
                                while key_states_p2[key]['arr_timer'] >= safe_arr:
                                    key_states_p2[key]['arr_timer'] -= safe_arr
                                    if key == pygame.K_a: game2.step(ACTION_LEFT)
                                    elif key == pygame.K_d: game2.step(ACTION_RIGHT)
                                    elif key == pygame.K_s: game2.step(ACTION_DOWN)

            # Gravity for Player 1
            if not game1.game_over:
                if fall_time1 >= fall_speed:
                    if not game1._check_collision(game1.piece_x, game1.piece_y + 1, game1.piece_rot, game1.piece_type):
                        game1.piece_y += 1
                    else:
                         game1._lock_piece()
                    fall_time1 = 0
            
            # Gravity for Player 2
            if not game2.game_over:
                if fall_time2 >= fall_speed:
                    if not game2._check_collision(game2.piece_x, game2.piece_y + 1, game2.piece_rot, game2.piece_type):
                        game2.piece_y += 1
                    else:
                         game2._lock_piece()
                    fall_time2 = 0

        # Rendering to Virtual Screen
        virtual_screen.fill((30, 30, 40)) 
        draw_grid(virtual_screen, game1, DAS, ARR, offset_x=0)      # Player 1 (Left)
        draw_grid(virtual_screen, game2, DAS, ARR, offset_x=600)    # Player 2 (Right)
        
        if paused:
            draw_pause_menu(virtual_screen, sliders)

        # Scale and Draw to Physical Screen
        # Maintain Aspect Ratio
        current_w, current_h = screen.get_size()
        scale_w = current_w / VIRTUAL_W
        scale_h = current_h / VIRTUAL_H
        scale = min(scale_w, scale_h)
        
        new_w = int(VIRTUAL_W * scale)
        new_h = int(VIRTUAL_H * scale)
        
        scaled_surf = pygame.transform.scale(virtual_screen, (new_w, new_h))
        
        # Center the scaled surface
        pad_x = (current_w - new_w) // 2
        pad_y = (current_h - new_h) // 2
        
        screen.fill((0, 0, 0)) # Fill black bars
        screen.blit(scaled_surf, (pad_x, pad_y))
        
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
