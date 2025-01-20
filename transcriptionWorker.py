import subprocess
from PySide6.QtCore import QThread, Signal
from whisper import load_model
import torch
import os
from pathlib import Path

class TranscriptionWorker(QThread):
    finished = Signal(str)
    progress = Signal(str)
    error = Signal(str)

    def __init__(self, video_file):
        super().__init__()
        self.video_file = video_file
        print(f"Initialized with video file: {video_file}")  # Debug print

    def run(self):
        try:
            # Extract audio
            print("Starting audio extraction...")  # Debug print
            self.progress.emit("Extracting audio...")

            # Get the current working directory of the project
            project_dir = Path(os.getcwd())  # Current project directory
            video_name = Path(self.video_file).stem  # Get video filename without extension
            audio_file = project_dir / f"{video_name}.mp3"  # Save in project directory

            print(f"Running ffmpeg command to save {audio_file}")  # Debug print
            subprocess.run(
                ["ffmpeg", "-i", self.video_file, "-q:a",
                 "0", "-map", "a", str(audio_file)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("Audio extraction complete")  # Debug print

            # Transcribe audio
            print("Loading Whisper model...")  # Debug print
            self.progress.emit("Loading Whisper model...")
            model = load_model(
                "tiny", device="cuda" if torch.cuda.is_available() else "cpu")
            
            # Debug print
            print(f"Using device: {'cuda' if torch.cuda.is_available() else 'cpu'}")

            self.progress.emit("Transcribing audio...")
            print("Starting transcription...")  # Debug print
            result = model.transcribe(str(audio_file))

            # Format transcription and emit progress
            transcription = ""
            total_segments = len(result["segments"])
            for index, segment in enumerate(result["segments"]):
                start = segment["start"]
                end = segment["end"]
                text = segment["text"]
                transcription += f"[{start:.2f} - {end:.2f}] {text}\n"

                # Emit progress update
                progress_percentage = (index + 1) / total_segments * 100
                self.progress.emit(str(int(progress_percentage)))

            print("Emitting finished signal")  # Debug print
            print(transcription)
            self.finished.emit(transcription)

        except Exception as e:
            print(f"Error occurred: {str(e)}")  # Debug print
            self.progress.emit(f"Error: {str(e)}")
            self.error.emit(str(e))
