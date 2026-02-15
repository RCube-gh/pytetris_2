# SRS (Super Rotation System) Data & Definitions
# This file contains the complete offset data for modern Tetris rotation rules.

# Mino Type IDs
MINO_I = 1
MINO_J = 2
MINO_L = 3
MINO_O = 4
MINO_S = 5
MINO_T = 6
MINO_Z = 7

# Rotation States (0=North, 1=East, 2=South, 3=West)
ROT_0 = 0
ROT_R = 1
ROT_2 = 2
ROT_L = 3

# Colors (R, G, B)
COLORS = {
    0: (0, 0, 0),       # Empty
    MINO_I: (0, 255, 255), # Cyan
    MINO_J: (0, 0, 255),   # Blue
    MINO_L: (255, 165, 0), # Orange
    MINO_O: (255, 255, 0), # Yellow
    MINO_S: (0, 255, 0),   # Green
    MINO_T: (128, 0, 128), # Purple
    MINO_Z: (255, 0, 0),   # Red
    8: (100, 100, 100) # Wall / Ghost
}

# Initial Shapes (Defined in a 4x4 grid concept, though usually 3x3 for non-I/O)
# We treat the pivot as the center of the local grid.
SHAPES = {
    MINO_I: [
        [(0, 1), (1, 1), (2, 1), (3, 1)], # ROT_0
        [(2, 0), (2, 1), (2, 2), (2, 3)], # ROT_R
        [(0, 2), (1, 2), (2, 2), (3, 2)], # ROT_2
        [(1, 0), (1, 1), (1, 2), (1, 3)]  # ROT_L
    ],
    MINO_J: [
        [(0, 0), (0, 1), (1, 1), (2, 1)], # ROT_0
        [(1, 0), (2, 0), (1, 1), (1, 2)], # ROT_R
        [(0, 1), (1, 1), (2, 1), (2, 2)], # ROT_2
        [(1, 0), (1, 1), (0, 2), (1, 2)]  # ROT_L
    ],
    MINO_L: [
        [(2, 0), (0, 1), (1, 1), (2, 1)], # ROT_0
        [(1, 0), (1, 1), (1, 2), (2, 2)], # ROT_R
        [(0, 1), (1, 1), (2, 1), (0, 2)], # ROT_2
        [(0, 0), (1, 0), (1, 1), (1, 2)]  # ROT_L
    ],
    MINO_O: [
        [(1, 0), (2, 0), (1, 1), (2, 1)], # ROT_0 (O doesn't really rotate but for consistency)
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)]
    ],
    MINO_S: [
        [(1, 0), (2, 0), (0, 1), (1, 1)], # ROT_0
        [(1, 0), (1, 1), (2, 1), (2, 2)], # ROT_R
        [(1, 1), (2, 1), (0, 2), (1, 2)], # ROT_2
        [(0, 0), (0, 1), (1, 1), (1, 2)]  # ROT_L
    ],
    MINO_T: [
        [(1, 0), (0, 1), (1, 1), (2, 1)], # ROT_0
        [(1, 0), (1, 1), (2, 1), (1, 2)], # ROT_R
        [(0, 1), (1, 1), (2, 1), (1, 2)], # ROT_2
        [(1, 0), (0, 1), (1, 1), (1, 2)]  # ROT_L
    ],
    MINO_Z: [
        [(0, 0), (1, 0), (1, 1), (2, 1)], # ROT_0
        [(2, 0), (1, 1), (2, 1), (1, 2)], # ROT_R
        [(0, 1), (1, 1), (1, 2), (2, 2)], # ROT_2
        [(1, 0), (0, 1), (1, 1), (0, 2)]  # ROT_L
    ]
}

# --- THE SRS KICK TABLES ---
# Format: (x_offset, y_offset). Y is usually -1 for UP (in standard math), 
# but in grid coordinates, -1 y is "up" (lower index).
# IMPORTANT: Modern Tetris uses y-up for kick calculations usually, but grid is y-down.
# Here we define offsets as (dx, dy) where +dy is DOWN (increasing row index), +dx is RIGHT.
# Standard SRS documentation often uses Y-up. We must be careful.
# Below are standard SRS wall kick data adapted for Y-down grid (dy = -srs_y)

# Wall Kicks for J, L, S, T, Z
# Test 1 is always (0,0). Tests 2-5 are the kicks.
SRS_JLSTZ = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)], # 0->R
    (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],   # R->0
    (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],   # R->2
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)], # 2->R
    (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],    # 2->L
    (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],# L->2
    (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],# L->0
    (0, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)]     # 0->L
}

# Wall Kicks for I (The long bar is special)
SRS_I = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],  # 0->R
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],  # R->0
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],  # R->2
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],  # 2->R
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],  # 2->L
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],  # L->2
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],  # L->0
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)]   # 0->L
}

# O piece does not kick.
