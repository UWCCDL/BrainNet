import time
import Constants
import numpy as np
import Messages
import CCDLUtil.SignalProcessing.Fourier as Fourier
import CCDLUtil.DataManagement.QueueManagement as QueueManagement
from CCDLUtil.SignalProcessing.Filters import butter_bandpass_filter


def trial_logic(eeg_system, out_buffer_queue, bgm, fs, high_freq, low_freq, prompt, window_width,
                drift_correction=False, sleep_time_if_not_ran=2):
    """
    Run a full trial of SSVEP experiment.

    :param eeg_system: Used EEG system (or None)
    :param out_buffer_queue: the queue to retrieve live data
    :param bgm: graphics task object (BlockGameManager)
    :param fs: sampling rate
    :param high_freq: the high frequency density we need
    :param low_freq: the low frequency density we need
    :param prompt: the prompt sentence to show on SSVEP screen
    :param window_width: the pixel width of the window
    :param sleep_time_if_not_ran: time to sleep if eeg_system == None
    :return: the answer, stop early or late
    """
    bgm.hide_all()
    bgm.show_cursor_task(prompt)
    bgm.graphics.reset_cursor()
    # graphic related constants
    cursor_x = window_width // 2
    boundary_left = 200
    boundary_right = window_width - 200
    # mark start time
    start_time = time.time()
    # If our EEG system is None, we'll sleep for a bit and then return a random result
    if eeg_system is None:
        time.sleep(sleep_time_if_not_ran)
        steps = 5
        packet_index = 0
        while packet_index < steps:
            x = 1 # random.randint(0, 1)
            # compare densities of 17Hz and 15Hz frequencies
            time.sleep(2)
            if x == 0:
                cursor_x += Constants.STEP
                bgm.graphics.move_cursor_delta_x(Constants.STEP)
            else:
                bgm.graphics.move_cursor_delta_x(-Constants.STEP)
            # if we reach left boundary
            if cursor_x + Constants.CURSOR_RADIUS <= boundary_left:
                bgm.graphics.collide_left()
                return Messages.ROTATE, start_time, time.time()
            # right boundary
            if cursor_x + Constants.CURSOR_RADIUS >= boundary_right:
                bgm.graphics.collide_right()
                return Messages.DONT_ROTATE, start_time, time.time()
            packet_index += 1
    else:
        # Else we run the system for real
        QueueManagement.clear_queue(out_buffer_queue)
        # shape of sample is : (sample, channel)
        packet = np.asarray(out_buffer_queue.get())
        # print "received packet: ", packet
        samples_per_packet = packet.shape[0]

        # get constants for full trial
        single_trial_duration_samples = Constants.EEG_COLLECT_TIME_SECONDS * fs
        single_trial_duration_packets = int(single_trial_duration_samples / samples_per_packet)

        # get constants for single window
        window_size_samples = Constants.WINDOW_SIZE_SECONDS * fs
        window_size_packets = window_size_samples / samples_per_packet

        # b is the np array to hold all data in single trial
        b = np.zeros(shape=(single_trial_duration_samples,))
        packet_index = 0
        QueueManagement.clear_queue(out_buffer_queue)
        while packet_index < single_trial_duration_packets:
            # insert the visualizer here
            packet = out_buffer_queue.get()  # Gives us a (10, 1) matrix.
            # print "received packet: ", packet
            # get the sample
            samples = np.squeeze(packet)      # Gives us a (10,) array
            sample_index = packet_index * samples_per_packet
            b[sample_index: sample_index + samples_per_packet] = samples
            packet_index += 1
            # if we have enough samples, perform FFT on a single window
            if packet_index != 0 and packet_index % window_size_packets == 0:
                # print "packet index: ", packet_index, ", do FFT"
                window = b[packet_index * samples_per_packet - window_size_samples:packet_index * samples_per_packet]
                # filter
                if drift_correction:
                    window = butter_bandpass_filter(window, 0.5, 40, 250, order=2)
                # perform FFT
                freq, density = Fourier.get_fft_all_channels(data=np.expand_dims(np.expand_dims(window, axis=0), axis=2),
                                                             fs=fs, noverlap=fs // 2, nperseg=fs)
                # compare densities of 17Hz and 15Hz frequencies
                # print density.shape
                if density[0][high_freq][0] <= density[0][low_freq][0]:
                    cursor_x += Constants.STEP
                    bgm.graphics.move_cursor_delta_x(Constants.STEP)
                else:
                    cursor_x -= Constants.STEP
                    bgm.graphics.move_cursor_delta_x(-Constants.STEP)
                # if we reach left boundary
                if cursor_x - Constants.CURSOR_RADIUS <= boundary_left:
                    bgm.graphics.collide_left()
                    return Messages.ROTATE, start_time, time.time()
                # right boundary
                if cursor_x + Constants.CURSOR_RADIUS >= boundary_right:
                    bgm.graphics.collide_right()
                    return Messages.DONT_ROTATE, start_time, time.time()

    # if time runs out, find which side cursor is closest to
    if cursor_x <= window_width // 2:
        bgm.graphics.collide_left()
        time.sleep(2)
        bgm.hide_all()
        bgm.show_crosshair()
        return Messages.ROTATE, start_time, time.time()
    else:
        bgm.graphics.collide_right()
        time.sleep(2)
        bgm.hide_all()
        bgm.show_crosshair()
        return Messages.DONT_ROTATE, start_time, time.time()

