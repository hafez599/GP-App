import asyncio
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
import shutil
import subprocess
import threading
from tqdm import tqdm
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from queue import Queue
from TranscriptionServer.audio_processing import prepare_audio, segment_audio, create_segment_jobs, cut_audio_segment
from TranscriptionServer.transcription_utils import transcribe_segment, write_srt_segment, format_timestamp
from TranscriptionServer.model_loading import load_whisper_model, load_translation_model
from TranscriptionServer.network_utils import is_port_available
import time
from datetime import datetime


class TranscriptionServer:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.app = FastAPI(title="Video Transcription Streaming API")
        self.segment_queues = {}
        self.model_cache = {}
        self.nmt_model = None
        self.tokenizer = None
        self.server_thread = None
        self.setup_middleware()
        self.setup_routes()
        self.log_file = "log.txt"
        self.log_lock = threading.Lock()

    def setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def log_step(self, step_name, elapsed_time, additional_info=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] Step '{step_name}' completed in {elapsed_time:.2f} seconds"
        if additional_info:
            log_message += f" | {additional_info}"
        log_message += "\n"
        with self.log_lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_message)

    def setup_routes(self):
        # Add a health check endpoint
        @self.app.get("/health")
        async def health_check():
            return JSONResponse(content={"status": "ok"}, status_code=200)

        @self.app.post("/transcribe/")
        async def transcribe_video_streaming(
            file: UploadFile = File(...),
            model_name: str = Form("small"),
            max_workers: int = Form(4),
            min_silence_duration: float = Form(0.7),
            silence_threshold: int = Form(-35)
        ):
            print(f"Received transcribe request for new task")
            task_id = str(uuid.uuid4())
            output_folder = f"temp/{task_id}"
            os.makedirs(output_folder, exist_ok=True)
            temp_file_path = f"{output_folder}/input_video.mp4"
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            self.segment_queues[task_id] = Queue()
            background_thread = threading.Thread(
                target=self.process_video_with_streaming,
                args=(
                    task_id,
                    temp_file_path,
                    output_folder,
                    model_name,
                    max_workers,
                    min_silence_duration,
                    silence_threshold
                )
            )
            background_thread.daemon = True
            background_thread.start()

            async def stream_transcription_results(task_id: str):
                queue = self.segment_queues[task_id]
                try:
                    while True:
                        try:
                            result = queue.get(block=True, timeout=0.1)
                            if result == "DONE":
                                # yield json.dumps({"status": "completed"}) + "\n"
                                break
                            yield json.dumps(result) + "\n"
                        except Exception:
                            await asyncio.sleep(0.1)
                finally:
                    if task_id in self.segment_queues:
                        del self.segment_queues[task_id]

            return StreamingResponse(
                stream_transcription_results(task_id),
                media_type="application/json"
            )

        @self.app.get("/download/{task_id}")
        async def download_srt(task_id: str, language: str = "english"):
            output_folder = f"temp/{task_id}"
            if not os.path.exists(output_folder):
                return {"error": "Task not found or files already cleaned up"}
            if language.lower() == "english":
                srt_path = os.path.join(output_folder, "english.srt")
            elif language.lower() == "arabic":
                srt_path = os.path.join(output_folder, "arabic.srt")
            else:
                return {"error": "Invalid language specified. Use 'english' or 'arabic'"}
            if not os.path.exists(srt_path):
                return {"error": f"{language.capitalize()} SRT file not found"}
            return FileResponse(
                path=srt_path,
                filename=f"{language}_transcription.srt",
                media_type="application/x-subrip"
            )

        @self.app.delete("/cleanup/{task_id}")
        async def cleanup_task(task_id: str):
            output_folder = f"temp/{task_id}"
            if not os.path.exists(output_folder):
                return {"message": "Task files already cleaned up or not found"}
            shutil.rmtree(output_folder)
            if task_id in self.segment_queues:
                del self.segment_queues[task_id]
            return {"message": f"Task {task_id} cleaned up successfully"}

        @self.app.on_event("startup")
        async def startup_event():
            os.makedirs("temp", exist_ok=True)
            self.nmt_model, self.tokenizer = load_translation_model()

    def process_video_with_streaming(
        self,
        task_id: str,
        video_path: str,
        output_folder: str,
        model_name: str,
        max_workers: int,
        min_silence_duration: float,
        silence_threshold: int
    ):
        try:
            print(
                f"Processing video with streaming results. Task ID: {task_id}")
            start_time = time.time()
            raw_audio_path = os.path.join(output_folder, "raw_audio.wav")
            cleaned_audio_path = os.path.join(
                output_folder, "cleaned_speech.wav")
            prepare_audio(video_path, raw_audio_path, cleaned_audio_path)
            elapsed_time = time.time() - start_time
            self.log_step("Prepare Audio", elapsed_time)

            start_time = time.time()
            model = load_whisper_model(model_name)
            elapsed_time = time.time() - start_time
            self.log_step("Load Whisper Model", elapsed_time)

            start_time = time.time()
            silent_points = segment_audio(
                cleaned_audio_path, video_path, min_silence_duration, silence_threshold)
            elapsed_time = time.time() - start_time
            self.log_step("Segment Audio", elapsed_time)

            start_time = time.time()
            video_duration = self.get_video_duration(video_path)
            jobs = create_segment_jobs(silent_points, video_duration)
            elapsed_time = time.time() - start_time
            self.log_step("Create Segment Jobs", elapsed_time)

            start_time = time.time()
            srt_path_en = os.path.join(output_folder, "english.srt")
            srt_path_ar = os.path.join(output_folder, "arabic.srt")
            open(srt_path_en, "w").close()
            open(srt_path_ar, "w").close()
            translation_queue = Queue()
            stop_signal = object()

            def translation_worker():
                while True:
                    segment_to_translate = translation_queue.get()
                    if segment_to_translate is stop_signal:
                        break
                    try:
                        translated = self.nmt_model.generate(
                            **self.tokenizer(
                                segment_to_translate["text"],
                                return_tensors="pt",
                                padding=True,
                                truncation=True
                            ).to(self.nmt_model.device)
                        )
                        translated_text = self.tokenizer.decode(
                            translated[0], skip_special_tokens=True)
                        translated_segment = {
                            **segment_to_translate, "text": translated_text}
                    except Exception as e:
                        print(
                            f"Translation failed for segment {segment_to_translate.get('index', 'unknown')}: {e}")
                        translated_segment = {
                            **segment_to_translate, "text": "[Translation Error]"}
                    index = segment_to_translate["index"]
                    write_srt_segment(translated_segment, srt_path_ar, index)
                    result = {
                        "segment_index": index,
                        "start_time": segment_to_translate["start"],
                        "end_time": segment_to_translate["end"],
                        "english": segment_to_translate["text"],
                        "arabic": translated_segment["text"]
                    }
                    self.segment_queues[task_id].put(result)

            translator_thread = threading.Thread(target=translation_worker)
            translator_thread.daemon = True
            translator_thread.start()

            def process_segment_streaming(job):
                start_time_segment = time.time()
                start_time, end_time, segment_idx = job
                temp_audio_file = os.path.join(
                    output_folder, f"segment_{segment_idx}_audio.wav")
                try:
                    cut_audio_segment(cleaned_audio_path,
                                      temp_audio_file, start_time, end_time)
                    adjusted_segments = transcribe_segment(
                        model, temp_audio_file, start_time, end_time)
                    for segment in adjusted_segments:
                        index = next(itertools.count(1))
                        write_srt_segment(segment, srt_path_en, index)
                        segment_with_index = {**segment, "index": index}
                        translation_queue.put(segment_with_index)
                    try:
                        os.remove(temp_audio_file)
                    except:
                        pass
                except Exception as e:
                    print(f"Error processing segment {segment_idx}: {str(e)}")
                finally:
                    elapsed_time_segment = time.time() - start_time_segment
                    self.log_step(
                        f"Process Segment {segment_idx}",
                        elapsed_time_segment,
                        additional_info=f"Start Time: {start_time:.2f}s, End Time: {end_time:.2f}s"
                    )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = list(tqdm(executor.map(process_segment_streaming, jobs), total=len(
                    jobs), desc="Transcribing segments"))
            elapsed_time = time.time() - start_time
            self.log_step(
                "Process Segments (Transcription and Translation)", elapsed_time)

            start_time = time.time()
            translation_queue.put(stop_signal)
            translator_thread.join()
            self.segment_queues[task_id].put("DONE")
            elapsed_time = time.time() - start_time
            self.log_step("Cleanup and Finalization", elapsed_time)

        except Exception as e:
            print(f"Error in video processing: {e}")
            if task_id in self.segment_queues:
                self.segment_queues[task_id].put(
                    {"status": "error", "message": str(e)})
                self.segment_queues[task_id].put("DONE")

    def get_video_duration(self, video_path):
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", video_path]
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())

    def start(self):
        if self.server_thread is None or not self.server_thread.is_alive():
            port = self.port
            while not is_port_available(port):
                print(f"Port {port} is in use, trying {port + 1}")
                port += 1
            self.port = port
            self.server_thread = threading.Thread(
                target=self.run_api, daemon=True)
            self.server_thread.start()
            print(
                f"Transcription server started at http://{self.host}:{self.port}")
        else:
            print("Server is already running.")

    def run_api(self):
        uvicorn.run(self.app, host=self.host, port=self.port)

    def stop(self):
        if self.server_thread and self.server_thread.is_alive():
            print("Stopping transcription server...")
            self.server_thread = None
            print("Transcription server stopped.")
