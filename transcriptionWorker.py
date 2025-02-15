# import subprocess
# from PySide6.QtCore import QThread, Signal
# from whisper import load_model
# import torch
# import os
# from pathlib import Path

# class TranscriptionWorker(QThread):
#     finished = Signal(str)
#     progress = Signal(str)
#     error = Signal(str)

#     def __init__(self, video_file):
#         super().__init__()
#         self.video_file = video_file
#         print(f"Initialized with video file: {video_file}")  # Debug print

#     def run(self):
#         try:
#             # Extract audio
#             print("Starting audio extraction...")  # Debug print
#             self.progress.emit("Extracting audio...")

#             # Get the current working directory of the project
#             project_dir = Path(os.getcwd())  # Current project directory
#             video_name = Path(self.video_file).stem  # Get video filename without extension
#             audio_file = project_dir / f"{video_name}.mp3"  # Save in project directory

#             print(f"Running ffmpeg command to save {audio_file}")  # Debug print
#             subprocess.run(
#                 ["ffmpeg", "-i", self.video_file, "-q:a",
#                  "0", "-map", "a", str(audio_file)],
#                 check=True,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE
#             )
#             print("Audio extraction complete")  # Debug print

#             # Transcribe audio
#             print("Loading Whisper model...")  # Debug print
#             self.progress.emit("Loading Whisper model...")
#             model = load_model(
#                 "tiny", device="cuda" if torch.cuda.is_available() else "cpu")

#             # Debug print
#             print(f"Using device: {'cuda' if torch.cuda.is_available() else 'cpu'}")

#             self.progress.emit("Transcribing audio...")
#             print("Starting transcription...")  # Debug print
#             result = model.transcribe(str(audio_file))

#             # Format transcription and emit progress
#             transcription = ""
#             total_segments = len(result["segments"])
#             for index, segment in enumerate(result["segments"]):
#                 start = segment["start"]
#                 end = segment["end"]
#                 text = segment["text"]
#                 transcription += f"[{start:.2f} - {end:.2f}] {text}\n"

#                 # Emit progress update
#                 progress_percentage = (index + 1) / total_segments * 100
#                 self.progress.emit(str(int(progress_percentage)))

#             print("Emitting finished signal")  # Debug print
#             print(transcription)
#             self.finished.emit(transcription)

#         except Exception as e:
#             print(f"Error occurred: {str(e)}")  # Debug print
#             self.progress.emit(f"Error: {str(e)}")
#             self.error.emit(str(e))


# import subprocess
# import os
# from pathlib import Path
# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.responses import JSONResponse
# from whisper import load_model
# import torch
# import uuid

# app = FastAPI()

# # Load the Whisper model once at startup
# device = "cuda" if torch.cuda.is_available() else "cpu"
# model = load_model("tiny", device=device)


# def extract_audio(video_path: str) -> str:
#     """Extracts audio from a video file using FFmpeg and saves it as an MP3."""
#     audio_file = str(Path(video_path).with_suffix(".mp3"))

#     subprocess.run(
#         ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_file],
#         check=True,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE
#     )

#     return audio_file


# def transcribe_audio_to_srt_format(audio_path: str) -> str:
#     """Transcribes an audio file using Whisper and returns a subtitle-formatted text."""
#     result = model.transcribe(audio_path)
#     # srt_text = ""

#     # for index, segment in enumerate(result["segments"], start=1):
#     #     start_time = segment["start"]
#     #     end_time = segment["end"]
#     #     text = segment["text"]

#     #     # Convert timestamps to SRT format (HH:MM:SS,mmm)
#     #     def format_time(seconds):
#     #         hours = int(seconds // 3600)
#     #         minutes = int((seconds % 3600) // 60)
#     #         seconds = seconds % 60
#     #         milliseconds = int((seconds - int(seconds)) * 1000)
#     #         return f"{hours:02}:{minutes:02}:{int(seconds):02},{milliseconds:03}"

#     #     srt_text += f"{index}\n"
#     #     srt_text += f"{format_time(start_time)} --> {format_time(end_time)}\n"
#     #     srt_text += f"{text}\n\n"

#     transcription = ""
#     total_segments = len(result["segments"])
#     for index, segment in enumerate(result["segments"]):
#         start = segment["start"]
#         end = segment["end"]
#         text = segment["text"]
#         transcription += f"[{start:.2f} - {end:.2f}] {text}\n"
    
#     # return srt_text
#     return transcription


# @app.post("/transcribe/")
# async def transcribe_video(file: UploadFile = File(...)):
#     """API endpoint to handle video file uploads and return SRT-formatted text."""
#     try:
#         # Save the uploaded file temporarily
#         temp_filename = f"temp_{uuid.uuid4().hex}{Path(file.filename).suffix}"
#         temp_filepath = Path(temp_filename)

#         with open(temp_filepath, "wb") as temp_file:
#             temp_file.write(await file.read())

#         # Extract audio
#         audio_path = extract_audio(str(temp_filepath))

#         # Transcribe into SRT format text
#         srt_text = transcribe_audio_to_srt_format(audio_path)

#         # Cleanup
#         os.remove(temp_filepath)
#         os.remove(audio_path)
#         print(srt_text)
#         return JSONResponse(content={"transcription": srt_text})

#     except subprocess.CalledProcessError as e:
#         raise HTTPException(status_code=500, detail=f"FFmpeg error: {e}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
