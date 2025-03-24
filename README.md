# Record Episodes

This repository contains the `record_episodes.py` script, which leverages the `EpisodeManager` class to record and manage episodes. Each episode is recorded with a predefined frame rate and duration, accompanied by audio cues at the start and end of the recording.

## Features

- **Episode Recording:** Records episodes with a set frame rate (`fps=20.0`) and duration (`record_duration=4.0` seconds).
- **Audio Cues:** Plays a start sound (`assets/sounds/start_sound.mp3`) and an end sound (`assets/sounds/end_sound.mp3`) using the `playsound` package.
- **User Interaction:** Prompts the user after each recording to either save or delete the episode.
- **Session Management:** Continues recording episodes until the user decides to exit.

## Prerequisites

- **Python 3.x:** Ensure you have a compatible Python version installed.
- **playsound Package:** This script requires the `playsound` package. Install it using pip:

  ```bash
  pip install playsound

## Installation

- Clone the Repository:

  ```bash
  git clone https://your-repository-url.git
  cd your-repository-directory

- Install Dependencies:
  ```bash
  pip install playsound
  
## Usage
- To run the episode recording script, execute:

  ```bash
  python record_episodes.py

## How It Works
### Initialization
  The script sets the dataset path, start sound, and end sound.
  An instance of EpisodeManager is created with parameters like frame rate and recording duration.
  Recording Loop
  Displays an introductory message from the EpisodeManager.
  Begins recording an episode.
  Once the recording finishes, the user is prompted:
  - Save Episode: Simply press Enter.
  - Delete Episode: Type del to remove the episode directory.
  The user is then asked whether to record the next episode or exit the program.
### Exit
  If the user types exit at the prompt, the script terminates.
