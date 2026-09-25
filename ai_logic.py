import random

from srs_data import SHAPES

# Version: 2.0 (Visible NEXT beam search)
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
        return moves, None # Random has no specific target really

class SmartBot(TetrisBot):
    def __init__(self, visible_next_count=5, beam_width=10):
        self.visible_next_count = visible_next_count
        self.beam_width = beam_width

    def get_moves(self, game):
        """
        Analyze the game state and return moves + target info.
        :param game: The TetrisGame object
        :return: (List of actions, Target Info or None)
        Target Info is (target_x, target_y, target_rot)
        """
        visible_queue = [game.piece_type] + list(game.bag[:self.visible_next_count])
        states = [{
            'grid': [row[:] for row in game.grid],
            'score': 0.0,
            'first_moves': [],
            'first_target': None,
        }]

        for depth, piece_type in enumerate(visible_queue):
            next_states = []
            for state in states:
                placements = self._generate_placements(state['grid'], piece_type)
                for placement in placements:
                    candidate = {
                        'grid': placement['grid'],
                        'score': state['score'] + self._score_position(placement, depth),
                        'first_moves': state['first_moves'],
                        'first_target': state['first_target'],
                    }

                    if depth == 0:
                        candidate['first_moves'] = self._build_move_sequence(
                            game.piece_x,
                            game.piece_rot,
                            placement['x'],
                            placement['rot'],
                        )
                        candidate['first_target'] = (placement['x'], placement['y'], placement['rot'])

                    next_states.append(candidate)

            if not next_states:
                return [ACTION_DROP], None

            next_states.sort(key=lambda state: state['score'], reverse=True)
            states = next_states[:self.beam_width]

        best_state = states[0]
        if not best_state['first_moves']:
            return [ACTION_DROP], best_state['first_target']
        return best_state['first_moves'], best_state['first_target']

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

    def _generate_placements(self, grid, piece_type):
        placements = []
        for rot in range(4):
            shape = SHAPES[piece_type][rot]
            min_x = min(block_x for block_x, _ in shape)
            max_x = max(block_x for block_x, _ in shape)

            for x in range(-min_x, GRID_WIDTH - max_x):
                y = self._find_drop_y(grid, shape, x)
                if y is None:
                    continue

                grid_after, lines_cleared = self._place_and_clear(grid, shape, x, y)
                placements.append({
                    'grid': grid_after,
                    'lines_cleared': lines_cleared,
                    'x': x,
                    'y': y,
                    'rot': rot,
                })
        return placements

    def _find_drop_y(self, grid, shape, x):
        start_y = None
        for y in range(-4, 5):
            if not self._check_collision(grid, shape, x, y):
                start_y = y
                break

        if start_y is None:
            return None

        y = start_y
        while not self._check_collision(grid, shape, x, y + 1):
            y += 1
        return y

    def _place_and_clear(self, grid, shape, x, y):
        temp_grid = [row[:] for row in grid]
        for bx, by in shape:
            abs_x = x + bx
            abs_y = y + by
            if 0 <= abs_y < TOTAL_HEIGHT and 0 <= abs_x < GRID_WIDTH:
                temp_grid[abs_y][abs_x] = 2

        full_rows = [row_index for row_index, row in enumerate(temp_grid) if all(cell != 0 for cell in row)]
        if full_rows:
            temp_grid = [row for row_index, row in enumerate(temp_grid) if row_index not in full_rows]
            for _ in full_rows:
                temp_grid.insert(0, [0] * GRID_WIDTH)

        return temp_grid, len(full_rows)

    def _score_position(self, placement, depth):
        heights = self._get_column_heights(placement['grid'])
        total_height = sum(heights)
        max_height = max(heights)
        holes = self._count_holes(placement['grid'])
        bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(GRID_WIDTH - 1))
        well_depth = self._get_right_well_depth(heights)
        line_transitions = self._count_row_transitions(placement['grid'])

        immediate_score = (
            placement['lines_cleared'] * 900
            - total_height * 35
            - holes * 260
            - bumpiness * 18
            - max_height * 12
            - line_transitions * 8
            + well_depth * 25
        )

        return immediate_score * (0.92 ** depth)

    def _get_column_heights(self, grid):
        heights = [0] * GRID_WIDTH
        for column in range(GRID_WIDTH):
            for row in range(TOTAL_HEIGHT):
                if grid[row][column] != 0:
                    heights[column] = TOTAL_HEIGHT - row
                    break
        return heights

    def _count_holes(self, grid):
        holes = 0
        for column in range(GRID_WIDTH):
            seen_block = False
            for row in range(TOTAL_HEIGHT):
                if grid[row][column] != 0:
                    seen_block = True
                elif seen_block:
                    holes += 1
        return holes

    def _count_row_transitions(self, grid):
        transitions = 0
        for row in grid:
            prev_filled = True
            for cell in row:
                filled = cell != 0
                if filled != prev_filled:
                    transitions += 1
                prev_filled = filled
            if not prev_filled:
                transitions += 1
        return transitions

    def _get_right_well_depth(self, heights):
        if len(heights) < 2:
            return 0
        return max(0, heights[-2] - heights[-1])

    def _build_move_sequence(self, current_x, current_rot, target_x, target_rot):
        moves = []

        rotation_delta = (target_rot - current_rot) % 4
        if rotation_delta == 1:
            moves.append(ACTION_ROTATE_R)
        elif rotation_delta == 2:
            moves.extend([ACTION_ROTATE_R, ACTION_ROTATE_R])
        elif rotation_delta == 3:
            moves.append(ACTION_ROTATE_L)

        dx = target_x - current_x
        if dx < 0:
            moves.extend([ACTION_LEFT] * abs(dx))
        elif dx > 0:
            moves.extend([ACTION_RIGHT] * dx)

        moves.append(ACTION_DROP)
        return moves
