"""

This module is for displaying graphics for a cursor task_description.  This also has functionality for a crosshair.

This module is NOT intended to be called by the client.  Use the BlockGameManager.  This communicates via a queue to this
module.

For now, uses the same color for the cursor task_description as the block game. If different functionality is wanted,
this script will need to be modified.

"""
import pygame
import CCDLUtil.Graphics.CursorTask.CursorTask as CursorTask
from CCDLUtil.Graphics.Util.Decorator import put_call_to_queue

class BlockGameGraphics(CursorTask.CursorTask):

    # Constants -- we'll prefix them with the term "Constant" to distinguish them
    # from messages that can be sent to the graphics queue.
    CONSTANT_FPS = 20
    BORDER_COLOR = (47, 79, 79)  # Gray
    CONSTANT_COLORS = [(0, 0, 0),  # Black
                       (51, 153, 51),  # Green
                       (204, 51, 255),  # Purple
                       (255, 153, 0),  # Orange
                       (255, 0, 0),  # Blue
                       (255, 255, 0),  # Yellow
                       (0, 0, 255),  # Red
                       (255, 0, 255),  # Cyan
                       ]

    CONSTANT_COLOR_DICT = {'red': (255, 0, 0), 'white': (255, 255, 255)}

    CONSTANT_CROSSHAIR_BKGRND_COLOR = (155, 155, 155)  # Grey
    CONSTANT_BLOCK_GAME_BACKGROUND = (0, 0, 0)  # Black.
    CONSTANT_CROSSHAIR_SIZE = 60

    def __init__(self, bgm):
        """
        :type bgm: BlockGameManager
        :param bgm: 
        """
        super(BlockGameGraphics, self).__init__(screen_size_height=bgm.background_height, screen_size_width=bgm.background_width, window_x_pos=bgm.window_x_pos,
                                                window_y_pos=bgm.window_y_pos, text_dictionary_list=bgm.dictionary_text_list)

        self.bgm = bgm

        # Flags to keep track of object state
        self.draw_block_game_flag = False

        # Location of upper left side of the board (not the screen, but the actual playing board) in pixels (x-y coords)
        self.BOARD_X = bgm.background_width // 2 - bgm.board_width // 2
        self.BOARD_Y = bgm.background_height - bgm.board_height

    @put_call_to_queue
    def display_message_multiline(self, msg, top_left):
        """
        Displays a message (msg) to screen at the top_left position
        :param msg: The string message
        :param top_left: (x, y) top left location -- relative to screen (not the board)
        :return: None - displays to screen
        """
        x, y = top_left
        for line in msg.splitlines():
            self.screen.blit(self.font.render(line, False, (255, 255, 255), (0, 0, 0)), (x, y))
            y += 14

    @put_call_to_queue
    def hide_all(self):
        """
        Hides all, making the screen blank
        """
        super(BlockGameGraphics, self).hide_all()
        self.hide_block_game()
        self.set_text_dictionary_list([])

    @put_call_to_queue
    def show_block_game(self):
        """
        Shows our block game
        """
        self.draw_block_game_flag = True

    @put_call_to_queue
    def hide_block_game(self):
        """
        Hide block game
        """
        self.draw_block_game_flag = False

    @put_call_to_queue
    def show_only_block_game(self):
        """
        Shows our block game, but hides everything else, changing our background to our cursor background.
        """
        self.hide_all()
        self.show_block_game()

    @put_call_to_queue
    def show_only_crosshair(self):
        """
        Shows only the crosshair, hiding everything else
        """
        self.hide_all()
        self.show_crosshair()

    @put_call_to_queue
    def update_graphics(self):
        # need this call to prevent freezing (win 10)
        pygame.event.clear()
        self._clear_events()

    # ----------private methods---------- #
    def _draw_shapes(self):
        """
        Takes care of drawing all onscreen objects.
        """
        # if self.draw_crosshair_flag:
        super(BlockGameGraphics, self)._draw_shapes()
        # draw the block game if needed.
        if self.draw_block_game_flag:
            self._sketch_block_game()

    def _sketch_block_game(self):
        """
        Draws our board, piece and background (ie the block game).
        """
        self.screen.fill((0, 0, 0))
        # self.draw_matrix(self.background, (0, 0))
        line_thickness = 3
        pygame.draw.line(self.screen,
                         (255, 255, 255),
                         (self.bgm.right_side + line_thickness + self.BOARD_X, self.BOARD_Y),
                         (self.bgm.right_side + line_thickness + self.BOARD_X, self.bgm.background_height - line_thickness), 3)
        pygame.draw.line(self.screen,
                         (255, 255, 255),
                         (self.BOARD_X - line_thickness, self.BOARD_Y),
                         (self.BOARD_X - line_thickness, self.bgm.background_height - line_thickness), 3)

        color = (255, 0, 0)
        x, y = (self.bgm.right_side + self.BOARD_X + self.bgm.background_width) / 2, int(self.bgm.background_height / 8)
        text = '%s' % str(self.bgm.lines_cleared)
        answer_txt = self.font.render(text, False, color)
        self.screen.blit(answer_txt, (x, y))

        # Draw Board
        if self.bgm.draw_bottom:
            self._draw_matrix(self.bgm.board, (0, 0))

        if not self.bgm.hide_piece:
            self._draw_matrix(self.bgm.piece, (self.bgm.piece_x, self.bgm.piece_y))

        if self.text_dictionary_list is not None and len(self.text_dictionary_list) > 0:
            self.draw_text()

    def _draw_matrix(self, matrix, offset, inner_offset=2):
        """
        Draws the specified matrix on screen with the specified offset
        :param matrix: A 2D np array with the color value (key for the color dictionary) at each location for the matrix
        :param offset: Tuple, number of pixels to offset by (this is relative to the board edge, not the screen edge)
        :param inner_offset: the offset for the start of the inner rectangle
        :return: None - draws to screen.
        """
        off_x, off_y = offset
        for y, row in enumerate(matrix):
            for x, val in enumerate(row):
                if val:
                    # draw outline
                    pygame.draw.rect(
                        self.screen,
                        self.BORDER_COLOR,
                        pygame.Rect((off_x + x) * self.bgm.cell_size + self.BOARD_X,
                                    (off_y + y) * self.bgm.cell_size + self.BOARD_Y,
                                    self.bgm.cell_size,
                                    self.bgm.cell_size), 0)
                    # draw inline
                    pygame.draw.rect(
                        self.screen,
                        self.CONSTANT_COLORS[val],
                        pygame.Rect((off_x + x) * self.bgm.cell_size + self.BOARD_X + inner_offset,
                                    (off_y + y) * self.bgm.cell_size + self.BOARD_Y + inner_offset,
                                    self.bgm.cell_size - inner_offset * 2,
                                    self.bgm.cell_size - inner_offset * 2), 0)
