import subprocess
from PySide6.QtCore import QThread, Signal
from whisper import load_model
import torch


class TranscriptionWorker(QThread):
    finished = Signal(str)
    progress = Signal(str)
    error = Signal(str)  # Add error signal

    def __init__(self, video_file):
        super().__init__()
        self.video_file = video_file
        print(f"Initialized with video file: {video_file}")  # Debug print

    def run(self):
        try:
            # Extract audio
            print("Starting audio extraction...")  # Debug print
            self.progress.emit("Extracting audio...")
            audio_file = self.video_file.rsplit('.', 1)[0] + '.mp3'

            print(f"Running ffmpeg command for {
                  self.video_file}")  # Debug print
            subprocess.run(
                ["ffmpeg", "-i", self.video_file, "-q:a",
                    "0", "-map", "a", audio_file],
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
            print(f"Using device: {
                  'cuda' if torch.cuda.is_available() else 'cpu'}")

            self.progress.emit("Transcribing audio...")
            print("Starting transcription...")  # Debug print
            result = model.transcribe(audio_file)

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
                # Emit progress as a percentage
                self.progress.emit(str(int(progress_percentage)))

            print("Emitting finished signal")  # Debug print
            self.finished.emit(transcription)

        except Exception as e:
            print(f"Error occurred: {str(e)}")  # Debug print
            self.progress.emit(f"Error: {str(e)}")
            self.error.emit(str(e))
