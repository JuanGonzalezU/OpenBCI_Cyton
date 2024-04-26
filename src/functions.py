from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from scipy.signal import welch
import numpy as np
from scipy.signal import butter, filtfilt, iirnotch, freqz


def prepare_board(com_port):
                  
    # Initialize board parameters
    params = BrainFlowInputParams()
    params.serial_port = com_port  # Replace 'COM3' with your actual COM port

    # Create a board objet
    board_id = BoardIds.CYTON_BOARD.value
    board = BoardShim(board_id, params)

    # Prepare the board
    BoardShim.enable_dev_board_logger()  # Enables logging for debugging
    try:
        board.prepare_session()  # Prepares the board for data acquisition
        status = 'Board is ready and connected!'
    except Exception as e:
        print('Error: ', e)
        status = e
    return board,board_id,status

def compute_fft_welch(eeg_data, fs, nperseg=None):
    if nperseg is None or nperseg > eeg_data.shape[1]:
        nperseg = min(fs, eeg_data.shape[1])

    psds = np.empty((eeg_data.shape[0], nperseg//2+1))  # Preallocate array based on typical output size of rfft
    valid_channels = [i for i, channel_data in enumerate(eeg_data) if len(channel_data) >= nperseg]

    for i in valid_channels:
        _, psd = welch(eeg_data[i], fs=fs, nperseg=nperseg)
        psds[i] = psd

    freqs = np.fft.rfftfreq(nperseg, 1/fs)
    return freqs, psds


def compute_power_bands(freqs, psds):
    bands = {'Delta': (0.5, 4), 'Theta': (4, 8), 'Alpha': (8, 13), 'Beta': (13, 30), 'Gamma': (30, 100)}
    band_indices = {band: np.logical_and(freqs >= low, freqs <= high) for band, (low, high) in bands.items()}
    
    psd_mean = np.mean(psds, axis=0)
    band_powers = {band: np.trapz(psd_mean[indices], freqs[indices]) for band, indices in band_indices.items()}
    
    return np.array(list(band_powers.values()))

def eeg_filtering(eeg_data, fs):
    
    return eeg_data

