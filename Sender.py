import os
import time
import Queue
import datetime
import Messages
import Constants
import SSVEP
import PygameUtils.EEGSetup as EEG
import CCDLUtil.Constants.OpenBCIConsts as EEGConstants
from CCDLUtil.Communications.TCPClient import TCPClient as Client
from BlockGame.BlockGameManager import BlockGameManager
import CCDLUtil.DataManagement.FileParser as FileParser
import CCDLUtil.DataManagement.Log as Log
from CCDLUtil.ArduinoInterface.Arduino2LightInterface import Arduino2LightInterface as Arduino
from CCDLUtil.Utility.VerboseInfo import verbose_info
import CCDLUtil.Utility.AssertVal as Assert


"""Create TCP Client"""
client = Client(server_ip=Constants.C0_IP_Address, port=Constants.PORT, buf=8192)


def start_graphics():
    """
    Create Graphics object and set up cursor task

    :return: BlockGameManager object
    """
    return BlockGameManager(window_x_pos=0, window_y_pos=0, background_width=1680, background_height=1050,
                            board_height=Constants.BOARD_HEIGHT, board_width=Constants.BOARD_WIDTH,
                            cell_size=Constants.CELL_SIZE, num_cols=Constants.NUM_COLS,
                            num_rows=Constants.NUM_ROWS)


def main(data_folder, live_channels, high_freq, low_freq, take_init, com_port):
    """
    Start the sender side of the experiment

    :param data_folder: the folder path to save EEG data
    :param live_channels: the channels for EEG live analysis
    :param high_freq: the high frequency used for SSVEP
    :param low_freq: the low frequency used for SSVEP
    :param take_init: true to take initial information from experimenter
    :param com_port: the communication
    :return:
    """
    # channel_dict
    fs = EEGConstants.FS
    # Start Arduino
    ard = None
    if RUN_ARDUINO:
        ard = Arduino(com_port=com_port)
    # manage data storage
    subject_num, subject_data_folder_path = FileParser.manage_storage(data_storage_location=data_folder,
                                                                      take_init=take_init)
    # start eeg
    if RUN_EEG:
        eeg = EEG.start_eeg(EEGConstants.NAME, live_channels, subject_data_folder_path, subject_num,
                            port=OPENBCI_COMPORT)
    else:
        eeg = None
    # out buffer queue
    out_buffer_queue = eeg.out_buffer_queue if eeg is not None else None
    # Start taking log file
    log_file_save_location = subject_data_folder_path + 'Subject%s_log.txt' % subject_num
    logger = Log.Log(subject_log_file_path=log_file_save_location)
    verbose_info(VERBOSE, "Saving Log File: " + log_file_save_location)
    # start graphics with only crosshair
    bgm = start_graphics()
    bgm.show_crosshair()
    # start main logic
    run_main_logic(bgm, fs, eeg, high_freq, low_freq, out_buffer_queue, ard, logger)


def run_main_logic(bgm, fs, eeg, high_freq, low_freq, out_buffer_queue, ard, logger):
    """
    Runs main logic of the game
    """
    # -----Set up----- #
    bgm.show_crosshair()
    # Send "Ready" message
    send_msg(message=Messages.READY_TO_START)
    # Record our header for our log file
    head_dict = {'Computer_type': COMPUTER_TYPE, 'sender_or_receiver': 'sender',
                 'Experiment_Date': "{:%B %d, %Y}".format(datetime.datetime.now()), 'start_time': time.time()}
    logger.info(str(head_dict))
    # Count the number of trials we iterate over.
    trial_index = 0

    while trial_index < Constants.NUM_EXP_TRIALS:
        # We don't need to record if this is a control trial or not.  This should be saved in the C0 log.
        trial_dict = {'trial_index': trial_index}
        turn_flag = None
        turn_times = 0
        for round_index in range(Constants.NUM_ROUNDS):
            # get board from c0
            bgm.set_board(str(get_msg()))
            bgm.show_block_game()
            bgm.graphics.update_graphics()
            control_txt = str(get_msg())
            # create dict to save info
            round_dict = dict()
            # Record meta information on the current round
            round_dict['round_index'] = round_index
            round_dict['initial_board_str'] = bgm.board_to_string()
            round_dict['C0_start_message_received'] = time.time()
            # wait to let subject determine their answer
            time.sleep(Constants.SLEEP_AFTER_SHOWING_BLOCK_GAME_TO_CX)
            # Get our response from the sender and send it to C0
            if RUN_ARDUINO:
                ard.turn_both_on()
            # ----------RUN SSVEP----------
            if AFFECTED and trial_index in Constants.FALSE_TRIAL and round_index == 0:
                response, start_data_collection_time, end_data_collection_time = \
                    SSVEP.trial_logic(None, out_buffer_queue, bgm, fs, high_freq, low_freq, "Turn the piece or not?",
                                      1680, drift_correction=True, direction=(control_txt == "Control"))
            else:
                response, start_data_collection_time, end_data_collection_time = \
                    SSVEP.trial_logic(eeg, out_buffer_queue, bgm, fs, high_freq, low_freq, "Turn the piece or not?",
                                      1680,
                                      drift_correction=True)

            if RUN_ARDUINO:
                ard.turn_both_off()
            # Give our answer to receiver
            send_msg(message=response)
            # Give Feedback to the Sender
            turn_flag = response == Messages.ROTATE
            if turn_flag:
                turn_times += 1
            # update prompt
            bgm.graphics.set_text_dictionary_list({'text': 'Waiting for Receiver to make a decision', 'pos': (None, 150),
                                                   'color': (255, 255, 255)})
            # Store our round dictionary into our trial dictionary
            round_dict['response'] = response
            round_dict['start_data_collection_time'] = start_data_collection_time
            round_dict['end_data_collection_time'] = end_data_collection_time
            round_dict['turn_flag'] = turn_flag
            trial_dict['round_' + str(round_index)] = round_dict
            # sleep for a sec
            time.sleep(Constants.SLEEP_AFTER_SHOWING_CX_FEEDBACK)

        # blocking call -- only show board after receive the new board
        board = str(get_msg())
        bgm.show_block_game()
        bgm.set_board(board)
        time.sleep(1)
        # show it
        bgm.drop_piece()
        time.sleep(1)
        bgm.clear_rows()
        time.sleep(1)
        # show feedback
        if get_msg() == 'True':
            feedback = 'You successfully cleared a line'
        else:
            feedback = 'You failed to clear a line'
        bgm.graphics.set_text_dictionary_list({'text': feedback, 'pos': (None, None), 'color': (255, 255, 255)})
        time.sleep(3)
        logger.info(str(trial_dict))


def get_msg():
    """
    Get message from C0
    :param run_c0: True to run c0
    :return: the game board string
    """
    if RUN_C0:  # If we are running c1, we'll wait for a message from it
        return client.receive_message()
    return None


def send_msg(message):
    """
    Sends message to C0
    :param run_c0: True to run C0
    :param message: The message to send
    :return: None
    """
    if RUN_C0:
        client.send_message(message)


if __name__ == '__main__':
    COMPUTER_TYPE = Constants.C2
    DATA_FOLDER = os.path.abspath('ExperimentData')
    ''' Debug Flags and parameters'''
    C0_RESPONSE_TIME_SECONDS = 3
    ARDUINO_COMPORT = "COM4"
    OPENBCI_COMPORT = "COM5"
    HIGH_FREQ = 17
    LOW_FREQ = 15
    RUN_C0 = True
    RUN_EEG = True
    TAKE_INIT = False
    VERBOSE = True  # We'll print what is happening to console if this is set to True.
    RUN_ARDUINO = True
    AFFECTED = False
    LIVE_CHANNELS = [int(input("What is the index (start from zero) for Oz channel? "))]
    main(data_folder=DATA_FOLDER, live_channels=LIVE_CHANNELS, high_freq=HIGH_FREQ,
         low_freq=LOW_FREQ, take_init=TAKE_INIT, com_port=ARDUINO_COMPORT)
