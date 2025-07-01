from confluent_kafka import Consumer
import json

conf = {'bootstrap.servers': 'localhost:9092', 'group.id': 'commentary', 'auto.offset.reset': 'earliest'}
consumer = Consumer(conf)
consumer.subscribe(['video_events'])

def generate_commentary(event):
    if event["event"] == "goal":
        return f"GOAL! {event.get('player', 'Unknown')} scores for {event.get('team', 'Unknown')} at {event['time']}!"
    elif event["event"] == "yellow_card":
        return f"Yellow card shown to {event['player']} at {event['time']}."
    elif event["event"] == "kickoff":
        return "The match has kicked off!"
    elif event["event"] == "substitution":
        return f"Substitution: {event['player_out']} off, {event['player_in']} on at {event['time']}."
    else:
        return f"{event['event'].capitalize()} occurred at {event['time']}."

try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None: continue
        if msg.error(): continue

        raw = msg.value().decode("utf-8")
        event = json.loads(raw)
        commentary = generate_commentary(event)
        print(f"📣 {commentary}")
except KeyboardInterrupt:
    consumer.close()
