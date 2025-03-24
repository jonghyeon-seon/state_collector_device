import os

def get_tactile_stream():
    return os.urandom(576)

def parse_tactile_data(data):
    """576 bytes data to [left/right][24][4][3] 3D list"""
    if len(data) != 576:
        raise ValueError("Tactile data length is not valid.")
    left_data = data[:288]
    right_data = data[288:]
    
    def bytes_to_nested_list(b):
        nested = []
        offset = 0
        for i in range(24):
            row = []
            for j in range(4):
                sensor = []
                for k in range(3):
                    sensor.append(b[offset])
                    offset += 1
                row.append(sensor)
            nested.append(row)
        return nested

    return {"left": bytes_to_nested_list(left_data),
            "right": bytes_to_nested_list(right_data)}