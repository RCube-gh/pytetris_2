# Moca-Tris: AI Tetris Environment

**Of the AI, by the AI, for the AI.**

A complete, guideline-compliant Tetris implementation built entirely by AI, designed as a training and testing environment for AI agents. This project demonstrates modern Tetris mechanics with full SRS (Super Rotation System) support, advanced scoring, and visual feedback systems.

## 🎮 Features

### Core Mechanics
- **SRS Rotation System**: Full Super Rotation System with wall kicks (I-piece and JLSTZ-piece kick tables)
- **7-Bag Randomizer**: Fair piece distribution using the modern 7-bag algorithm
- **Hold System**: Store and swap pieces with standard hold mechanics
- **Ghost Piece**: Visual preview of landing position
- **Hard Drop & Soft Drop**: Instant placement and accelerated falling

### Advanced Gameplay
- **T-Spin Detection**: 3-corner rule implementation for T-Spin recognition
  - T-Spin Single/Double/Triple scoring
  - Visual feedback with side-panel display
- **Back-to-Back (B2B)**: Bonus scoring for consecutive difficult clears (Tetris/T-Spin)
- **Combo System**: Multiplier for consecutive line clears
- **Perfect Clear Detection**: Special scoring and visual effects for all-clear boards

### Visual Effects
- **Line Clear Animation**: Smooth left-to-right flash effect
- **Text Displays**:
  - "TETRIS" - Gold text for 4-line clears (center screen)
  - "T-SPIN DOUBLE/TRIPLE" - Purple text with slide-in animation (side panel)
  - "BACK-TO-BACK" - Yellow indicator for B2B chains
  - "PERFECT CLEAR!!" - Cyan pulsating text for all-clears
- **Ghost Piece**: Semi-transparent preview of drop position

### Input System
- **DAS (Delayed Auto Shift)**: Configurable horizontal movement delay
- **ARR (Auto Repeat Rate)**: Configurable horizontal movement speed
- **SDI (Soft Drop Interval)**: Configurable soft drop speed
- **Real-time Adjustment**: Pause menu with sliders for all timing parameters

### AI-Ready Design
- **Simple API**: `TetrisGame` class with clean `step(action)` interface
- **State Access**: Full grid state, piece information, and scoring available
- **Headless Mode Ready**: Rendering separated from game logic
- **Observation Space**: Easy integration with RL frameworks (Gym/Gymnasium compatible)

## 🚀 Installation

### Requirements
- Python 3.8+
- Pygame 2.0+

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd tetris_ai

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install pygame
```

## 🎯 Usage

### Playing the Game
```bash
python tetris.py
```

### Controls
- **Left/Right Arrow**: Move piece horizontally
- **Down Arrow**: Soft drop
- **Space**: Hard drop
- **X / Up Arrow**: Rotate clockwise
- **Z**: Rotate counter-clockwise
- **C / Shift**: Hold piece
- **R**: Restart game
- **ESC**: Pause / Settings menu

### Settings (Pause Menu)
- **DAS**: Delay before auto-repeat starts (10-300ms)
- **ARR**: Auto-repeat rate (0-100ms)
- **SDI**: Soft drop interval (0-100ms)
- **Anim Speed**: Line clear animation duration (0-1000ms, 0=instant)

## 🤖 AI Development

### Basic Usage
```python
from tetris import TetrisGame, ACTION_LEFT, ACTION_RIGHT, ACTION_DROP, ACTION_ROTATE_R

# Initialize game
game = TetrisGame()

# Game loop
while not game.game_over:
    # Get current state
    grid = game.grid
    current_piece = game.piece_type
    
    # Choose action (your AI logic here)
    action = choose_action(grid, current_piece)
    
    # Execute action
    game.step(action)
    
    # Update gravity (call periodically)
    if should_fall():
        game.step(ACTION_DOWN)
```

### Available Actions
```python
ACTION_LEFT = 0      # Move left
ACTION_RIGHT = 1     # Move right
ACTION_DOWN = 2      # Soft drop
ACTION_DROP = 4      # Hard drop
ACTION_ROTATE_R = 5  # Rotate clockwise
ACTION_ROTATE_L = 6  # Rotate counter-clockwise
ACTION_HOLD = 7      # Hold piece
```

### State Information
- `game.grid`: 20x10 board state (0=empty, 1-7=piece colors)
- `game.piece_type`: Current piece (1-7)
- `game.piece_x, game.piece_y, game.piece_rot`: Current piece position
- `game.next_pieces`: Upcoming pieces queue
- `game.hold_piece`: Held piece (or None)
- `game.score`: Current score
- `game.combo`: Current combo count
- `game.back_to_back`: B2B chain active

## 📊 Scoring System

### Base Scores (per combo level)
- Single: 100
- Double: 300
- Triple: 500
- Tetris: 800

### T-Spin Scores
- T-Spin Single: 800
- T-Spin Double: 1200
- T-Spin Triple: 1600

### Bonuses
- **Combo Multiplier**: Score × (combo + 1)
- **Back-to-Back**: 1.5× multiplier for consecutive Tetris/T-Spin clears
- **Perfect Clear**: +3000 points

## 🏗️ Project Structure

```
tetris_ai/
├── tetris.py          # Main game implementation
├── srs_data.py        # SRS rotation kick tables
├── example.py         # AI agent example (placeholder)
└── README.md          # This file
```

## 🎨 Design Philosophy

This Tetris implementation prioritizes:
1. **Guideline Compliance**: Follows modern Tetris guidelines (SRS, 7-bag, etc.)
2. **AI-First Design**: Clean API for agent development
3. **Visual Feedback**: Rich feedback for understanding game state
4. **Configurability**: Adjustable timing for different playstyles/training scenarios
5. **Code Quality**: Clean, readable, well-documented code

## 🤝 Contributing

This project was created entirely by AI (Moca) as a demonstration of AI-assisted development. Contributions, suggestions, and AI agent implementations are welcome!

## 📝 License

MIT License - Feel free to use this for AI research, game development, or learning purposes.

## 🙏 Acknowledgments

- Built with love by Moca (AI Assistant) 💜
- Designed for AI agents to learn and master Tetris
- Inspired by modern Tetris guidelines and competitive play

---

**"The perfect playground for AI to learn, compete, and evolve."** 🤖✨
