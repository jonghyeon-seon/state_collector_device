import os
import shutil
from episode_manager import EpisodeManager
import argparse

def main():
    parser = argparse.ArgumentParser(description='Record episodes for a dataset.')
    parser.add_argument('--save_path', type=str, default='dataset/holiworld', help='Path to save the dataset')
    parser.add_argument('--start_sound_path', type=str, default='assets/sounds/start', help='Path to the start sound')
    parser.add_argument('--end_sound_path', type=str, default='assets/sounds/end', help='Path to the end sound')
    parser.add_argument('--tactile_port', type=str, default='/dev/ttyACM0', help='Path to the tactile port')
    args = parser.parse_args()
    
    SAVE_PATH = args.save_path
    START_SOUND_PATH = args.start_sound_path
    END_SOUND_PATH = args.end_sound_path
    TACTILE_PORT = args.tactile_port
    
    episode_manager = EpisodeManager(
        SAVE_PATH, 
        START_SOUND_PATH, 
        END_SOUND_PATH, 
        tactile_port=TACTILE_PORT,
        fps=20.0, 
        record_duration=3.0
    )
    
    print(episode_manager.intro_message)
    
    while True:
        success, idx = episode_manager.run_episode()
        if not success:
            print("Episode recording failed. Exiting program.")
            break
        
        user_choice = input("Press enter to save or type 'del' to delete: ").strip().lower()
        episode_dir = os.path.join(SAVE_PATH, f"epi_{idx:06d}")
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
