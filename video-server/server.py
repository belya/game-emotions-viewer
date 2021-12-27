from time import sleep
import paho.mqtt.client as mqtt
import json
import time
import sqlite3
import pandas as pd


def on_message(client, userdata, message):
    message_json = json.loads(
        str(message.payload.decode("utf-8"))
    )
    client_id = "mock-session"

    if 'frames' in message.topic:
        on_frame_message(client_id, message_json)

    elif 'events' in message.topic:
        on_event_message(client_id, message_json)


def on_frame_message(client_id, message_json):
    print(f"Receiving FRAME message from {client_id}")
    message_time = int(message_json['time'] * 1000)
    message_path = f'./data/{client_id}/frame-{message_time}.json'

    json.dump(message_json, open(message_path, 'w'))


def on_event_message(client_id, message_json):
    print(f"Receiving EVENT message from {client_id}")
    events_database = f'./data/{client_id}/events.db'
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


client = mqtt.Client('server-client')
client.connect('localhost')

client.subscribe("/signal/frames")
client.subscribe("/signal/events")

client.on_message = on_message
client.loop_forever()
