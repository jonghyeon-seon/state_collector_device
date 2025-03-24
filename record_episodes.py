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
            print("Episode recording failed. Exiting program.")
            break
        
        user_choice = input("Press enter to save or type 'del' to delete: ").strip().lower()
        episode_dir = os.path.join(DATASET_PATH, f"epi_{idx:06d}")
        if user_choice == "del":
            shutil.rmtree(episode_dir)
            print(f"Episode {idx} has been deleted.")
        else:
            print(f"Episode {idx} has been saved.")
        
        next_choice = input("Press enter to record the next episode or type 'exit' to quit: ").strip().lower()
        if next_choice == "exit":
            print("Exiting program.")
            break

if __name__ == "__main__":
    main()
