import CCDLUtil.Utility.Constants as Constants
import CCDLUtil.EEGInterface.BrainAmp.BrainAmpInterface as BrainAmp
import CCDLUtil.EEGInterface.OpenBCI.OpenBCIInterface as OpenBCI


def start_eeg(eeg_system, live_channels, subject_data_folder_path, subject_num, port=None):
    """
    Start eeg streamer

    :param eeg_system: the name of the eeg system
    :param out_buffer_queue: out buffer queue for live analysis
    :param live_channels: channels to record data from
    :param subject_data_folder_path: file path to save eeg data
    :param subject_num: subject number
    :param port: communication port specifically for OpenBCI headset
    :return: eeg streamer, data save queue
    """

    if eeg_system is None:
        return None, None

    if eeg_system == Constants.EEGSystemNames.BRAIN_AMP:
        eeg_system = BrainAmp.BrainAmpStreamer(channels_for_live=live_channels, live=True, save_data=True,
                                               subject_name=str(subject_num))
    elif eeg_system == Constants.EEGSystemNames.OpenBCI:
        eeg_system = OpenBCI.OpenBCIStreamer(channels_for_live=live_channels, live=True, save_data=True,
                                             subject_name=str(subject_num), port=port)
    else:
        raise ValueError("We will only use BrainAmp and OpenBCI in BrainNet")

    # save data -- this design should be integrated into interfaces in the future!
    eeg_system.start_saving_data(save_data_file_path=subject_data_folder_path+'Subject%s_eeg.csv' % subject_num)

    eeg_system.start_recording()
    return eeg_system
