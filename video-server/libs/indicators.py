import mne
import pandas as pd
import matplotlib
import numpy as np
import json

from scipy.signal import hilbert

rhythms = {
    'theta': (4, 8), 
    'alpha': (8, 14), 
    'beta': (15, 30)
}

indicator_names = {
    'alpha': 'flow',
    'beta': 'boredom',
    'theta': 'anxiety'
}

def get_raw_signal(signal_df, sampling_freq, ch_names):
    # signal_df.columns = ch_names

    # signal_df["time"] = pd.to_datetime(signal_df["time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
#     signal_df["time"] = pd.to_datetime(signal_df["timestamp"], unit='ms')
    
    ch_types = ["eeg"] * len(ch_names)

    signal_info = mne.create_info(
        ch_names, 
        ch_types=ch_types, 
        sfreq=float(sampling_freq)
    )
    signal_info.set_montage('standard_1020')
    
    data = signal_df[ch_names].values.T

    raw = mne.io.RawArray(data, signal_info)

    raw.notch_filter(50, notch_widths=3)

    raw.filter(1, 50)
    
    return raw

def process_indicator(averaged_amplitude_data, sfreq, downsample_factor=10):
    insight_points = averaged_amplitude_data.shape[0] / sfreq * 1 * 1
    quantile_insights = insight_points / averaged_amplitude_data.shape[0]
    level_of_interest = np.quantile(averaged_amplitude_data, 1 - quantile_insights)

    indicator = pd.Series(averaged_amplitude_data > level_of_interest).rolling(int(sfreq) * 5, center=True).mean().fillna(0)
    indicator = indicator / indicator.max()

    indicator = indicator[indicator.index % downsample_factor == 0].copy()

    return indicator

def get_indicators(signal_df, sampling_freq, ch_names):
    indicators_df = pd.DataFrame()
    selected_channels = 'Fp1, AF7, AF3, F7, F5, F3, FT7, FC5, FC3, FC1'.split(', ')
    selected_channels = [c for c in selected_channels if c in signal_df.columns]

    assert len(selected_channels) > 0

    raw = get_raw_signal(signal_df, sampling_freq, ch_names)

    for band, (start_f, end_f) in rhythms.items():
        channel_data = raw.copy().pick(selected_channels).filter(start_f, end_f).get_data()

        analytical_signal = hilbert(channel_data)
        amplitude_data = np.abs(analytical_signal)
        averaged_amplitude_data = amplitude_data.mean(axis=0)
        sfreq = raw.info['sfreq']

        indicator = process_indicator(averaged_amplitude_data, sfreq)

        indicator_name = indicator_names[band]
        indicators_df[indicator_name] = indicator

    indicators_df.index = indicators_df.index / sfreq
    indicators_df.index.name = 'time'

    return indicators_df