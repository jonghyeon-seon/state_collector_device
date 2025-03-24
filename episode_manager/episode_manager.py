import cv2
import os
import time
import json
from playsound import playsound
import episode_manager.util as util
import episode_manager.tactile as tactile

class EpisodeRecorder:
    """
    에피소드 녹화를 담당하는 클래스.
    초기화 단계, 녹화 단계, 종료 및 데이터 저장 단계를 메서드로 분리하여 관리.
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
        """카메라와 비디오 라이터를 초기화하는 단계"""
        self.cap = util.get_stereo_camera()
        if not self.cap:
            raise RuntimeError("스테레오 카메라를 찾을 수 없습니다.")
        
        ret, frame = self.cap.read()
        if not ret:
            self.cap.release()
            raise RuntimeError("카메라에서 프레임을 읽지 못했습니다.")
        
        self.height, width, _ = frame.shape
        self.half_width = width // 2
        
        self.left_writer = cv2.VideoWriter(self.left_video_path, self.fourcc, self.fps, (self.half_width, self.height))
        self.right_writer = cv2.VideoWriter(self.right_video_path, self.fourcc, self.fps, (self.half_width, self.height))
    
    def record(self):
        """녹화 시간 동안 카메라 프레임과 촉각 데이터를 수집하여 저장"""
        start_time = time.time()
        while time.time() - start_time < self.record_duration:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: 프레임 읽기 실패")
                break
            # 스테레오 프레임을 좌/우로 분리
            left_frame = frame[:, :self.half_width]
            right_frame = frame[:, self.half_width:]
            self.left_writer.write(left_frame)
            self.right_writer.write(right_frame)
            
            # 촉각 센서 데이터 수집 및 파싱
            tactile_raw = tactile.get_tactile_stream()
            tactile_parsed = tactile.parse_tactile_data(tactile_raw)
            self.tactile_data_list.append(tactile_parsed)
            
            time.sleep(1.0 / self.fps)
    
    def cleanup_resources(self):
        """카메라와 비디오 라이터 자원을 해제"""
        if self.cap:
            self.cap.release()
        if self.left_writer:
            self.left_writer.release()
        if self.right_writer:
            self.right_writer.release()
    
    def save_tactile_data(self):
        """수집된 촉각 데이터를 JSON 파일로 저장"""
        with open(self.tactile_json_path, "w") as f:
            json.dump(self.tactile_data_list, f)

class EpisodeManager:
    """
    에피소드 폴더 생성 및 녹화 실행, 그리고 사용자의 저장/삭제 선택을 관리하는 클래스
    """
    def __init__(self, base_path, start_sound, end_sound, fps=20.0, record_duration=4.0):
        self.base_path = base_path
        self.start_sound = start_sound
        self.end_sound = end_sound
        self.fps = fps
        self.record_duration = record_duration
        if not os.path.exists(base_path):
            os.makedirs(base_path)
    
    def get_next_episode_dir(self):
        """다음 사용 가능한 episode 폴더를 생성하고, index와 폴더 경로를 반환"""
        idx = util.get_next_episode_index(self.base_path)
        episode_dir = os.path.join(self.base_path, f"epi_{idx:06d}")
        os.makedirs(episode_dir)
        return idx, episode_dir
    
    def run_episode(self):
        """하나의 에피소드를 녹화하는 전체 과정을 실행"""
        idx, episode_dir = self.get_next_episode_dir()
        print("\n================")
        print(f"[Episode {idx}]")
        input("준비되었으면 enter를 눌러주세요: ")
        
        print("녹화 준비")
        util.play_sound(self.start_sound)
        print("녹화 시작")
        
        recorder = EpisodeRecorder(episode_dir, self.record_duration, self.fps)
        try:
            recorder.prepare_resources()
        except Exception as e:
            print(f"자원 준비 실패: {e}")
            return False, idx
        
        recorder.record()
        recorder.cleanup_resources()
        recorder.save_tactile_data()
        
        print("녹화 종료")
        util.play_sound(self.end_sound)
        print("================")
        
        return True, idx