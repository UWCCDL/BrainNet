import CCDLUtil.Utility.AssertVal as Assert

"""
This file contains all constants used in BrainNet
"""

"""
Block Game Related
"""
NUM_ROUNDS = 2

"""
Graphics Related
"""
# the radius of the ball cursor
CURSOR_RADIUS = 60
# window position and size
CURSOR_TASK_X = 0
CURSOR_TASK_SIZE = (1920, 1080)
# the distance of steps taken in the task
STEP = 50
# results
STOP_EARLY = 'stop_early'
STOP_LATE = 'stop_late'
YES = 'yes'
NO = 'no'
# some constants
CELL_SIZE = 100  # Size of the cells
NUM_COLS = 12   # Number of columns for Tetris pieces on the board (Affects Size)
NUM_ROWS = 10   # Number of rows for Tetris pieces in the board
BOARD_WIDTH = CELL_SIZE * NUM_COLS
BOARD_HEIGHT = CELL_SIZE * NUM_ROWS
# We want our number of columns to be divisible by 3
Assert.assert_equal(NUM_COLS % 3, 0)

"""
SSVEP Related
"""
EEG_COLLECT_TIME_SECONDS = 15
WINDOW_SIZE_SECONDS = 2
RECEIVER_Q = 'Did you see a phosphene?'
SENDER_Q = 'Should the piece be turned?'

"""
Communication Related
"""
PORT = 9999
# Guthrie
C0_IP_Address = '128.95.226.122'
C1_IP_ADDRESS = '128.95.226.134'
C2_IP_ADDRESS = '128.95.226.196'

# Just an upper limit, will stop when server exhausts its list
NUM_EXP_TRIALS = 20
NUM_CONTROL_TRIALS = 10

FLASH_RED_DUR = 0.2
SLEEP_AFTER_FLASH = 0.4
SLEEP_BETWEEN_FIRINGS = 8  # Need 8 seconds, takes 1.5 seconds to charge.
SLEEP_AFTER_SHOWING_BLOCK_GAME_TO_C0 = 3.5
SLEEP_AFTER_SHOWING_BLOCK_GAME_TO_CX = 10
SLEEP_AFTER_SHOWING_CX_FEEDBACK = 3
SLEEP_AFTER_TMS_FIRE_TWICE = 5


""" Computer TYPE """
C0 = 'C0'
C1 = 'C1'
C2 = 'C2'

EXPERIMENTAL_STR = 'Experimental'
CONTROL_STR = 'Control'

FALSE_TRIAL = [1, 2, 4, 5, 6, 9, 10, 12, 13, 14]