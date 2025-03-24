import os

def get_tactile_stream():
    """촉각 센서 스트림 데이터를 시뮬레이션(576바이트)"""
    return os.urandom(576)

def parse_tactile_data(data):
    """576바이트 데이터를 [left/right][24][4][3] 구조의 3차원 리스트로 파싱"""
    if len(data) != 576:
        raise ValueError("데이터 길이가 올바르지 않습니다.")
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