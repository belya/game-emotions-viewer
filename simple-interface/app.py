import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
import numpy as np

from libs import vis
from libs import stats 
from libs import eventql

import os

# -- Set page config

def process_events(events_df, lane_id, ends=False):
    events_df['startTimeMillis'] = events_df['start']
    if ends:
        events_df['endTimeMillis'] = events_df['end']
    events_df['eventId'] = lane_id + events_df.index.astype(str)
    events_df['laneId'] = lane_id 
    events_df['tooltip'] = events_df['type']

    return events_df

st.set_page_config(
    page_title='Game Emotions Viewer', 
    page_icon=":eyeglasses:",
    layout='wide'
)

game_viewer_component = components.declare_component(
    "game_viewer",
    url="http://localhost:3000"
)

timeseries_df = pd.read_csv('mock-session-indicators.csv')
timeseries_df = timeseries_df.set_index('time')
timeseries = timeseries_df.values.T
time = timeseries_df.index.values

channel_names = dict(enumerate(timeseries_df.columns))


events_df = pd.read_csv('mock-session-events.csv').drop(columns="Unnamed: 0")

events_df['start'] = events_df['start_sec']
events_df['end'] = events_df['end_sec']

events_df = process_events(events_df, 'events-lane')

st.sidebar.markdown("""
 ## Match-3, by Winterbolt Games
 * Record time: 07.01.2022, 20:45
 * Duration: 1 min 28 sec
 * Device: OpenBCI Cyton
   * 8 channels, 250 Hz
 * Patient: NOOMKCALB
""")

eventql_query = st.sidebar.text_input('EventQL query:', '[match3x]')
# show_events = st.sidebar.checkbox('Show events', True)
# show_fragments = st.sidebar.checkbox('Show selected fragments', True)

unique_events = events_df['type'].unique()
events_dict = eventql.create_events_dictionary(unique_events)
source_string = eventql.get_eventql_source_string(events_df, events_dict=events_dict)
eventql_regex = eventql.extract_regex(eventql_query, events_dict=events_dict)
fragments_df = eventql.search_regex_indices(events_df, source_string, eventql_regex)

abtest_stats = stats.calculate_simple_statistics(
    timeseries, 
    fragments_df
)

fragments_df = process_events(fragments_df, 'fragments-lane', ends=True)

events_json = events_df.to_dict(orient='records') +\
    fragments_df.to_dict(orient='records')

stat_text = [
    "## General Event Information",
    f"* Repeats: {abtest_stats['count']}",
    f"* Avg. duration: {abtest_stats['length'] / 100:.2f} sec.",
]

for i, score in enumerate(abtest_stats['scores']):
    stat_text.append(f'* {channel_names[i].capitalize()} p-value: {score * 100:.2f}%')

os.system('cp ./mock-session.mp4 ./frontend/public/')

game_viewer_component(
    video='./mock-session.mp4',
    signal={
        'time': time.tolist(),
        'duration': time.max(),
        'boredom': timeseries_df['boredom'].tolist(),
        'flow': timeseries_df['flow'].tolist(),
        'anxiety': timeseries_df['anxiety'].tolist()
    },
    events=events_json
)

st.sidebar.markdown("\n".join(stat_text))
