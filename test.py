# import re
# from transformers import MarianMTModel, MarianTokenizer

# # Extract the sentences from the input text
# input_text = """
# [0.00 - 10.52]  Hello and welcome to the Los Poyers of the Manus Family.
# [10.52 - 13.28]  My name is Gustavo, but you can call me Gus.
# [13.28 - 16.52]  I am thrilled that you will be joining our team.
# [16.52 - 22.24]  Each and every day we serve our customers exceptional food with impeccable service.
# [22.24 - 24.92]  We take pride in everything that we do.
# [24.92 - 31.24]  And after this 10 week online seminar, I am confident that you fit right in.
# [31.24 - 34.72]  I like to think I see things in people.
# [34.72 - 39.68]  To begin, I'd like to talk about the cornerstone of the Los Poyers of Manus brand,
# [39.68 - 40.68]  communication.
# """

# sentences = re.findall(r'\[(.*?)\]\s+(.*)', input_text)

# # Load the pre-trained model and tokenizer
# model_name = 'Helsinki-NLP/opus-mt-tc-big-en-ar'
# model = MarianMTModel.from_pretrained(model_name)
# tokenizer = MarianTokenizer.from_pretrained(model_name)

# # Translate the sentences
# translated_sentences = []
# for _, sentence in sentences:
#     encoded_text = tokenizer.encode(sentence, return_tensors='pt')
#     output_ids = model.generate(encoded_text, max_length=100, num_beams=4, early_stopping=True)
#     translated_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
#     translated_sentences.append(translated_text)

# # Combine the timestamps and translated sentences
# output_text = '\n'.join([f'[{timestamp}] {translated}' for timestamp, translated in zip([timestamp for timestamp, _ in sentences], translated_sentences)])

# print(output_text)
# with open("transcription.txt", "w", encoding="utf-8") as file:
#             file.write(output_text)
#             print("Transcription saved to file")

# from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
# from PySide6.QtGui import QFont, QFontDatabase


# class LabelExample(QWidget):
#     def __init__(self):
#         super().__init__()

#         # Layout for the label
#         layout = QVBoxLayout()

#         # Create a QLabel
#         label = QLabel("Hello, World!")

#         # Load the custom font
#         font_id = QFontDatabase.addApplicationFont('DancingScript-VariableFont_wght.ttf')

#         # Check if the font was successfully loaded
#         if font_id == -1:
#             print("Failed to load font!")
#         else:
#             # Get the font family name (it might be different from the font file name)
#             font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

#         # Create a QFont object and set the font properties
#         font = QFont()
#         font.setFamily(font_family)  # Set the font family
#         font.setPointSize(18)    # Set the font size
#         font.setBold(True)       # Set the font to bold
#         font.setItalic(False)    # Set the font to not italic
#         font.setUnderline(False)  # Set the font to not underlined

#         # Apply the font to the label
#         label.setFont(font)

#         # Set text color
#         label.setStyleSheet("color: #FF6347;")  # Set text color

#         # Add the label to the layout
#         layout.addWidget(label)

#         # Set layout for the window
#         self.setLayout(layout)


# if __name__ == "__main__":
#     app = QApplication([])
#     window = LabelExample()
#     window.show()
#     app.exec_()








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