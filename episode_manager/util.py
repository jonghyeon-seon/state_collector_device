import cv2
import os
from playsound import playsound


def get_stereo_camera():
    """Find the stereo camera connected to the USB."""
    max_index = 3
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame.shape[1] == 2560:
                return cap
    return None

def play_sound(sound_file):
    try:
        playsound(sound_file)
    except Exception as e:
        print(f"Sound playback error: {e}")

def get_next_episode_index(base_path):
    idx = 0
    while os.path.exists(os.path.join(base_path, f"epi_{idx:06d}")):
        idx += 1
    return idx