import mne
import pandas as pd
import matplotlib
import numpy as np
import json

supported_bands = {
    "alpha": (7, 14),
    "low-beta": (15, 25)
}

def get_raw_signal(signal_df, ch_types, sampling_freq):
    additional_channels = ["x", "y", "z", "time", "timestamp"]

    main_channels_num = (signal_df.shape[1] - 1 - len(additional_channels))
    main_channels = [f"channel_{i}" for i in range(main_channels_num)] 

    ch_names = ["#"] + main_channels + additional_channels
    signal_df.columns = ch_names

    # signal_df["time"] = pd.to_datetime(signal_df["time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    signal_df["time"] = pd.to_datetime(signal_df["timestamp"], unit='ms')
    
    signal_info = mne.create_info(
        ch_names, 
        ch_types=ch_types, 
        sfreq=sampling_freq
    )
    signal_info.set_montage('standard_1020')
    signal_info["start_time"] = signal_df["time"].min()
    
    data = signal_df[ch_names].values.T
    raw = mne.io.RawArray(data, signal_info)

    # Filter line noise
    raw.notch_filter(50, notch_widths=3)

    # Filter nessesary frequencies
    raw.filter(1, 50)
    
    return raw

def get_bands(raw, sampling_freq, channels, frequencies, stim_channel_name=None):
    channel_raw = raw.copy().pick(channels).get_data(channels)
    channel_fft = np.abs(
        mne.time_frequency.stft(channel_raw, sampling_freq, 16)[:, frequencies, :]
    )
    
    channel_alpha = channel_fft.mean(axis=0).mean(axis=0)
    
    signal_info = mne.create_info(
        ["amplitude"], 
        ch_types=["misc"], 
        sfreq=sampling_freq // 16
    )
    signal_info["start_time"] = raw.info["start_time"]
    
    data = [channel_alpha]
    
    return mne.io.RawArray(data, signal_info)

def get_indicators(signal_df):
    # Get raw signal
    # Extract bands for channels
    # Compose bands