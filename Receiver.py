import os
import time
import Queue
import random
import datetime
import Messages
import Constants
import PygameUtils.EEGSetup as EEG
import SSVEP
from CCDLUtil.Communications.MultiClientServer import TCPServer as Server
import CCDLUtil.DataManagement.Log as Log
import CCDLUtil.Constants.BrainAmpConsts as EEGConstants
from CCDLUtil.Utility.VerboseInfo import verbose_info
import CCDLUtil.Utility.AssertVal as Assert
import CCDLUtil.DataManagement.FileParser as FileParser
from BlockGame.BlockGameManager import BlockGameManager
import CCDLUtil.Utility.SystemInformation as SystemsInfo
from CCDLUtil.ArduinoInterface.Arduino2LightInterface import Arduino2LightInterface as Arduino
import CCDLUtil.MagStimRapid2Interface.ArmAndFire as TMS


'''create server'''
server = Server(port=Constants.PORT, buf=8192)

# This computer is referred to as c0. Other computers are c1 and c2
# Left is Turn, Right is NoTurn. 0 is Turn, 1 is No Turn.


def is_control(s):
    assert s == 'Control' or s == 'Experimental'
    return True if s == 'Control' else False


def start_graphics():
    """
    Create Graphics object and set up cursor task
    :return: 
    """
    return BlockGameManager(window_x_pos=1920, window_y_pos=0, background_width=1920, background_height=1080,
                            board_height=Constants.BOARD_HEIGHT, board_width=Constants.BOARD_WIDTH,
                            cell_size=Constants.CELL_SIZE, num_cols=Constants.NUM_COLS,
                            num_rows=Constants.NUM_ROWS)


def prompt_screen(bgm, attempt, computer):
    """
    Show the prompt for subject to wait for a stimulation
    :param bgm: BlockGameManager
    :param attempt: the number of attempt to show on screen
    :param computer: the index of the computer (C1 or C2)
    """
    bgm.hide_all()
    bgm.graphics.set_text_dictionary_list({'text': 'Stimulation from Sender%s, Attempt %s' % (str(computer), str(attempt)),
                                           'pos': (None, 150), 'color': (255, 255, 255)})


def main(data_folder):
    # Set up the TMS Machine
    tms = None
    if FIRE_TMS:
        tms = TMS.TMS()
        tms.tms_arm()
    # sampling rate
    fs = SystemsInfo.get_eeg_sampling_rate(EEGConstants.NAME)
    # manage data storage / Start EEG threads
    subject_num, subject_data_folder_path = FileParser.manage_storage(data_storage_location=data_folder,
                                                                      take_init=TAKE_INIT)
    condition, experiment_num = 0, 0
    # for BrainAmp
    live_channels = ['Oz']

    if TAKE_INIT:
        experiment_num = int(raw_input('TMS Group Experiment Number Tracker:'))
        condition = int(raw_input('Enter condition (int):'))
        tms_low = int(raw_input('Enter TMS Low intensity (integer between 1 and 100):'))
        tms_high = int(raw_input('Enter TMS High intensity (integer between 1 and 100):'))
        # check intensity range
        Assert.assert_less(tms_low, tms_high)
        Assert.assert_less(tms_high, 100)
        Assert.assert_greater(tms_low, 0)
    else:
        tms_high, tms_low = 70, 55

    # Create Arduino
    if RUN_ARDUINO:
        ard = Arduino(com_port=ARDUINO_COMPORT)
    else:
        ard = None
    # Load our reference list
    ref_list = FileParser.load_yaml_file('ref/Condition%d.yaml' % condition)
    verbose_info(VERBOSE, ref_list)
    # Set up our EEG system
    if RUN_EEG:
        eeg = EEG.start_eeg(EEGConstants.NAME, live_channels, subject_data_folder_path, subject_num)
    else:
        eeg, data_save_queue = None, Queue.Queue()
    # out buffer queue
    out_buffer_queue = eeg.out_buffer_queue if eeg is not None else None
    # Start our Logging
    log_file_save_location = subject_data_folder_path + 'Subject%s_log.txt' % subject_num
    logger = Log.Log(subject_log_file_path=log_file_save_location)
    verbose_info(VERBOSE, "Saving Log File: " + log_file_save_location)

    # graphics
    bgm = start_graphics()
    # Meta contains all the meta info about the experiment, such as the condition number and the subject number.
    meta = {'condition': condition, 'subject_id': subject_num, 'high_tms': tms_high, 'low_tms': tms_low,
            'experiment_num': experiment_num, 'subject_num': subject_num, 'data_path': subject_data_folder_path}
    logger.info(str(meta))  # Save our meta info to our log file.

    # Start
    run_main_logic(ref_list=ref_list, bgm=bgm, ard=ard, logger=logger, eeg=eeg, fs=fs,
                   out_buffer_queue=out_buffer_queue, tms=tms, tms_low=tms_low, tms_high=tms_high)


def start_connection():
    verbose_info(VERBOSE, "Waiting to receive message: " + Messages.READY_TO_START)

    c1_message, c2_message = None, None
    # If we are either running c1 or c2, we'll wait for our message from each.
    if RUN_C1:
        while not server.is_connected_with(Constants.C1_IP_ADDRESS):
            pass
        c1_message = server.receive_msg(Constants.C1_IP_ADDRESS)
    if RUN_C2:
        while not server.is_connected_with(Constants.C2_IP_ADDRESS):
            pass
        c2_message = server.receive_msg(Constants.C2_IP_ADDRESS)

    # Throw our errors if our messages don't match
    if RUN_C1 and RUN_C2:
        if c1_message != Messages.READY_TO_START or c2_message != Messages.READY_TO_START:
            raise ValueError("Invalid Message received: %s and %s" % (str(c1_message), str(c2_message)))
    if RUN_C1 and not RUN_C2:
        if c1_message != Messages.READY_TO_START:
            raise ValueError("Invalid Message received: %s and %s" % (str(c1_message), str(c2_message)))
    if not RUN_C1 and RUN_C2:
        if c2_message != Messages.READY_TO_START:
            raise ValueError("Invalid Message received: %s and %s" % (str(c1_message), str(c2_message)))

    # If we aren't running either c1 or c2, just sleep for mock_sleep_time seconds.
    if not RUN_C1 and not RUN_C2:
        time.sleep(2)

    print "System ready to start"


def run_main_logic(ref_list, bgm, ard, logger, fs, eeg, out_buffer_queue,
                   tms, tms_low, tms_high):
    """
    Runs main logic of the game
    """
    bgm.show_crosshair()
    # Wait until the other computers have started
    start_connection()

    # log header
    head_dict = {'Computer_type': COMPUTER_TYPE, 'sender_or_receiver': 'receiver', 'tms_low_intensity': tms_low, 'tms_high_intensity': tms_high, 'Experiment_Date': "{:%B %d, %Y}".format(datetime.datetime.now()), 'start_time': time.time()}
    logger.info(str(head_dict))

    # Count the number of trials we iterate over.
    for trial_index, control_txt in enumerate(ref_list):
        # Clear our feedback
        bgm.graphics.set_text_dictionary_list([])
        # Create a Trial dictionary for recording events in this trial
        trial_dict = {'trial_index': trial_index, 'control_trial': control_txt}
        # Set whether this is a control or experimental trial
        assert control_txt in (Constants.CONTROL_STR, Constants.EXPERIMENTAL_STR)
        # generate new board
        bgm.new_board(control=(control_txt == Constants.CONTROL_STR))
        round_info = dict()
        # for round_index in [1, 2]:  # Round_index = 1 if we are first starting, 2 if we are on the second pass.
        for round_index in range(Constants.NUM_ROUNDS):

            # show just the piece
            bgm.hide_bottom()
            bgm.show_block_game()

            # get current board string and send to Senders
            board_str = bgm.board_to_string()
            send_message_to_other_computers(message=board_str)
            # send control text
            send_message_to_other_computers(message=control_txt)
            # log data for this round
            round_info.clear()
            round_info['round_index'] = round_index
            round_info['C1_and_C2_start_message_sent_time'] = time.time()

            # let subject know we're going to wait
            pos = (None, None) if round_index == 0 else (None, 100)
            bgm.graphics.set_text_dictionary_list({'text': 'Waiting on Senders', 'pos': pos,
                                                   'color': (255, 255, 255)})

            # wait for Senders to make their selections
            c1_message, c2_message = wait_for_trial_results()

            # log data
            round_info['C1_and_C2_command_receive_time'] = time.time()
            round_info['C1_command'] = c1_message
            round_info['C2_command'] = c2_message

            # True if Sender says to rotate
            c1_rotate = (c1_message == Messages.ROTATE)
            c2_rotate = (c2_message == Messages.ROTATE)

            # Fire the TMS to transmit the Sender information to the Receiver
            fire_times = fire_twice(c1_rotate, c2_rotate, bgm, tms, tms_high, tms_low, round_index)

            # log data
            round_info['fire_tms1_time'] = fire_times[0]
            round_info['fire_tms2_time'] = fire_times[1]

            # give subject time to make decision
            time.sleep(Constants.SLEEP_AFTER_TMS_FIRE_TWICE)

            # Arduino lights on and off
            if RUN_ARDUINO:
                ard.turn_both_on()
            # -----RUN SSVEP----- #
            c0_response, c0_start_data_collection_time, c0_end_data_collection_time = \
                SSVEP.trial_logic(eeg, out_buffer_queue, bgm, fs, 17, 15, 'Do you choose to turn the piece?', 1920)
            if RUN_ARDUINO:
                ard.turn_both_off()

            # update turn flag
            turn_flag = (c0_response == Messages.ROTATE)
            bgm.show_block_game()
            time.sleep(1)
            # update board here
            if turn_flag:
                bgm.rotate_piece()
            time.sleep(1)

            # log data
            round_info['c0_response'] = c0_response
            round_info['c0_start_data_collection_time'] = c0_start_data_collection_time
            round_info['c0_end_data_collection_time'] = c0_end_data_collection_time
            round_info['turn_flag'] = turn_flag
            trial_dict['round_' + str(round_index)] = round_info

            if round_index == 0:
                # drop half way
                bgm.drop_piece_halfway()

        # send final board to Senders
        send_message_to_other_computers(message=bgm.board_to_string())
        # display the dropping of the piece
        bgm.show_bottom()
        time.sleep(1)
        bgm.drop_piece()
        time.sleep(1)
        success = bgm.clear_rows()
        time.sleep(2)
        send_message_to_other_computers(message=str(success))
        # Save all our trial information.
        logger.info(str(trial_dict))


def fire_twice(c1_turn, c2_turn, bgm, tms, high_intensity, low_intensity, attempt):
    """
    Fires the TMS twice if fire_tms_flag.  If not fire_tms_flag, we'll just flash the crosshairs red.
    
    Fires according to:
        TMS- High threshold if cX_turn is True (we need to rotate the piece)

    Fire High if Rotate.  Fire low if Not Rotate.

    :param c1_turn: True if we need to rotate the piece as according to c1, false otherwise
    :param c2_turn: True if we need to rotate the piece as according to c2, false otherwise
    :param bgm: Block game manager (so we can flash the cross hairs)
    :param tms: the TMS object
    :param high_intensity: the high intensity to fire TMS
    :param low_intensity: the low intensity to fire TMS
    :param attempt: show the round index (1 or 2)
    """
    # set up
    Assert.assert_less(low_intensity, high_intensity)
    verbose_info(VERBOSE, "Firing TMS: %s, %s" % ('High' if c1_turn else "Low", 'High' if c2_turn else "Low"))
    fire_times = []
    for i, cx_turn in enumerate([c1_turn, c2_turn]):
        # show prompt
        prompt_screen(bgm, attempt + 1, i + 1)
        # fire
        if FIRE_TMS:
            # Set our intensity now so we can fire sooner later.
            if cx_turn:
                tms.set_intensity(intensity=high_intensity)
            else:
                tms.set_intensity(intensity=low_intensity)

        if FIRE_TMS:
            fire_times.append(fire(cx_turn, bgm=bgm, tms=tms, high_intensity=high_intensity, low_intensity=low_intensity))
        # Only sleep after c1_turn
        if i == 0:  # We need to sleep between firings for safety reasons.
            time.sleep(Constants.SLEEP_BETWEEN_FIRINGS)

    if not FIRE_TMS:
        fire_times = [None, None]

    return fire_times


def fire(high_flag, bgm, tms, high_intensity, low_intensity):
    """
    Fire the TMS at the high intensity if high_flag, else we'll fire it at the low intensity.
    """
    Assert.assert_less(low_intensity, high_intensity)
    # flash red crosshair
    fire_time = time.time()
    bgm.flash_red()
    if high_flag:
        tms.tms_fire(i=high_intensity)
    else:
        tms.tms_fire(i=low_intensity)
    return fire_time


def wait_for_trial_results():
    """
    We'll wait for our trial results from c2 and c2.  We'll throw an error if we receive an invalid message

    :param run_c1: True if we are running c1, false if we are mocking it.
    :param run_c2: True if we are running c2, false if we are not.
    :returns: c1_message, c2_message
    """
    valid_messages = {Messages.ROTATE, Messages.DONT_ROTATE}

    if RUN_C1:  # If we are running c1, we'll wait for a message from it
        c1_message = server.receive_msg(Constants.C1_IP_ADDRESS)
    else:  # Else, we select a message at random.
        c1_message = random.choice(tuple(valid_messages))

    if RUN_C2:
        c2_message = server.receive_msg(Constants.C2_IP_ADDRESS)
    else:
        c2_message = random.choice(tuple(valid_messages))

    # Ensure we received valid messages.
    if c1_message not in valid_messages or c2_message not in valid_messages:
        raise ValueError("Invalid message - Expected either %s or %s" %
                         (Messages.ROTATE, Messages.DONT_ROTATE))
    print "got both messages..."
    return c1_message, c2_message


def send_message_to_other_computers(message):
    """
    Sends message to both the C1 and C2 Computers
    :param message: The message to send
    :return: None -- Sends messages
    """
    if RUN_C1:
        server.send_msg(Constants.C1_IP_ADDRESS, message)
    if RUN_C2:
        server.send_msg(Constants.C2_IP_ADDRESS, message)


if __name__ == '__main__':
    # This is receiver C0
    COMPUTER_TYPE = 'C0'
    # Arduino comport
    ARDUINO_COMPORT = 10
    # data storage
    DATA_FOLDER = os.path.abspath('ExperimentData')
    # -----Debug Flags and parameters----- #
    C0_RESPONSE_TIME_SECONDS = 3  # The amount of time we will wait for C0 response.  For the experiment, set this to 18
    # Do we want to run C1 and/or C2?
    RUN_C1, RUN_C2 = True, True
    RUN_EEG = True
    ##### CHANGE BACK TO TRUE FOR ALL SET UP
    RUN_ARDUINO = True
    FIRE_TMS = True
    TAKE_INIT = False
    VERBOSE = True  # We'll print what is happening to console if this is set to True.

    main(data_folder=DATA_FOLDER)
