import time
import json
from confluent_kafka import Producer

conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)

def delivery_report(err, msg):
    if err:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered: {msg.value().decode("utf-8")}')

events = [
    {"event": "kickoff", "time": "00:00"},
    {"event": "goal", "team": "Barcelona", "player": "Lewandowski", "time": "05:12"},
    {"event": "yellow_card", "player": "Messi", "time": "12:34"},
    {"event": "foul", "player": "Ramos", "time": "18:49"},
    {"event": "substitution", "player_out": "Xavi", "player_in": "Gavi", "time": "45:00"},
]

for event in events:
    event_json = json.dumps(event)
    producer.produce('video_events', value=event_json, callback=delivery_report)
    producer.poll(0)
    time.sleep(2)  # simulate delay between events

producer.flush()
