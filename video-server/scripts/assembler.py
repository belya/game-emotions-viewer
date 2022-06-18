import sys
sys.path.append('../')

import json
import numpy as np
import os
import pandas as pd
import sqlite3
import cv2
from tqdm import tqdm

from libs import indicators

# TODO calculate frame rate
# TODO restore proper image
# TODO sort frame order

data_dir = '../data'

def restore_video(client_id, json_frames, field):
    print(f"Converting video for {field}")

    first_frame = json_frames[0][field]
    screen_width = first_frame['screenWidth']
    screen_height = first_frame['screenHeight']
    video_fps = round(1 / first_frame["period"])

    frame_order = {}
    for message_json in tqdm(json_frames):
        frame_time = message_json['time']
        image_data = cv2.imread(message_json[field]['videoFrameBase64'])
        frame_order[frame_time] = image_data

    out_video = cv2.VideoWriter(
        f'{data_dir}/{client_id}/{client_id}_{field}_tmp.mp4', 
        cv2.VideoWriter_fourcc(*'mp4v'), 
        video_fps, 
        (screen_width, screen_height), 
        True
    )

    previous_time = 0
    previous_frames = 0
    fixed_frames = []

    for time, image_data in sorted(frame_order.items()):
        expected_frames = int(time * video_fps)
        frame_window_size = expected_frames - previous_frames
        
        fixed_frames += [image_data] * frame_window_size
        previous_frames += frame_window_size
        previous_time = time        

    for image_data in fixed_frames:
        out_video.write(image_data)

    out_video.release()

    print("Video duration:", len(fixed_frames) / video_fps)
    os.system(f"ffmpeg -i {data_dir}/{client_id}/{client_id}_{field}_tmp.mp4 -vcodec libx264 -f mp4 -y {data_dir}/{client_id}/{client_id}_{field}.mp4")


def restore_board_data(client_id, json_frames, field):
    first_frame = json_frames[0][field]
    device = first_frame['device']
    sampling_rate = devices[device]['sampling_rate']
    channels = devices[device]['channels']
    channels_shape = first_frame['channelsShape']

    signal_order = {}
    for message_json in json_frames:
        frame_time = message_json['time']

        signal_window_size = int(message_json[field]["period"] * sampling_rate)
        board_data_path = message_json[field]['boardData']
        board_data = np.load(board_data_path)
        signal_order[frame_time] = board_data

    board_data_sorted = []

    for time, board_data in sorted(signal_order.items()):
        board_data = board_data.reshape(channels_shape, -1)
        board_data_sorted.append(board_data)

    board_data_concat = np.hstack(board_data_sorted)

    print("Board data duration:", board_data_concat.shape[-1] / sampling_rate)
    # TODO set +1 only for OpenBCI
    board_data_df = pd.DataFrame(board_data_concat.T[:, 1:len(channels) + 1], columns=channels)
    board_data_df['time'] = board_data_df.index / sampling_rate

    board_data_df.set_index('time').to_csv(f'{data_dir}/{client_id}/{client_id}-raw-signal.csv')
    return board_data_df, sampling_rate, channels


def restore_indicators(client_id, board_data_df, sampling_rate, channels):
    indicators_df = indicators.get_indicators(board_data_df, sampling_rate, channels)
    indicators_df.to_csv(f'{data_dir}/{client_id}/{client_id}-indicators.csv')


def restore_events(client_id):
    events_database = f'{data_dir}/{client_id}/events.db'
    conn = sqlite3.connect(events_database)
    events_df = pd.read_sql("""
        SELECT 
            game_time AS start_sec,
            game_time + 0.1 AS end_sec,
            type
        FROM events
        ORDER BY game_time
    """, conn)
    events_df.to_csv(f'{data_dir}/{client_id}/{client_id}-events.csv')


if __name__ == '__main__':
    devices = json.load(open('../devices.json'))

    client_ids = [
        path
        for path in os.listdir(f'{data_dir}/')
        if os.path.isdir(f'{data_dir}/{path}')
    ]

    if len(sys.argv) > 1:
        client_id = sys.argv[1]
        client_ids = [f"{data_dir}/{client_id}/"]

    for client_id in client_ids:
        # Frame reading
        dir_path = f'{data_dir}/{client_id}'

        if os.path.exists(dir_path + '/compiled'):
            continue
        if 'mock-session' in client_id:
            continue

        json_frames = []

        frames_path = dir_path + '/jsonFrame'

        for file in tqdm(list(os.listdir(frames_path))):
            if ".json" not in file:
                continue

            path = os.path.join(frames_path, file)
            try:
                message_json = json.load(open(path))
            except:
                print(f"{file} is unreadable")

            json_frames.append(message_json)

        json_frames = sorted(json_frames, key=lambda x: x['time'])

        board_data_df, sampling_rate, channels = restore_board_data(client_id, json_frames, 'boardFrame')
        restore_indicators(client_id, board_data_df, sampling_rate, channels)
        restore_video(client_id, json_frames, 'webCamFrame')
        restore_video(client_id, json_frames, 'screenVideoFrame')
        restore_events(client_id)

        os.system(f'touch {dir_path}/compiled')
