import os
import shutil
from episode_manager import EpisodeManager
def main():
    DATASET_PATH = "dataset/holiworld"
    RECORDING_START_SOUND = "assets/sounds/start_sound.mp3"
    RECORDING_END_SOUND = "assets/sounds/end_sound.mp3"
    
    episode_manager = EpisodeManager(
        DATASET_PATH, 
        RECORDING_START_SOUND, 
        RECORDING_END_SOUND, 
        fps=20.0, 
        record_duration=4.0
        )
    
    print(episode_manager.intro_message)    
    while True:
        success, idx = episode_manager.run_episode()
        if not success:
            print("에피소드 녹화에 실패했습니다. 프로그램을 종료합니다.")
            break
        
        user_choice = input("저장하려면 enter를, 삭제하려면 'del'을 입력하세요: ").strip().lower()
        episode_dir = os.path.join(DATASET_PATH, f"epi_{idx:06d}")
        if user_choice == "del":
            shutil.rmtree(episode_dir)
            print(f"Episode {idx}가 삭제되었습니다.")
        else:
            print(f"Episode {idx}가 저장되었습니다.")
        
        next_choice = input("다음 에피소드를 녹화 -> enter \n종료 -> 'exit' 입력: ").strip().lower()
        if next_choice == "exit":
            print("프로그램을 종료합니다.")
            break

if __name__ == "__main__":
    main()
