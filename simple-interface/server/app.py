import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
import numpy as np
import json

import os

st.set_page_config(
    page_title='Game Emotions Viewer', 
    page_icon=":eyeglasses:",
    layout='wide'
)

query_params = st.experimental_get_query_params()
session_id_param = query_params.get('session_id', ['mock-session'])[0]

all_sessions = sorted([d for d in os.listdir('/opt/emotions-dashboard/sessions') if os.path.isdir('/opt/emotions-dashboard/sessions/' + d)])
session_id = st.sidebar.selectbox('Session', all_sessions, index=all_sessions.index(session_id_param))
session_path = f'/opt/emotions-dashboard/sessions/{session_id}'

st.experimental_set_query_params(**{'session_id': session_id})

host = os.environ.get('HOST', 'localhost')

def process_events(events_df, lane_id, ends=False):
    events_df['startTimeMillis'] = events_df['start']
    if ends:
        events_df['endTimeMillis'] = events_df['end']
    events_df['eventId'] = lane_id + events_df.index.astype(str)
    events_df['laneId'] = lane_id 
    events_df['tooltip'] = events_df['type']

    return events_df

game_viewer_component = components.declare_component(
    "game_viewer",
    url=f"http://{host}:3000"
)

timeseries_df = pd.read_csv(f'{session_path}/{session_id}-indicators.csv')
timeseries_df = timeseries_df.set_index('time')
timeseries = timeseries_df.values.T
time = timeseries_df.index.values

channel_names = dict(enumerate(timeseries_df.columns))


events_df = pd.read_csv(f'{session_path}/{session_id}-events.csv').drop(columns="Unnamed: 0")

events_df['start'] = events_df['start_sec']
events_df['end'] = events_df['end_sec']

events_df = process_events(events_df, 'events-lane')

game_json = json.load(open(f'/opt/emotions-dashboard/sessions/mock-description.json'))

st.sidebar.markdown("""
 ## {game_title}, by {game_author}
 * Record time: {record_time}
 * Duration: {duration}
 * Device: OpenBCI Cyton
   * 8 channels, 250 Hz
 * Patient: {patient_name}
""".format(**game_json))

events_json = events_df.to_dict(orient='records') #+\

host = os.environ['HOST']

game_viewer_component(
    video={
        'screen': f'http://{host}:8080/{session_id}/{session_id}_screenVideoFrame.mp4',
        'webcam': f'http://{host}:8080/{session_id}/{session_id}_webCamFrame.mp4'
    },
    signal={
        'time': time.tolist(),
        'duration': time.max(),
        'boredom': timeseries_df['boredom'].tolist(),
        'flow': timeseries_df['flow'].tolist(),
        'anxiety': timeseries_df['anxiety'].tolist()
    },
    events=events_json
)
