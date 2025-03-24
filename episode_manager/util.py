import cv2
import os
from playsound import playsound

def get_stereo_camera():
    """USB로 연결된 스테레오 카메라를 찾는다. (해상도 2560 픽셀 가정)"""
    max_index = 3
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame.shape[1] == 2560:
                return cap
    return None

def play_sound(sound_file):
    """사운드 파일을 재생한다."""
    try:
        playsound(sound_file)
    except Exception as e:
        print(f"사운드 재생 에러: {e}")

def get_next_episode_index(base_path):
    """base_path 내에서 사용 가능한 다음 episode index를 반환한다."""
    idx = 0
    while os.path.exists(os.path.join(base_path, f"epi_{idx:06d}")):
        idx += 1
    return idx