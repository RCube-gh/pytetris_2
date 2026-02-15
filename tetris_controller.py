import pygame
import random
from ai_logic import RandomBot, SmartBot # Import both

# Actions (Mirrored from tetris.py to avoid circular import)
ACTION_NONE = 0
ACTION_LEFT = 1
ACTION_RIGHT = 2
ACTION_DOWN = 3 # Soft drop
ACTION_DROP = 4 # Hard drop
ACTION_ROTATE_R = 5
ACTION_ROTATE_L = 6
ACTION_HOLD = 7

class TetrisController:
    """
    Base class for any controller (Human or AI).
    Controls a specific TetrisGame instance.
    """
    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        """
        Process single input events (like key presses).
        Mainly for Human controllers.
        """
        pass

    def update(self, dt):
        """
        Called every frame.
        Used for continuous input (DAS/ARR) or AI thinking.
        """
        pass

class HumanController(TetrisController):
    """
    Controls the game via Keyboard input.
    Handles DAS (Delayed Auto Shift) and ARR (Auto Repeat Rate).
    """
    def __init__(self, game, key_map, das_ms, arr_ms, sdi_ms):
        super().__init__(game)
        self.key_map = key_map 
        # key_map example:
        # {
        #   'LEFT': pygame.K_LEFT,
        #   'RIGHT': pygame.K_RIGHT,
        #   'DOWN': pygame.K_DOWN,
        #   'DROP': pygame.K_SPACE,
        #   'ROT_R': pygame.K_UP,
        #   'ROT_L': pygame.K_z,
        #   'HOLD': pygame.K_LSHIFT
        # }
        
        # Tuning
        # Note: These references allow dynamic tuning via sliders if we pass the improved values
        self.das_ms = das_ms
        self.arr_ms = arr_ms
        self.sdi_ms = sdi_ms
        
        # State
        self.key_states = {
            'LEFT':  {'pressed': False, 'das_timer': 0, 'arr_timer': 0},
            'RIGHT': {'pressed': False, 'das_timer': 0, 'arr_timer': 0},
            'DOWN':  {'pressed': False, 'das_timer': 0, 'arr_timer': 0}
        }

    def update_settings(self, das, arr, sdi):
        """Update handling speeds dynamically"""
        self.das_ms = das
        self.arr_ms = arr
        self.sdi_ms = sdi

    def handle_event(self, event):
        if self.game.game_over:
            # Special case: Restart
            if event.type == pygame.KEYDOWN and event.key == self.key_map.get('RESTART', pygame.K_r):
                 # We cannot re-init the game object here easily without reference assignment, 
                 # but for now let's assume the main loop handles restart or we add a reset method to TetrisGame.
                 # Actually, tetris.py re-creates TetrisGame(). 
                 # We might need a 'reset' method in TetrisGame later.
                 pass
            return

        if event.type == pygame.KEYDOWN:
            # Discrete Actions
            if event.key == self.key_map['ROT_R']:
                self.game.step(ACTION_ROTATE_R)
            elif event.key == self.key_map['ROT_L']:
                self.game.step(ACTION_ROTATE_L)
            elif event.key == self.key_map['DROP']:
                self.game.step(ACTION_DROP)
                # Note: fall_time reset is handled in main loop currently, 
                # but ideally the game itself should handle gravity reset on drop.
                # For now, we will rely on the game state.
            elif event.key == self.key_map['HOLD']:
                self.game.step(ACTION_HOLD)
            
            # Continuous Input Setup
            for action_name, key_code in [('LEFT', self.key_map['LEFT']), ('RIGHT', self.key_map['RIGHT']), ('DOWN', self.key_map['DOWN'])]:
                if event.key == key_code:
                    state = self.key_states[action_name]
                    state['pressed'] = True
                    state['das_timer'] = 0
                    state['arr_timer'] = 0
                    
                    # Initial Tap
                    if action_name == 'LEFT': self.game.step(ACTION_LEFT)
                    elif action_name == 'RIGHT': self.game.step(ACTION_RIGHT)
                    elif action_name == 'DOWN': self.game.step(ACTION_DOWN)

        elif event.type == pygame.KEYUP:
            for action_name, key_code in [('LEFT', self.key_map['LEFT']), ('RIGHT', self.key_map['RIGHT']), ('DOWN', self.key_map['DOWN'])]:
                if event.key == key_code:
                    self.key_states[action_name]['pressed'] = False

    def update(self, dt):
        if self.game.game_over:
            return

        # Handle DAS / ARR
        for action_name in ['LEFT', 'RIGHT', 'DOWN']:
            state = self.key_states[action_name]
            if state['pressed']:
                # Determine repeat rate
                base_arr = self.sdi_ms if action_name == 'DOWN' else self.arr_ms
                safe_arr = max(1, base_arr)

                state['das_timer'] += dt
                if state['das_timer'] >= self.das_ms:
                    state['arr_timer'] += dt
                    if state['arr_timer'] >= safe_arr:
                        while state['arr_timer'] >= safe_arr:
                            state['arr_timer'] -= safe_arr
                            
                            # Execute
                            if action_name == 'LEFT': self.game.step(ACTION_LEFT)
                            elif action_name == 'RIGHT': self.game.step(ACTION_RIGHT)
                            elif action_name == 'DOWN': self.game.step(ACTION_DOWN)

class AIController(TetrisController):
    """
    Controls the game via AI Logic.
    """
    def __init__(self, game):
        super().__init__(game)
        self.move_queue = [] # List of actions to execute
        self.timer = 0
        self.action_delay = 50 # Make it faster! (Original 150)
        self.bot = SmartBot() # Use SmartBot!

    def update_speed(self, delay_ms):
        """Update the delay between AI actions."""
        self.action_delay = delay_ms

    def update(self, dt):
        if self.game.game_over:
            return

        self.timer += dt
        if self.timer >= self.action_delay:
            self.timer = 0
            
            # If no moves left, ask the bot for a plan!
            if not self.move_queue:
                self.move_queue = self.bot.get_moves(self.game)

            # Execute next move
            if self.move_queue:
                action = self.move_queue.pop(0)
                self.game.step(action)
