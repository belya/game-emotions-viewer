import sys
import json
import numpy as np
import os
import pandas as pd
import sqlite3
import cv2

# TODO calculate frame rate
# TODO restore proper image
# TODO sort frame order

if __name__ == '__main__':
    client_id = sys.argv[1]
    dir_path = f"./data/{client_id}/"

    # Frame reading

    frame_order = {}
    signal_order = {}

    channels = None
    screen_width = None
    screen_height = None
    video_fps = None
    sampling_rate = None

    for file in os.listdir(dir_path):
        if ".json" not in file:
            print(f"Skipping {file}")
            continue

        path = os.path.join(dir_path, file)
        try:
            message_json = json.load(open(path))
        except:
            print(f"{file} is unreadable")

        channels = message_json['channels']
        screen_width = message_json['screenWidth']
        screen_height = message_json['screenHeight']
        video_fps = round(1 / message_json["period"])
        sampling_rate = message_json['samplingRate']

        frame_time = message_json['time']

        signal_window_size = int(message_json["period"] * sampling_rate)
        board_data = np.array(message_json['boardData']).reshape(channels, -1)[:, -2 * signal_window_size:]
        signal_order[frame_time] = board_data

        image_data = np.array(
            message_json['videoFrame']
        ).reshape(screen_height, screen_width, 3).astype(np.uint8)[:, :, ::-1]
        frame_order[frame_time] = image_data

    # Video restoring
    out_video = cv2.VideoWriter(
        f'{client_id}_tmp.mp4', 
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
    os.system(f"ffmpeg -i {client_id}_tmp.mp4 -vcodec libx264 -f mp4 -y {client_id}.mp4")

    # Signal restoring

    previous_time = 0
    previous_samples = 0
    board_data_sorted = []

    for time, board_data in sorted(signal_order.items()):
        expected_samples = int(time * sampling_rate)
        window_size = expected_samples - previous_samples

        board_data_sorted.append(board_data[:, -window_size:])
        previous_samples += window_size
        previous_time = time

    board_data_concat = np.hstack(board_data_sorted)

    print("Board data duration:", board_data_concat.shape[-1] / sampling_rate)
    # TODO add info
    board_data_df = pd.DataFrame(board_data_concat.T)
    board_data_df['time'] = board_data_df.index / sampling_rate
    board_data_df.to_csv(f'{client_id}.csv')

    # import matplotlib.pyplot as plt
    # plt.plot(board_data_concat[0, :])
    # plt.show()

    # Statistics calculation

    # Events restoring

    events_database = f'./data/{client_id}/events.db'
    conn = sqlite3.connect(events_database)
    events_df = pd.read_sql("""
        SELECT 
            game_time AS start_sec,
            game_time + 0.1 AS end_sec,
            type
        FROM events
        ORDER BY game_time
    """, conn)
    events_df.to_csv(f'{client_id}-events.csv')

    # import pdb
    # pdb.set_trace()
