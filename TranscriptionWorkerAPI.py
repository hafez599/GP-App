from PySide6.QtCore import QThread, Signal
import requests
import os
import json
from filelock import FileLock  # <-- Add filelock import
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


class TranscriptionWorkerAPI(QThread):
    finished = Signal(str)   # Emitted when all transcription is done
    # Emitted when first segment transcription is done
    receive_first_segment = Signal(str)
    progress = Signal(str)   # Emitted as segments stream in
    error = Signal(str)      # Emitted on any error

    def __init__(self, video_file, language):
        super().__init__()
        self.video_file = video_file
        self.api_url = f"https://bf2c-35-240-248-88.ngrok-free.app/transcribe/"
        self.translate = not language  # True if language=False
        self.transcript_filename = "transcription.txt"
        self.lock = FileLock(self.transcript_filename + ".lock")  # Lock file
        self.is_first_segment = True

    def run(self):
        try:
            if os.path.exists(self.transcript_filename):
                os.remove(self.transcript_filename)
                print(f"{self.transcript_filename} has been deleted.")

            with open(self.video_file, "rb") as f:
                encoder = MultipartEncoder(
                    fields={
                        "file": (os.path.basename(self.video_file), f, "video/mp4"),
                        "model_name": "small",
                        "max_workers": "1",
                        "min_silence_duration": "0.7",
                        "silence_threshold": "-35"
                    }
                )

                def callback(monitor):
                    percent = int((monitor.bytes_read / monitor.len) * 100)
                    self.progress.emit(f"Uploading: {percent}%")

                monitor = MultipartEncoderMonitor(encoder, callback)

                headers = {"Content-Type": monitor.content_type}

                response = requests.post(
                    self.api_url,
                    data=monitor,
                    headers=headers,
                    stream=True,
                    timeout=300
                )

                if response.status_code != 200:
                    self.error.emit(f"API Error: {response.text}")
                    return

                for line in response.iter_lines():
                    if line:
                        try:
                            segment = json.loads(line)

                            # Round time fields
                            segment["start_time"] = round(
                                segment.get("start_time", 0), 3)
                            segment["end_time"] = round(
                                segment.get("end_time", 0), 3)
                            preference = 'arabic' if self.translate else 'english'

                            # Compose readable format
                            text = f"[{segment['start_time']} - {segment['end_time']}] {segment[preference]}\n"

                            # Safely write to file using file lock
                            with self.lock:
                                with open(self.transcript_filename, "a", encoding="utf-8") as f:
                                    f.write(text)
                                    f.flush()
                            if self.is_first_segment:
                                self.receive_first_segment.emit(
                                    "First Segment Received")
                                self.is_first_segment = False

                            # Emit each line as progress
                            self.progress.emit(text)
                        except Exception as e:
                            self.error.emit(f"Streaming decode error: {e}")

            self.finished.emit("Transcription completed and saved.")

        except Exception as e:
            self.error.emit(f"Request failed: {str(e)}")
