from PySide6.QtCore import QThread, Signal
import requests
import os


class TranscriptionWorkerAPI(QThread):
    finished = Signal(str)   # Signal when transcription is complete
    progress = Signal(str)   # Dummy progress signal
    error = Signal(str)      # Signal for errors

    def __init__(self, video_file, language):
        super().__init__()
        self.video_file = video_file
        # FastAPI URL
        self.api_url = f"https://76c3-34-87-137-39.ngrok-free.app/transcribe/?translate={not language}"

    def run(self):
        """Calls the FastAPI endpoint asynchronously and retrieves the transcript file."""
        try:
            self.progress.emit("Uploading file...")

            with open(self.video_file, "rb") as file:
                files = {"file": (os.path.basename(
                    self.video_file), file, "video/mp4")}

                response = requests.post(self.api_url, files=files)

            if response.status_code == 200:
                # Parse the JSON response
                response_data = response.json()

                # Extract transcription text
                transcription_text = response_data.get("transcription", "")

                # Ensure proper formatting
                formatted_text = transcription_text.strip()

                # Debug: Print the transcription
                print("Received transcription:\n", formatted_text)

                # Save the received transcription file locally
                transcript_filename = "transcription.txt"
                with open(transcript_filename, "w", encoding="utf-8") as f:
                    f.write(formatted_text)

                self.finished.emit(f"{formatted_text}")
            else:
                error_message = response.text
                self.error.emit(f"API Error: {error_message}")

        except Exception as e:
            self.error.emit(f"Request failed: {str(e)}")
