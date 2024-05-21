from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from scipy.signal import welch
import numpy as np
from scipy.signal import filtfilt, cheby1


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
    bands = {'Delta': (1, 4), 'Theta': (4, 8), 'Alpha': (8, 13), 'Beta': (13, 30), 'Gamma': (30, 100)}
    band_indices = {band: np.logical_and(freqs >= low, freqs <= high) for band, (low, high) in bands.items()}
    
    psd_mean = np.mean(psds, axis=0)
    band_powers = {band: np.trapz(psd_mean[indices], freqs[indices]) for band, indices in band_indices.items()}
    
    return np.array(list(band_powers.values()))

def cheby1_bandpass(lowcut, highcut, fs, order=4, rp=0.5):
    nyq = 0.5 * fs  # Nyquist Frequency
    low = lowcut / nyq
    high = highcut / nyq
    b, a = cheby1(order, rp, [low, high], btype='band')
    return b, a

def cheby1_notch(fs, center_freq=60, band_width=1, order=4, rp=0.5):
    nyq = 0.5 * fs  # Nyquist Frequency
    low = (center_freq - band_width / 2) / nyq
    high = (center_freq + band_width / 2) / nyq
    b, a = cheby1(order, rp, [low, high], btype='bandstop')
    return b, a

def eeg_filtering(eeg_data, fs, lowcut=0.1, highcut=100, order=4, rp=0.5):
    order = 4    
    b, a = cheby1_bandpass(lowcut, highcut, fs, order, rp)
    b1,a1 = cheby1_notch(fs, 60, 1, 4, rp)   
    filtered_data = np.zeros_like(eeg_data)  # Initialize the array to hold filtered data

    # Apply filter to each channel
    for i in range(eeg_data.shape[0]):
        filtered_data[i] = eeg_data[i]-np.mean(eeg_data)
        filtered_data[i] = filtfilt(b, a, filtered_data[i], axis=-1)
        filtered_data[i] = filtfilt(b1, a1, filtered_data[i])
    
    return filtered_data
