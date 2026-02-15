import random
import copy
# Avoid circular import from tetris_controller by defining actions locally
# Actions (Mirrored)
ACTION_NONE = 0
ACTION_LEFT = 1
ACTION_RIGHT = 2
ACTION_DOWN = 3 
ACTION_DROP = 4 
ACTION_ROTATE_R = 5
ACTION_ROTATE_L = 6
ACTION_HOLD = 7

# Constants
GRID_WIDTH = 10
GRID_HEIGHT = 20
TOTAL_HEIGHT = 40 

class TetrisBot:
    def __init__(self):
        pass
    def get_moves(self, game):
        return []

class RandomBot(TetrisBot):
    def get_moves(self, game):
        moves = []
        rotations = random.randint(0, 3)
        for _ in range(rotations):
            moves.append(ACTION_ROTATE_R)
        move_x = random.randint(-5, 5)
        if move_x < 0:
            for _ in range(abs(move_x)): moves.append(ACTION_LEFT)
        elif move_x > 0:
            for _ in range(move_x): moves.append(ACTION_RIGHT)
        moves.append(ACTION_DROP)
        return moves

class SmartBot(TetrisBot):
    def get_moves(self, game):
        best_score = -float('inf')
        best_moves = []
        
        # We need shapes data locally or from srs_data
        from srs_data import SHAPES
        
        piece_type = game.piece_type
        # Starting position of piece in game is usually (4, 20) or similar spawn point.
        # But we want to simulate ALL possible placements.
        
        # Try all rotations (0-3)
        for rot in range(4):
            shape = SHAPES[piece_type][rot]
            
            # Try all horizontal positions (approx -2 to 9)
            # Efficient range scanning based on piece width would be better, but fixed range is safe.
            for x in range(-2, GRID_WIDTH + 2):
                
                # Check if this X/Rot is valid at a high Y (spawn area)
                # We start simulation from Y=BUFFER_HEIGHT (20) to find drop point.
                # Actually, simply checking if we can place it anywhere in the column is enough.
                
                # Simulate Drop: Start from top valid position and go down
                start_y = 0 
                # Find the highest non-colliding Y for this X,Rot
                # If even the top is colliding, this X,Rot is invalid.
                if self._check_collision(game.grid, shape, x, start_y):
                     # Try a bit lower if spawn is blocked? usually spawn is open.
                     # If spawn is blocked, game is over anyway.
                     # Let's try searching down a bit just in case.
                     valid_start = False
                     for zy in range(start_y, start_y + 4):
                         if not self._check_collision(game.grid, shape, x, zy):
                             start_y = zy
                             valid_start = True
                             break
                     if not valid_start:
                         continue

                # Drop until collision
                y = start_y
                while not self._check_collision(game.grid, shape, x, y + 1):
                    y += 1
                
                # 'y' is now the placement height.
                
                # Evaluate this final state
                score = self._evaluate_board(game.grid, shape, x, y)
                
                if score > best_score:
                    best_score = score
                    # Reconstruct moves from CURRENT game state to target (x, rot)
                    # Note: Pathfinding is complex (SRS kicks). 
                    # We assume simplified movement: Rotate -> Move X -> Drop
                    best_moves = []
                    
                    # 1. Rotations
                    # We assume we can rotate freely at start.
                    current_rot = game.piece_rot
                    dr = (rot - current_rot) % 4
                    if dr == 1: best_moves.append(ACTION_ROTATE_R)
                    elif dr == 2: best_moves.extend([ACTION_ROTATE_R, ACTION_ROTATE_R])
                    elif dr == 3: best_moves.append(ACTION_ROTATE_L)
                    
                    # 2. Horizontal Move
                    dx = x - game.piece_x
                    if dx < 0:
                        for _ in range(abs(dx)): best_moves.append(ACTION_LEFT)
                    elif dx > 0:
                        for _ in range(dx): best_moves.append(ACTION_RIGHT)
                    
                    # 3. Hard Drop
                    best_moves.append(ACTION_DROP)
        
        return best_moves

    def _check_collision(self, grid, shape, x, y):
        for bx, by in shape:
            abs_x = x + bx
            abs_y = y + by
            
            # Check Boundaries
            if abs_x < 0 or abs_x >= GRID_WIDTH:
                return True
            if abs_y >= TOTAL_HEIGHT:
                return True
            if abs_y < 0: 
                continue # Above grid is fine
                
            # Check Grid
            if grid[abs_y][abs_x] != 0:
                return True
        return False

    def _evaluate_board(self, grid, shape, x, y):
        # Create a temporary lightweight grid representation to place piece
        # We only need to copy the relevant rows or use a set of filled blocks?
        # Full copy for simplicity (20x10 is small).
        # Optimization: Use 1D array or bitboard if slow.
        
        # Place the piece
        # We need to calculate features without full copy if possible?
        # But 'holes' calculation needs full grid structure.
        
        # Let's modify a copy of the grid.
        temp_grid = [row[:] for row in grid]
        placed_blocks = []
        for bx, by in shape:
            abs_x = x + bx
            abs_y = y + by
            if 0 <= abs_y < TOTAL_HEIGHT and 0 <= abs_x < GRID_WIDTH:
                temp_grid[abs_y][abs_x] = 2 # Mark as placed
                placed_blocks.append((abs_x, abs_y))
        
        # --- Heuristics ---
        
        # 1. Completed Lines
        cleared = 0
        # Only check rows we touched
        affected_rows = set(py for px, py in placed_blocks)
        for r in affected_rows:
            if all(c != 0 for c in temp_grid[r]):
                cleared += 1
                
        # 2. Aggregate Height & Bumpiness & Holes
        heights = [0] * GRID_WIDTH
        holes = 0
        bumpiness = 0
        
        for c in range(GRID_WIDTH):
            col_height = 0
            found_top = False
            for r in range(TOTAL_HEIGHT):
                if temp_grid[r][c] != 0:
                    if not found_top:
                        col_height = TOTAL_HEIGHT - r
                        found_top = True
                    # If we found top, any 0 below it is a hole
                elif found_top:
                    holes += 1
            heights[c] = col_height
            
        total_height = sum(heights)
        max_height = max(heights)
        
        for c in range(GRID_WIDTH - 1):
            bumpiness += abs(heights[c] - heights[c+1])
            
        # Weights (Tuned for standard AI)
        w_lines = 1000
        w_height = -5
        w_holes = -50 # Holes are very bad
        w_bumpiness = -5
        w_max_height = -5 # Panic when high
        
        score = (cleared * w_lines) + \
                (total_height * w_height) + \
                (holes * w_holes) + \
                (bumpiness * w_bumpiness) + \
                (max_height * w_max_height)
                
        return score
