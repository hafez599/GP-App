import re
from transformers import MarianMTModel, MarianTokenizer
from torch.quantization import quantize_dynamic
import torch
from PySide6.QtCore import QThread, Signal

class NmtModel(QThread):
    finished = Signal(str, str)
    progress = Signal(str)
    error = Signal(str)

    def __init__(self, transcription, video_path):
        super().__init__()
        self.transcription = transcription
        self.video_path = video_path
        print(f"Initialized NMT Model with transcription length: {len(transcription)}")

    def run(self):
        try:
            # Load translation model
            model_name = 'Helsinki-NLP/opus-mt-tc-big-en-ar'
            model = MarianMTModel.from_pretrained(model_name)
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = quantize_dynamic(
                model,  # Model to quantize
                {torch.nn.Linear},  # Layers to quantize
                dtype=torch.qint8  # Use 8-bit integers
            )

            # Correct timestamp format using regex (fix colons and missing decimals)
            self.transcription = re.sub(r'(\d+):(\d+)', r'\1.\2', self.transcription)
            self.transcription = re.sub(r'(\d+)\.(\d{2})\.(\d{2})', r'\1.\2\3', self.transcription)

            # Regex pattern to capture timestamps and text separately
            pattern = r'\[(\d{1,3}\.\d{2})\s*-\s*(\d{1,3}\.\d{2})\]\s*(.*)'

            translated_lines = []
            for match in re.finditer(pattern, self.transcription):
                start_time, end_time, text = match.groups()

                if text.strip():
                    encoded_text = tokenizer([text], return_tensors="pt", padding=True, truncation=True)
                    output_ids = model.generate(encoded_text['input_ids'], num_beams=1, length_penalty=1.0)
                    translated_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

                    # Store translated line with timestamps
                    translated_lines.append(f"[{start_time} - {end_time}] {translated_text}")

            # Join translated lines with newlines
            translated_transcription = "\n".join(translated_lines)

            # Emit the translated text
            self.finished.emit(translated_transcription, self.video_path)

            # Notify progress
            self.progress.emit("Translation completed successfully")

        except Exception as e:
            print(f"Translation error: {str(e)}")
            self.error.emit(str(e))
