from PySide6.QtCore import QThread, Signal
import requests
import os
import json
from filelock import FileLock  # <-- Add filelock import

class TranscriptionWorkerAPI(QThread):
    finished = Signal(str)   # Emitted when all transcription is done
    receive_first_segment = Signal(str)   # Emitted when all transcription is done
    progress = Signal(str)   # Emitted as segments stream in
    error = Signal(str)      # Emitted on any error

    def __init__(self, video_file, language):
        super().__init__()
        self.video_file = video_file
        self.api_url = f"https://d31d-34-125-125-220.ngrok-free.app/transcribe/"
        self.translate = not language  # True if language=False
        self.transcript_filename = "transcription.txt"
        self.lock = FileLock(self.transcript_filename + ".lock")  # Lock file

    def run(self):
        try:
            if os.path.exists(self.transcript_filename):
                os.remove(self.transcript_filename)
                print(f"{self.transcript_filename} has been deleted.")
                    
            with open(self.video_file, "rb") as file:
                files = {"file": (os.path.basename(self.video_file), file, "video/mp4")}
                data = {
                    "model_name": "small",
                    "max_workers": "1",
                    "min_silence_duration": "0.7",
                    "silence_threshold": "-35"
                }

                response = requests.post(self.api_url, data=data, files=files, stream=True, timeout=300)

                if response.status_code != 200:
                    self.error.emit(f"API Error: {response.text}")
                    return
                self.receive_first_segment.emit("First Segment Received")

                for line in response.iter_lines():
                    if line:
                        try:
                            segment = json.loads(line)

                            # Round time fields
                            segment["start_time"] = round(segment.get("start_time", 0), 3)
                            segment["end_time"] = round(segment.get("end_time", 0), 3)
                            preference = 'arabic' if self.translate else 'english'

                            # Compose readable format
                            text = f"[{segment['start_time']} - {segment['end_time']}] {segment[preference]}\n"

                            # Safely write to file using file lock
                            with self.lock:
                                with open(self.transcript_filename, "a", encoding="utf-8") as f:
                                    f.write(text)
                                    f.flush()

                            self.progress.emit(text)  # Emit each line as progress
                        except Exception as e:
                            self.error.emit(f"Streaming decode error: {e}")

            self.finished.emit("Transcription completed and saved.")

        except Exception as e:
            self.error.emit(f"Request failed: {str(e)}")