import cv2
import os
import time
import json
import episode_manager.util as util
import episode_manager.tactile as tactile


class EpisodeRecorder:
    """
    Class responsible for recording an episode.
    Manages the initialization, recording, termination, and data saving phases through separate methods.
    """
    def __init__(self, episode_dir, record_duration=4.0, fps=20.0):
        self.episode_dir = episode_dir
        self.record_duration = record_duration
        self.fps = fps
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
    
    def prepare_resources(self):
        """Initialize the camera and the video writers."""
        self.cap = util.get_stereo_camera()
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
    
    def record(self):
        """Collect and save camera frames and tactile data for the duration of the recording."""
        start_time = time.time()
        while time.time() - start_time < self.record_duration:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to read frame")
                break
            # Separate the stereo frame into left and right frames
            left_frame = frame[:, :self.half_width]
            right_frame = frame[:, self.half_width:]
            self.left_writer.write(left_frame)
            self.right_writer.write(right_frame)
            
            # Collect and parse the tactile sensor data
            tactile_raw = tactile.get_tactile_stream()
            tactile_parsed = tactile.parse_tactile_data(tactile_raw)
            self.tactile_data_list.append(tactile_parsed)
            
            time.sleep(1.0 / self.fps)
    
    def cleanup_resources(self):
        """Release the camera and the video writer resources."""
        if self.cap:
            self.cap.release()
        if self.left_writer:
            self.left_writer.release()
        if self.right_writer:
            self.right_writer.release()
    
    def save_tactile_data(self):
        """Save the collected tactile data as a JSON file."""
        with open(self.tactile_json_path, "w") as f:
            json.dump(self.tactile_data_list, f)

class EpisodeManager:
    """
    Class that manages the creation of episode folders, execution of recordings,
    and user decisions to save or delete the recordings.
    """
    def __init__(self, base_path, start_sound, end_sound, fps=20.0, record_duration=4.0):
        self.base_path = base_path
        self.start_sound = start_sound
        self.end_sound = end_sound
        self.fps = fps
        self.record_duration = record_duration
        self.intro_message = f"""
            Notice: The recording will automatically stop after {self.record_duration} seconds.
            It will record at {self.fps} fps.
            If you wish to delete the recording, type 'del'.
            To continue, press 'enter'.
            """
        if not os.path.exists(base_path):
            os.makedirs(base_path)
    
    def get_next_episode_dir(self):
        """Generate the next available episode folder and return its index and path."""
        idx = util.get_next_episode_index(self.base_path)
        episode_dir = os.path.join(self.base_path, f"epi_{idx:06d}")
        os.makedirs(episode_dir)
        return idx, episode_dir
    
    def run_episode(self):
        """Execute the complete process of recording a single episode."""
        idx, episode_dir = self.get_next_episode_dir()
        print("\n================")
        print(f"[Episode {idx}]")
        input("Press enter when ready: ")
        
        print("Preparing for recording")
        util.play_sound(self.start_sound)
        print("Starting recording")
        
        recorder = EpisodeRecorder(episode_dir, self.record_duration, self.fps)
        try:
            recorder.prepare_resources()
        except Exception as e:
            print(f"Resource preparation failed: {e}")
            return False, idx
        
        recorder.record()
        recorder.cleanup_resources()
        recorder.save_tactile_data()
        
        print("Recording finished")
        util.play_sound(self.end_sound)
        print("================")
        
        return True, idx