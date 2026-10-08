import random
import json
from datetime import datetime, timedelta

def generate_iot_data(num_entries=100):
    rooms = ['livingroom', 'hall', 'bedroom', 'bathroom', 'kitchen', 'garage', 'study']
    node_ids = [1, 2, 3]
    custom_events = [
        {"type": "fridge_opened", "room": "kitchen"},
        {"type": "kitchen_light", "room": "kitchen"},
        {"type": "pillbox_opened", "room": "bedroom"}
    ]
    
    base_timestamp = int(datetime.now().timestamp())
    data_entries = []

    for _ in range(num_entries):
        # Randomly choose between standard sensor data and custom events
        if random.random() < 0.7:  # 70% chance of standard sensor data
            room = random.choice(rooms)
            node_id = random.choice(node_ids)
            timestamp = base_timestamp - random.randint(0, 3600)
            
            entry_type = random.choice(['temperature', 'occupancy', 'onOff', 'humidity'])
            
            if entry_type == 'temperature':
                value = random.randint(1500, 3000)
                entry = {
                    "timestamp": timestamp,
                    "room": room,
                    "nodeId": node_id,
                    "temperature": value
                }
            elif entry_type == 'occupancy':
                value = random.randint(0, 1)
                entry = {
                    "timestamp": timestamp,
                    "room": room,
                    "nodeId": node_id,
                    "occupancy": value
                }
            elif entry_type == 'onOff':
                value = random.choice([True, False])
                entry = {
                    "timestamp": timestamp,
                    "room": room,
                    "nodeId": node_id,
                    "onOff": value
                }
            elif entry_type == 'humidity':
                value = random.randint(3000, 7000)
                entry = {
                    "timestamp": timestamp,
                    "room": room,
                    "nodeId": node_id,
                    "humidity": value
                }
        else:  # 30% chance of custom event
            event = random.choice(custom_events)
            timestamp = base_timestamp - random.randint(0, 3600)
            
            entry = {
                "timestamp": timestamp,
                "room": event["room"],
                "event": event["type"]
            }
        
        data_entries.append(entry)
    
    return data_entries

# Generate data
iot_data = generate_iot_data(100)

# Print as JSON
for entry in iot_data:
    print(json.dumps(entry))