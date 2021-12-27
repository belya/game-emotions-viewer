from scipy import stats
import numpy as np


def calculate_simple_statistics(timeseries, fragments_df):
    fragments_length = fragments_df['end'] - fragments_df['start']
    fragments_count = fragments_df.shape[0]
    
    mean_fragment_length = fragments_length.mean()
    timeseries_parts = []
    
    for i, fragment in fragments_df.iterrows():
        timeseries_part = timeseries[:, int(fragment['start']):int(fragment['end'])]
        timeseries_parts.append(timeseries_part)
        
    timeseries_parts_concat = np.hstack(timeseries_parts)
    
    channel_means = timeseries_parts_concat.mean(axis=1)
    channel_stds = timeseries_parts_concat.std(axis=1)
    n_points = timeseries_part.shape[-1]
    channel_scores = stats.norm.cdf(channel_means / channel_stds * np.sqrt(n_points))
    
    return {
        'count': fragments_count,
        'length': mean_fragment_length,
        'scores': channel_scores
    }
