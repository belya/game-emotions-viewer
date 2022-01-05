import streamlit as st

import pandas as pd
import numpy as np

from libs import vis
from libs import stats 
from libs import eventql

# -- Set page config

st.set_page_config(
    page_title='Game Emotions Viewer', 
    page_icon=":eyeglasses:",
    layout='wide'
)

timeseries_df = pd.read_csv('mock-session-indicators.csv')
timeseries_df = timeseries_df.set_index('time')
timeseries = timeseries_df.values.T
time = timeseries_df.index.values

channel_names = dict(enumerate(timeseries_df.columns))

events_df = pd.read_csv('mock-session-events.csv')
events_df['start'] = events_df['start_sec']
events_df['end'] = events_df['end_sec'] 

st.sidebar.markdown("""
 ## Legend of Zelda: Breath of the Wild
 * Record time: 20.05.2022, 11:00
 * Duration: 7 min 31 sec
 * Device: OpenBCI Cyton, 8 channels, 250 Hz
 * Patient: NOOMKCALB
""")

eventql_query = st.sidebar.text_input('EventQL query:', 'down -> [up] -> down')
show_events = st.sidebar.checkbox('Show events', True)
show_fragments = st.sidebar.checkbox('Show selected fragments', True)

unique_events = events_df['type'].unique()
events_dict = eventql.create_events_dictionary(unique_events)
source_string = eventql.get_eventql_source_string(events_df, events_dict=events_dict)
eventql_regex = eventql.extract_regex(eventql_query, events_dict=events_dict)
fragments_df = eventql.search_regex_indices(events_df, source_string, eventql_regex)

abtest_stats = stats.calculate_simple_statistics(
    timeseries, 
    fragments_df
)

stat_text = [
    "## General Event Information",
    f"* Repeats: {abtest_stats['count']}",
    f"* Avg. duration: {round(abtest_stats['length'] / 100, 2)} sec.",
]

for i, score in enumerate(abtest_stats['scores']):
    stat_text.append(f'* {channel_names[i]} p-value: {score * 100}%')

st.sidebar.markdown("\n".join(stat_text))

fig = vis.show_channels(timeseries, time)

if show_events:
    vis.show_events(fig, events_df)

if show_fragments:
    vis.show_events(fig, fragments_df)

# vis.show_slider(fig)

st.plotly_chart(fig, use_container_width=True)

video_file = open('mock-session.mp4', 'rb')
video_bytes = video_file.read()

st.video(video_bytes)

