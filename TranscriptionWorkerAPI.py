from PySide6.QtCore import QThread, Signal
import requests
import os


class TranscriptionWorkerAPI(QThread):
    finished = Signal(str)   # Signal when transcription is complete
    progress = Signal(str)   # Dummy progress signal
    error = Signal(str)      # Signal for errors

    def __init__(self, video_file):
        super().__init__()
        self.video_file = video_file
        self.api_url = "https://64a8-34-168-219-90.ngrok-free.app/transcribe/"  # FastAPI URL

    def run(self):
        """Calls the FastAPI endpoint asynchronously."""
        try:
            self.progress.emit("Uploading file...")
            with open(self.video_file, "rb") as file:
                files = {"file": (os.path.basename(
                    self.video_file), file, "video/mp4")}

                response = requests.post(self.api_url, files=files)

            if response.status_code == 200:
                transcription = response.json()["transcription"]
                self.finished.emit(transcription)
            else:
                error_message = response.json().get("detail", "Unknown error")
                self.error.emit(f"API Error: {error_message}")

        except Exception as e:
            self.error.emit(f"Request failed: {str(e)}")
