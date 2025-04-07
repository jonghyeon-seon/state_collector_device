import cv2
import os
import time
import json
import random
import shutil
import threading
from queue import Queue

import numpy as np 
import episode_manager.utils as utils
from hday import Robot  

import warnings
warnings.filterwarnings("ignore")


class EpisodeRecorder:
    def __init__(self, episode_dir, record_duration=4.0, fps=20.0, tactile_port="/dev/ttyACM0"):
        self.episode_dir = episode_dir
        self.record_duration = record_duration
        self.fps = fps
        self.tactile_port = tactile_port
        self.cap = None
        self.left_writer = None
        self.right_writer = None
        self.tactile_data_list = []
        self.half_width = None
        self.height = None
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.left_video_path = os.path.join(episode_dir, "left_video.mp4")
        self.right_video_path = os.path.join(episode_dir, "right_video.mp4")
        self.tactile_json_path = os.path.join(episode_dir, "tactile.json")
        
        self.latest_tactile = {}  
        self.tactile_lock = threading.Lock()
        self.tactile_stop_event = threading.Event()
        self.start_time = None 

    def __enter__(self):
        self.prepare_resources()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup_resources()
        self.save_tactile_data()

    def prepare_resources(self):
        self.cap = utils.get_stereo_camera()
        if not self.cap:
            raise RuntimeError("Stereo camera not found.")
        
        ret, frame = self.cap.read()
        if not ret:
            self.cap.release()
            raise RuntimeError("Failed to read a frame from the camera.")
        
        self.height, width, _ = frame.shape
        self.half_width = width // 2
        
        self.left_writer = cv2.VideoWriter(self.left_video_path, self.fourcc, self.fps, (self.half_width, self.height))
        self.right_writer = cv2.VideoWriter(self.right_video_path, self.fourcc, self.fps, (self.half_width, self.height))
    
    def camera_worker(self, frame_queue):
        while True:
            item = frame_queue.get()
            if item is None:  # 종료 신호 수신 시 종료.
                break
            left_frame, right_frame = item
            self.left_writer.write(left_frame)
            self.right_writer.write(right_frame)
    
    def tactile_worker(self, init_tactile_table=None):
        try:
            with Robot(self.tactile_port) as robot:
                robot.request_robot_enable(True)
                while not self.tactile_stop_event.is_set():
                    sensor_bypass_id, sensor_bypass_data = robot.getSensorBypassPacket()
                    # 센서 id가 128~133인 경우에만 처리 (각각 [16][3] 배열로 구성됨)
                    if sensor_bypass_id is not None and 128 <= sensor_bypass_id <= 139:
                        tactile_timestamp = time.perf_counter() - self.start_time
                        with self.tactile_lock:
                            adjusted_data = sensor_bypass_data
                            if init_tactile_table is not None:
                                if sensor_bypass_id in init_tactile_table:
                                    adjusted_data = sensor_bypass_data - init_tactile_table[sensor_bypass_id]

                            self.latest_tactile[sensor_bypass_id] = {
                                "data": adjusted_data,  # [16][3] 데이터
                                "timestamp": tactile_timestamp
                            }
                    time.sleep(0.001)
        except Exception as e:
            print("Tactile thread encountered error:", e)
            
    def validate_sensors(self, validation_duration=5.0, validation_threshold=6):
        print("Validating sensors...")
        collected_ids = set()
        self.tactile_stop_event.clear()  
        self.start_time = time.perf_counter()
        tactile_thread = threading.Thread(target=self.tactile_worker)
        tactile_thread.daemon = True
        tactile_thread.start()
        
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < validation_duration:
            with self.tactile_lock:
                collected_ids.update(self.latest_tactile.keys())
            time.sleep(0.01)
        
        self.tactile_stop_event.set()
        tactile_thread.join()
        
        expected_ids = set(range(128, 140))  # 128~139
        missing_ids = expected_ids - collected_ids
        if missing_ids:
            print("     => Validation failed. Missing sensors:", missing_ids)
            return False, {}
        
        #check sensor init data with threshold
        CHECK_THRESHOLD = validation_threshold
        init_tactile_table = {}
        for id in [134, 135, 136, 137, 138, 139]:
            data = self.latest_tactile[id]["data"]
            if not np.all(np.abs(data) < CHECK_THRESHOLD):
                init_tactile_table[id] = data
                
                
        return True, init_tactile_table
        
        
    
    def record(self, init_tactile_table):
        frame_queue = Queue(maxsize=10)
        camera_thread = threading.Thread(target=self.camera_worker, args=(frame_queue,))
        camera_thread.daemon = True
        camera_thread.start()

        tactile_thread = threading.Thread(target=self.tactile_worker, args=(init_tactile_table,))
        tactile_thread.daemon = True
        tactile_thread.start()
        
        self.start_time = time.perf_counter()
        fps_interval = 1.0 / self.fps
        next_frame_time = self.start_time
        
        while time.perf_counter() - self.start_time < self.record_duration:
            now = time.perf_counter()
            if now < next_frame_time:
                while time.perf_counter() < next_frame_time:
                    pass
            current_timestamp = time.perf_counter() - self.start_time
            next_frame_time += fps_interval
            
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to read frame")
                break
            
            left_frame = frame[:, :self.half_width]
            right_frame = frame[:, self.half_width:]
            
            frame_queue.put((left_frame, right_frame))
            
            with self.tactile_lock:
                tactile_snapshot = self.latest_tactile.copy()
            
            self.tactile_data_list.append({
                "timestamp": f'{current_timestamp:.2f}',
                "tactile": tactile_snapshot
            })
        
        self.tactile_stop_event.set()
        tactile_thread.join()
        
        frame_queue.put(None)
        camera_thread.join()
    
    def cleanup_resources(self):
        if self.cap:
            self.cap.release()
        if self.left_writer:
            self.left_writer.release()
        if self.right_writer:
            self.right_writer.release()
    
    def save_tactile_data(self):
        with open(self.tactile_json_path, "w") as f:
            json.dump(self.tactile_data_list, f)


class EpisodeManager:
    def __init__(self, base_path, start_sound_path, end_sound_path, tactile_port, fps=20.0, record_duration=4.0):
        self.base_path = base_path
        self.start_sound_path = start_sound_path
        self.end_sound_path = end_sound_path
        self.start_sound_list = os.listdir(start_sound_path)
        self.end_sound_list = os.listdir(end_sound_path)
        self.fps = fps
        self.record_duration = record_duration
        self.tactile_port = tactile_port
        self.intro_message = f"""
            Notice: The recording will automatically stop after {self.record_duration} seconds.
            It will record at {self.fps} fps.
            If you wish to delete the recording, type 'del'.
            To continue, press 'enter'.
            """
        if not os.path.exists(base_path):
            os.makedirs(base_path)
    
    def get_next_episode_dir(self):
        idx = utils.get_next_episode_index(self.base_path)
        episode_dir = os.path.join(self.base_path, f"epi_{idx:06d}")
        os.makedirs(episode_dir)
        return idx, episode_dir
    
    def _play_start_sounds(self):
        utils.play_sound(os.path.join(self.start_sound_path, self.start_sound_list[random.randint(0, len(self.start_sound_list) - 1)]))
        
    def _play_end_sounds(self):
        utils.play_sound(os.path.join(self.end_sound_path, self.end_sound_list[random.randint(0, len(self.end_sound_list) - 1)]))
    
    def run_episode(self):
        idx, episode_dir = self.get_next_episode_dir()
        print("\n================")
        print(f"[Episode {idx}]")
        input("Press enter when ready: ")
        
        print("     => Preparing for recording")
        try:
            with EpisodeRecorder(episode_dir, self.record_duration, self.fps, tactile_port=self.tactile_port) as recorder:
                success, init_tactile_table = recorder.validate_sensors(validation_duration=2.0, validation_threshold=10)
                if not success:
                    raise RuntimeError("Validation failed. Please check the sensors.")
                
                self._play_start_sounds()
                print("     => Starting recording")
                recorder.record(init_tactile_table)
                
        except Exception as e:
            print(f"Recording failed: {e}")
            shutil.rmtree(episode_dir)
            return False, idx

        print("     => Recording finished")
        self._play_end_sounds()
        print("================")
        
        return True, idx
