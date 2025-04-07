import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import threading
import time

# =============================================================================
# 기존 파일 기반 시각화 코드
# =============================================================================

def load_tactile_data(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    # 촉각 데이터가 있는 프레임만 필터링
    frames = [d for d in data if d.get("tactile") and d["tactile"]]
    return frames

def draw_sensor_patch(ax, sensor_data, origin, sensor_name, cell_size=2):
    # 16x3 데이터를 4x4x3 배열로 재구성
    grid = np.array(sensor_data).reshape((4, 4, 3))
    x0, y0 = origin
    patch_width = 4 * cell_size
    patch_height = 4 * cell_size

    # 패치 외곽 및 셀 경계 그리기
    for i in range(5):
        ax.plot([x0, x0 + patch_width], [y0 + i * cell_size, y0 + i * cell_size], 'k-', linewidth=0.5)
        ax.plot([x0 + i * cell_size, x0 + i * cell_size], [y0, y0 + patch_height], 'k-', linewidth=0.5)

    # 각 셀 중앙에 값(여기서는 z채널)을 텍스트로 표시
    for r in range(4):
        for c in range(4):
            display_r = 3 - r  # top row가 위쪽에 오도록 반전
            value_x = grid[r, c, 0] 
            value_y = grid[r, c, 1] 
            value_z = grid[r, c, 2] 
            ax.text(x0 + c * cell_size + cell_size / 2,
                    y0 + display_r * cell_size + cell_size / 2,
                    f"{value_x:.0f}\n{value_y:.0f}\n{value_z:.0f}",
                    ha='center', va='center', fontsize=4)
    # 센서 이름을 패치 상단 중앙에 표시
    ax.text(x0 + patch_width / 2, y0 + patch_height + 0.1,
            sensor_name, ha='center', va='bottom', fontsize=10, fontweight='bold')

def draw_hand(ax, tactile, sensor_ids, sensor_positions, sensor_labels):
    for sid in sensor_ids:
        if sid in tactile:
            sensor_data = tactile[sid]['data']
            origin = sensor_positions[sid]
            label = sensor_labels[sid]
            draw_sensor_patch(ax, sensor_data, origin, label, cell_size=2.5)

def init_hand(ax, xlim, ylim):
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

def animate(frame_idx, frames, ax_right, ax_left, right_sensor_ids, right_positions, right_sensor_labels,
            left_sensor_ids, left_positions, left_sensor_labels, time_text):
    ax_right.clear()
    ax_left.clear()
    init_hand(ax_right, (0, 50), (0, 30))
    init_hand(ax_left, (-50, 0), (0, 30))

    # 현재 프레임의 tactile 데이터 사용
    tactile = frames[frame_idx]["tactile"]
    draw_hand(ax_right, tactile, right_sensor_ids, right_positions, right_sensor_labels)
    ax_right.set_title("Right Hand")
    draw_hand(ax_left, tactile, left_sensor_ids, left_positions, left_sensor_labels)
    ax_left.set_title("Left Hand")

    ts = frames[frame_idx].get("timestamp", 0)
    try:
        ts_float = float(ts)
    except:
        ts_float = 0
    time_text.set_text(f"Timestamp: {ts_float:.2f}")

def animate_tactile_video(frames):
    # 오른손 센서 구성
    right_sensor_ids = ['128', '129', '130', '131', '132', '133']
    right_sensor_labels = {
        '128': 'Thumb',
        '129': 'Index',
        '130': 'Middle',
        '131': 'Ring',
        '132': 'Pinky',
        '133': 'Palm'
    }
    right_positions = {
        '128': (0, 15),
        '129': (10, 15),
        '130': (20, 15),
        '131': (30, 15),
        '132': (40, 15),
        '133': (20, 0)
    }
    # 왼손 센서 구성
    left_sensor_ids = ['134', '135', '136', '137', '138', '139']
    left_sensor_labels = {
        '134': 'Thumb',
        '135': 'Index',
        '136': 'Middle',
        '137': 'Ring',
        '138': 'Pinky',
        '139': 'Palm'
    }
    left_positions = {
        '134': (-10, 15),
        '135': (-20, 15),
        '136': (-30, 15),
        '137': (-40, 15),
        '138': (-50, 15),
        '139': (-30, 0)
    }

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(12, 6))
    init_hand(ax_left, (-10, 4), (-1, 11))
    init_hand(ax_right, (0, 15), (-1, 11))
    time_text = fig.text(0.5, 0.95, '', ha='center', fontsize=12)

    anim = animation.FuncAnimation(fig, animate,
                                   frames=len(frames),
                                   fargs=(frames, ax_right, ax_left,
                                          right_sensor_ids, right_positions, right_sensor_labels,
                                          left_sensor_ids, left_positions, left_sensor_labels,
                                          time_text),
                                   interval=500,
                                   repeat=True)
    plt.show()
    # 비디오로 저장하려면 아래 주석 해제:
    # anim.save('tactile_video.mp4', writer='ffmpeg', fps=2)


# =============================================================================
# 실시간 시각화 기능 (Real-Time Visualization)
# =============================================================================

# 전역 변수 (실시간 센서 데이터 저장용)
live_tactile_lock = threading.Lock()
live_tactile_data = {}

def live_tactile_worker(tactile_port="/dev/ttyACM0", stop_event=None):
    """
    실시간 촉각 센서 데이터를 읽어 전역 딕셔너리 live_tactile_data에 업데이트합니다.
    hday.Robot 클래스를 사용합니다.
    """
    from hday import Robot  # hday 모듈이 환경에 있어야 합니다.
    try:
        with Robot(tactile_port) as robot:
            robot.request_robot_enable(True)
            while not stop_event.is_set():
                sensor_id, sensor_data = robot.getSensorBypassPacket()
                # 센서 id가 128~139인 경우만 처리
                if sensor_id is not None and 128 <= sensor_id <= 139:
                    tactile_timestamp = time.perf_counter()
                    with live_tactile_lock:
                        # key를 문자열로 통일
                        live_tactile_data[str(sensor_id)] = {
                            "data": sensor_data,
                            "timestamp": tactile_timestamp
                        }
                time.sleep(0.001)
    except Exception as e:
        print("Live tactile worker error:", e)

def animate_live(frame_idx, ax_right, ax_left, right_sensor_ids, right_positions, right_sensor_labels,
                 left_sensor_ids, left_positions, left_sensor_labels, time_text):
    ax_right.clear()
    ax_left.clear()
    init_hand(ax_right, (0, 50), (0, 30))
    init_hand(ax_left, (-50, 0), (0, 30))

    # 전역 변수에서 최신 촉각 데이터를 읽어옴
    with live_tactile_lock:
        tactile_snapshot = live_tactile_data.copy()

    draw_hand(ax_right, tactile_snapshot, right_sensor_ids, right_positions, right_sensor_labels)
    ax_right.set_title("Right Hand (Live)")
    draw_hand(ax_left, tactile_snapshot, left_sensor_ids, left_positions, left_sensor_labels)
    ax_left.set_title("Left Hand (Live)")

    # 데이터가 있을 경우 가장 최근 timestamp 표시, 없으면 0
    if tactile_snapshot:
        current_ts = max(val["timestamp"] for val in tactile_snapshot.values())
    else:
        current_ts = 0
    time_text.set_text(f"Timestamp: {current_ts:.2f}")

def animate_live_tactile_video(tactile_port="/dev/ttyACM0"):
    """
    실시간 촉각 데이터를 시각화합니다.
    별도의 스레드에서 센서 데이터를 읽어오며, matplotlib animation으로 업데이트합니다.
    """
    # 오른손 센서 구성
    right_sensor_ids = ['128', '129', '130', '131', '132', '133']
    right_sensor_labels = {
        '128': 'Thumb',
        '129': 'Index',
        '130': 'Middle',
        '131': 'Ring',
        '132': 'Pinky',
        '133': 'Palm'
    }
    right_positions = {
        '128': (0, 15),
        '129': (10, 15),
        '130': (20, 15),
        '131': (30, 15),
        '132': (40, 15),
        '133': (20, 0)
    }
    # 왼손 센서 구성
    left_sensor_ids = ['134', '135', '136', '137', '138', '139']
    left_sensor_labels = {
        '134': 'Thumb',
        '135': 'Index',
        '136': 'Middle',
        '137': 'Ring',
        '138': 'Pinky',
        '139': 'Palm'
    }
    left_positions = {
        '134': (-10, 15),
        '135': (-20, 15),
        '136': (-30, 15),
        '137': (-40, 15),
        '138': (-50, 15),
        '139': (-30, 0)
    }

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(12, 6))
    init_hand(ax_left, (-10, 4), (-1, 11))
    init_hand(ax_right, (0, 15), (-1, 11))
    time_text = fig.text(0.5, 0.95, '', ha='center', fontsize=12)

    # 실시간 촉각 데이터를 읽어오는 스레드 시작
    stop_event = threading.Event()
    tactile_thread = threading.Thread(target=live_tactile_worker, args=(tactile_port, stop_event))
    tactile_thread.daemon = True
    tactile_thread.start()

    anim = animation.FuncAnimation(fig, animate_live,
                                   frames=200,  # 또는 원하는 프레임 수
                                   fargs=(ax_right, ax_left,
                                          right_sensor_ids, right_positions, right_sensor_labels,
                                          left_sensor_ids, left_positions, left_sensor_labels,
                                          time_text),
                                   interval=100,  # 업데이트 간격 (ms)
                                   repeat=True)
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        tactile_thread.join()

# =============================================================================
# 메인 실행부
# =============================================================================
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--filepath', type=str, default='/Users/jhseon_mac/Desktop/projects/scv/dataset/holiworld_s/epi_000104/tactile.json')
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--tactile_port', type=str, default='/dev/ttyACM0')
    args = parser.parse_args()
    
    # 기존 JSON 파일을 읽어 시각화 (파일 기반)
    if args.live:
        animate_live_tactile_video(tactile_port=args.tactile_port)
    else:
        filepath = args.filepath
        frames = load_tactile_data(filepath)
        if frames:
            animate_tactile_video(frames)
        else:
            print("유효한 tactile 데이터 프레임이 없습니다.")
    

