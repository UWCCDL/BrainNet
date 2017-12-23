import numpy as np


def string_to_matrix(string, shape_x, shape_y):
    string = string.replace('[', '').replace(']', '')
    string_lst = string.split(',')
    string_lst = [int(xx.strip()) for xx in string_lst]
    string = np.asarray(string_lst)
    return string.reshape((int(shape_x), int(shape_y)))


def string_board_shape_to_tup_board_shape(board_shape):
    """
    Takes a string of the form '(x, xx)', where x and xx are numbers

    Returns float(x), float(xx)
    """
    board_shape.replace('(', '').replace(')', '')
    board_shape = board_shape.split(',')
    board_shape = [float(xx.strip()) for xx in board_shape]
    return board_shape[0], board_shape[1]
