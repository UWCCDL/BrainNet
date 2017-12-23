"""
This is a container for all logic related to the block game.

This object can be made and run in the same thread.  We'll put the graphics in a separate thread and talk with it via
the graphics_queue.

"""

import random
import time
import numpy as np
import BlockGameGraphics
import StringConverter
import Constants


class BlockGameManager(object):

    def __init__(self, cell_size, num_cols, num_rows, board_height,
                 board_width, hide_piece=False, window_x_pos=-1920, window_y_pos=0, background_width=1920,
                 background_height=1080):

        self.cell_size = cell_size
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.board_height = board_height
        self.board_width = board_width
        self.hide_piece = hide_piece
        self.window_x_pos = window_x_pos
        self.window_y_pos = window_y_pos
        self.background_width = background_width
        self.background_height = background_height

        self.draw_bottom = True
        self.graphics = None
        self.board = None
        self.piece = None
        self.piece_x = 0
        self.piece_y = 0
        self.new_board()
        # create new board
        self.dictionary_text_list = []
        self.right_side = self.cell_size * self.num_cols # The width of the board
        # Create Graphics #
        self.brick_color = None
        self.background = [[0 for _ in xrange(self.num_cols)] for _ in xrange(self.num_rows)]
        # Set Board #
        self.board_x = 300
        self.board_y = 0
        self.lines_cleared = 0
        # create graphics
        self.graphics = BlockGameGraphics.BlockGameGraphics(self)
        # current bottom slots
        self.slots = []

    def drop_piece(self):
        """
        Drops the piece to the floor
        """
        while not self._drop():
            pass
        self.piece = np.zeros((self.piece_x, self.piece_y))
        self._update_graphics()

    def drop_piece_halfway(self):
        self.piece_y = int(Constants.NUM_ROWS * 0.40)
        self._update_graphics()

    def rotate_piece(self):
        """
        Rotates if we don't have a collision
        """
        new_piece = self._rotate_clockwise(self.piece)
        new_piece = self._rotate_clockwise(new_piece)
        if not BlockGameManager.check_collision(self.board, new_piece, (self.piece_x, self.piece_y)):
            self.piece = new_piece
        self._update_graphics()

    def show_bottom(self):
        self.draw_bottom = True

    def hide_bottom(self):
        self.draw_bottom = False

    def show_crosshair(self):
        """
        Display crosshair
        """
        self.graphics.show_only_crosshair()

    def show_cursor_task(self, prompt):
        """
        Display cursor task
        """
        self.graphics.hide_all()
        self.graphics.show_right_flag()
        self.graphics.show_left_flag()
        self.graphics.show_yes_flag()
        self.graphics.show_no_flag()
        self.graphics.set_text_dictionary_list({'text': prompt, 'pos': (None, 150), 'color': (255, 255, 255)})
        self.graphics.show_cursor()

    def show_block_game(self):
        self.graphics.hide_all()
        self.graphics.show_block_game()

    def flash_red(self, before_flash=2, dur=0.8):
        """
        Flashes the crosshair read for dur amount of seconds.  Graphics are automatically updated.
        """
        self.graphics.show_crosshair()
        time.sleep(before_flash)
        # Change to our flash color
        self.graphics.set_crosshairs_color(self.graphics.crosshair_cross_color_flash)
        self._update_graphics()
        time.sleep(dur)
        # Change back to our default color.
        self.graphics.set_crosshairs_color(self.graphics.crosshair_cross_color_default)
        self._update_graphics()

    def hide_all(self):
        """
        Hide all graphics and show blank
        """
        self.graphics.hide_all()
        self.graphics.set_text_dictionary_list([])

    def set_board(self, state_string):
        """
        Sets a new board state based on the given state string

        :requires State_string is of the form:
                  '\t'.join([board_str, str(board_shape_x), str(board_shape_y), str(piece_str), str(piece_shape_x),
                            str(piece__shape_y), str(piece_location_x), str(piece_location_y)])
        """
        board_str, board_shape_x, board_shape_y, piece_str, piece_shape_x, piece_shape_y, piece_location_x, \
            piece_location_y = state_string.strip().split('\t')
        old_shape = self.board.shape
        self.piece_x = int(piece_location_x)
        self.piece_y = int(piece_location_y)
        # convert board
        self.board = StringConverter.string_to_matrix(board_str, board_shape_x, board_shape_y)
        self.piece = StringConverter.string_to_matrix(piece_str, piece_shape_x, piece_shape_y)
        # board shape should not change
        assert old_shape == self.board.shape
        # update graphics
        self._update_graphics()

    def new_piece(self, upright=None):
        """
        Generates a random colored block in the "best" new place.
        
        :param upright: If None, we'll randomly select whether the piece is upright. If true, the piece will be upright
                        false, we'll make the piece upside down
        :return: True if the new block is upright, else false.
        """
        # Reset color
        self.brick_color = random.choice(range(2, len(BlockGameGraphics.BlockGameGraphics.CONSTANT_COLORS)))
        # Get new x value
        new_x = round_down(self.slots[0], 3)
        # get bottom of board
        bottom = self._get_bottom_of_sub_grid(self._back_fill(self.board[:, new_x:new_x + 3].copy()))
        # Get new asymmetrical piece
        new_piece = self._add_random_topping(self._get_complement(bottom))
        while self._check_symmetric(new_piece):
            new_piece = self._add_random_topping(self._get_complement(bottom))

        self.piece_y, i = 0, 0
        # here this defines control or experimental
        upright = random.choice([True, False]) if upright is None else upright
        if not upright:
            new_piece = self._rotate_clockwise(self._rotate_clockwise(new_piece))
        # Set current values to new ones
        self.piece = new_piece
        self.piece_x = new_x
        # Check to see if we have a game over
        if self.check_collision(self.board, self.piece, (self.piece_x, self.piece_y)):
            print "GAME ENDED!!!"
        # update
        if self.graphics is not None:
            self._update_graphics()
        return upright

    def board_to_string(self):
        """
        Returns the current board in the form:

        State_string is of the form:
            '\t'.join([board_str, str(board_shape_x), str(board_shape_y), str(piece_str), str(piece_shape_x),
                          str(piece__shape_y), str(piece_location_x), str(piece_location_y)])
        """
        self.board = np.asarray(self.board)
        self.piece = np.asarray(self.piece)
        board_shape_x, board_shape_y = self.board.shape
        piece_shape_x, piece_shape_y = np.asarray(self.piece).shape
        piece_location_x, piece_location_y = self.piece_x, self.piece_y
        board_str = str(list(self.board.ravel()))
        piece_str = str(list(self.piece.ravel()))
        return '\t'.join([board_str, str(board_shape_x), str(board_shape_y), str(piece_str), str(piece_shape_x),
                          str(piece_shape_y), str(piece_location_x), str(piece_location_y)])

    def new_board(self, control=None):
        """
        Generates and returns a new board
        """
        self.board = np.asarray([[0 for _ in xrange(self.num_cols)] for _ in xrange(self.num_rows)] + \
                [[1 for _ in xrange(self.num_cols)]])
        self._gen_bottom()
        self.new_piece(control)

    # ----------Game Logic---------- #

    def _check_symmetric(self, piece):
        """
        Returns true if this piece is equal to its 180 degree rotation.
        """
        return np.array_equal(piece, self._rotate_clockwise((self._rotate_clockwise(piece))))

    def _back_fill(self, piece):
        for j in range(piece.shape[1]):
            col = piece[:, j]
            index = smallest_index_of_nonzero(col)
            for i in range(col.shape[0]):
                if i > index:
                    piece[i, j] = self.brick_color
        return piece

    def _get_bottom_of_sub_grid(self, grid):
        bottom = np.zeros((3, 3), dtype=int)
        for i, row in enumerate(grid):
            if any(row) and not all(row):
                if self._check_valid_row_index(i - 2):
                    bottom = np.vstack([grid[i - 2], grid[i - 1], row])  # add checks
        return bottom

    def _add_random_topping(self, brick):
        if type(brick) is int:
            brick = np.asarray([[brick]])
        top_row = brick[0, :]
        new_row = []
        for x in top_row:
            if x == 0:
                new_row.append(0)
            else:
                app = 0 if random.choice([1, 0]) == 0 else self.brick_color
                new_row.append(app)
        new_row = np.asarray(new_row)
        if any(new_row):
            new_row.reshape(brick.shape[1], 1)
            brick = np.vstack((new_row, brick))
        return brick

    def _move(self, delta_x):
        new_x = self.piece_x + delta_x
        if new_x < 0:
            new_x = 0
        if new_x > self.num_cols - len(self.piece[0]):
            new_x = self.num_cols - len(self.piece[0])
        if not self.check_collision(self.board, self.piece, (new_x, self.piece_y)):
            self.piece_x = new_x

    def clear_rows(self):
        for i, row in enumerate(self.board[:-1]):
            if 0 not in row:
                self.board = self._remove_row(self.board, i)
                self.lines_cleared += 1
                return True
        return False

    def _drop(self):
        self.piece_y += 1
        if self.check_collision(self.board, self.piece, (self.piece_x, self.piece_y)):
            self.board = BlockGameManager.join_matrices(self.board, self.piece, (self.piece_x, self.piece_y))
            self.piece_x, self.piece_y = 0, 0
            return True
        return False

    @staticmethod
    def _rotate_clockwise(shape):
        """
        rotates the passed shape 90 degrees
        """
        return [[shape[y][x] for y in xrange(len(shape))] for x in xrange(len(shape[0]) - 1, -1, -1)]

    def _get_complement(self, arr):
        """
        Returns the complement of a matrix (non-zeros switched with zeros and vice versa)
        """
        comp = np.logical_not(arr).astype(int)
        for j in range(comp.shape[1]):
            col = comp[:, j]
            for i in range(col.shape[0]):
                if comp[i, j]:
                    comp[i, j] = self.brick_color
        return comp

    def _gen_bottom(self):
        """
        Generates and sets the bottom of the board to a random row.
        :return: 
        """
        # how many slots to leave on bottom row
        num_slots = random.randint(1, 3)
        # keep the indices of slots
        for row in range(self.num_rows - 1, self.num_rows - 2, -1):
            if num_slots == 1:
                self.slots = [random.randint(0, self.num_cols - 1)]
            elif num_slots == 2:
                miss_idx = random.randint(0, self.num_cols - 2)
                while miss_idx % 3 == 2:
                    miss_idx = random.randint(0, self.num_cols - 2)
                self.slots = [miss_idx, miss_idx + 1]
            else:
                miss_idx = random.randint(0, self.num_cols - 3)
                while miss_idx % 3 != 0:
                    miss_idx = random.randint(0, self.num_cols - 3)
                self.slots = [miss_idx, miss_idx + 1, miss_idx + 2]
            for col in range(0, self.num_cols):
                self.board[row, col] = 0 if col in self.slots else 1

    def _check_valid_row_index(self, index):
        """
        Check if the passed index is within the bounds of our game.
        :param index: 
        :return: 
        """
        return 0 < index <= self.num_rows

    @staticmethod
    def check_collision(board, shape, offset):
        off_x, off_y = offset
        for cy, row in enumerate(shape):
            for cx, cell in enumerate(row):
                try:
                    if cell and board[cy + off_y][cx + off_x]:
                        return True
                except IndexError:
                    return True
        return False

    def _remove_row(self, board, row):
        board = list(board)
        del board[row]
        return np.asarray([[0 for _ in xrange(self.num_cols)]] + board)

    @staticmethod
    def join_matrices(matrix_1, matrix_2, matrix2_offset):
        off_x, off_y = matrix2_offset
        for cy, row in enumerate(matrix_2):
            for cx, val in enumerate(row):
                matrix_1[cy + off_y - 1][cx + off_x] += val
        return matrix_1

    def _update_graphics(self):
        """
        Call to update the graphics onscreen.
        """
        self.graphics.update_graphics()

    # ----------Game Control---------- #
    def play_game_with_keys(self):
        """
        Lets you play the game with key commands instead of direct calls to this object.

        """
        key_actions = {
            'a': lambda: self._move(-1),
            'd': lambda: self._move(+1),
            's': lambda: self.drop_piece(),
            'w': lambda: self.rotate_piece(),
            'n': lambda: self.new_piece()
        }

        while True:
            event = raw_input('EnterEvent:')
            try:
                key_actions[event]()
            except KeyError:
                pass
            self._update_graphics()

    def __str__(self):
        """
        String representation of the board
        :return: the board string
        """
        return self.board_to_string()


def smallest_index_of_nonzero(col):
    for i, x in enumerate(col):
        if x != 0:
            return i
    return None


def round_down(num, divisor):
    return num - (num % divisor)


def main():
    """
    Runs an example that takes values from raw_input and applies those transformations to the onscreen task_description.
    This calls play_game_with_keys.  See play_game_with_keys for how to play.
    """
    # fix
    bgm = BlockGameManager(window_x_pos=1920, window_y_pos=0, background_width=1680, background_height=1050,
                           board_height=Constants.BOARD_HEIGHT, board_width=Constants.BOARD_WIDTH,
                           cell_size=Constants.CELL_SIZE, num_cols=Constants.NUM_COLS,
                           num_rows=Constants.NUM_ROWS)
    bgm.show_block_game()
    bgm.drop_piece_halfway()

if __name__ == '__main__':
    main()
