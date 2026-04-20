import json
import time

# Usage
input_file = '/home/ivob/Projects/llm_engineering/project/data/raw_data.json'
output_file = '/home/ivob/Projects/llm_engineering/project/data/transformed_data.json'

events = []

def read_events():
    with open(input_file, 'r') as f:
        events = [json.loads(line) for line in f]
    return events

def transform_event(event, base_timestamp=None):
    if base_timestamp is None:
        base_timestamp = int(time.time())

    if 'data' in event:
        #only run if array
        if isinstance(event['data'], list): 
            # Extract node ID, which is the first element in the data list
            node_id = event['data'][0]
            
            # Extract the specific attribute and its value
            attribute_data = event['data'][1]
            attribute_id = list(attribute_data.keys())[0]
            attribute_type = list(attribute_data[attribute_id].keys())[0]
            
            # Determine the value based on attribute type
            if attribute_type == 'TemperatureMeasurement':
                value = attribute_data[attribute_id][attribute_type]['MeasuredValue']
            elif attribute_type == 'RelativeHumidityMeasurement':
                value = attribute_data[attribute_id][attribute_type]['MeasuredValue']
            elif attribute_type == 'OnOff':
                value = attribute_data[attribute_id][attribute_type]['OnOff']
            elif attribute_type == 'OccupancySensing':
                value = attribute_data[attribute_id][attribute_type]['Occupancy']
            else:
                value = None

            # Generate output dictionary
            output = {
                'timestamp': base_timestamp + (hash(json.dumps(event)) % 1000),
                'room': 'kitchen',
                'nodeId': node_id
            }
            
            # Add specific attribute to output
            if attribute_type == 'TemperatureMeasurement':
                output['temperature'] = value
            elif attribute_type == 'RelativeHumidityMeasurement':
                output['humidity'] = value
            elif attribute_type == 'OnOff':
                output['onOff'] = value
            elif attribute_type == 'OccupancySensing':
                output['occupancy'] = value
        else:
            output = None 
    else:
        output = None 

    return output

# Sample usage
events = read_events()

transformed_events = [transform_event(event) for event in events]
for event in transformed_events:
    if event is not None:
        print(json.dumps(event))