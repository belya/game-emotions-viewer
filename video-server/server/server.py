import os

from time import sleep
import paho.mqtt.client as mqtt
import json
import time
import sqlite3
import pandas as pd
import numpy as np
import base64

import cv2


data_dir = '../data'

def init_session(client_id):
    if not os.path.exists(f'{data_dir}/{client_id}'):
        os.system(f'mkdir {data_dir}/{client_id}')
        os.system(f'mkdir {data_dir}/{client_id}/boardFrame')
        os.system(f'mkdir {data_dir}/{client_id}/screenVideoFrame')
        os.system(f'mkdir {data_dir}/{client_id}/webCamFrame')
        os.system(f'mkdir {data_dir}/{client_id}/jsonFrame')

        events_database = f'{data_dir}/{client_id}/events.db'
        conn = sqlite3.connect(events_database)
        
        cursor = conn.cursor()
        # TODO time and type as pk
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS events (
                ID          INTEGER PRIMARY KEY     AUTOINCREMENT,
                game_time   FLOAT               NOT NULL,
                type        CHAR(50)            NOT NULL
            )
        """)

        conn.close()

def on_message(client, userdata, message):
    message_json = json.loads(
        str(message.payload.decode("utf-8"))
    )
    client_id = message_json['clientId'] # Fix the error!
    init_session(client_id)

    if 'frames' in message.topic:
        on_frame_message(client_id, message_json)

    elif 'events' in message.topic:
        on_event_message(client_id, message_json)


def preprocess_video_frame(client_id, message_json, field):
    sub_message_json = message_json[field]
    message_time = message_json['time_int']
    # Save image separately
    screen_width = sub_message_json['screenWidth']
    screen_height = sub_message_json['screenHeight']
    image_path = f"{data_dir}/{client_id}/{field}/{field}-{message_time}.png"

    video_frame_base64 = sub_message_json['videoFrameBase64'].encode('utf-8')
    video_frame_bytes = base64.decodebytes(video_frame_base64)
    video_frame = np.frombuffer(
        video_frame_bytes, 
        np.uint8
    ).reshape(screen_height, screen_width, 4).astype(np.uint8)[:, :, ::-1][:, :, 1:]
    video_frame = np.flipud(video_frame)

    cv2.imwrite(image_path, video_frame)
    sub_message_json['videoFrameBase64'] = image_path


def preprocess_board_frame(client_id, message_json, field):
    sub_message_json = message_json[field]
    message_time = message_json['time_int']

    board_data_path = f"{data_dir}/{client_id}/{field}/{field}-{message_time}.npy"
    board_data = sub_message_json['boardData']

    np.save(board_data_path, board_data)
    sub_message_json['boardData'] = board_data_path


def on_frame_message(client_id, message_json):
    message_time = int(message_json['time'] * 1000)
    message_json['time_int'] = message_time

    message_path = f'{data_dir}/{client_id}/jsonFrame/frame-{message_time}.json'
    print(f"Receiving FRAME message from {client_id}, {message_time}")

    preprocess_video_frame(client_id, message_json, 'webCamFrame')
    preprocess_video_frame(client_id, message_json, 'screenVideoFrame')
    preprocess_board_frame(client_id, message_json, 'boardFrame')
    
    json.dump(message_json, open(message_path, 'w'))


def on_event_message(client_id, message_json):
    print(f"Receiving EVENT message from {client_id}")
    events_database = f'{data_dir}/{client_id}/events.db'
    conn = sqlite3.connect(events_database)

    cursor.execute("""
        INSERT INTO events (game_time, type)
        VALUES (?, ?)
    """, [message_json['time'], message_json['type']])

    print(pd.read_sql("""
        SELECT *
        FROM events
        ORDER BY game_time DESC
        LIMIT 1
    """, conn))

    cursor.close()
    conn.commit()
    conn.close()  


client = mqtt.Client('server-client', clean_session=True)
client.connect('localhost')

client.subscribe("/signal/frames", qos=2)
client.subscribe("/signal/events", qos=2)

client.on_message = on_message
print('Server is ready')
client.loop_forever()
