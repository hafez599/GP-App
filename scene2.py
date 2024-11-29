from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                              QProgressBar, QTextEdit, QScrollArea)
from transcriptionWorker import TranscriptionWorker
from nmtModel import NmtModel
class Scene2(QWidget):
    def __init__(self, main_window,video_path=None,language=None):
        super().__init__()
        self.main_window = main_window
        # Create layout
        layout = QVBoxLayout()
        self.data_label = QLabel()
        self.data_label.setWordWrap(True)
        layout.addWidget(self.data_label)
        # Create text display area with scrolling
        self.transcript_display = QTextEdit()
        self.transcript_display.setReadOnly(True)
        self.transcript_display.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        
        # Back button
        button = QPushButton("Back")
        button.clicked.connect(self.main_window.switch_to_scene1)
        button.setStyleSheet("""
            QPushButton {
                background-color: #0083e5;
                border: none;
                padding: 15px;
                border-radius: 5px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #359ae8;
            }
        """)
        
        # Add widgets to layout
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.transcript_display)
        layout.addWidget(button)
        
        self.setLayout(layout)

    def transcript(self, video_path,language):
        self.video_path = video_path
        self.language = language
        print(f"Starting transcription for: {video_path}")  # Debug print
        if not video_path:
            self.data_label.setText("Error: No video file selected")
            return
            
        self.progress_bar.show()
        self.progress_bar.setFormat("Processing...")
        self.transcription_worker = TranscriptionWorker(video_path)
        self.transcription_worker.progress.connect(self.update_progress)
        self.transcription_worker.finished.connect(self.handle_transcription)
        self.transcription_worker.error.connect(self.handle_error)  # Add error handler
        self.transcription_worker.start()
        print("TranscriptionWorker started")  # Debug print

    def handle_transcription(self, transcription):
        print("Received transcription")  # Debug print
        # Display the result
        self.data_label.setText(transcription[:100] + "...")  # Show first 100 chars
        if(self.language == False):
            self.nmtModel = NmtModel(transcription)
            self.nmtModel.progress.connect(self.update_progress)
            self.nmtModel.finished.connect(lambda translated_text: self.handle_transcription_forNmt(translated_text, self.video_path))
            self.nmtModel.start()
        else:
    # Save transcription to file
            try:
                with open("transcription.txt", "w", encoding="utf-8") as file:
                    file.write(transcription)
                print("Transcription saved to file")  # Debug print
            except Exception as e:
                print(f"Error saving file: {str(e)}")  # Debug print
                self.data_label.setText(f"Error saving transcription: {str(e)}")
                    
        # Hide progress bar
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        self.main_window.switch_to_VideoPlayer(self.video_path)



    def handle_transcription_forNmt(self, transcription,video_path):
        print("Received transcription")  # Debug print
    # Save transcription to file
        try:
            with open("transcription.txt", "w", encoding="utf-8") as file:
                file.write(transcription)
            print("Transcription saved to file")  # Debug print
        except Exception as e:
            print(f"Error saving file: {str(e)}")  # Debug print
            self.data_label.setText(f"Error saving transcription: {str(e)}")
                
        # Hide progress bar
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        self.main_window.switch_to_VideoPlayer(video_path)



    def handle_error(self, error_message):
        print(f"Error received: {error_message}")  # Debug print
        self.data_label.setText(f"Error: {error_message}")
        self.progress_bar.hide()

    def update_progress(self, message):
        print(f"Progress update: {message}")  # Debug print
        self.progress_bar.setFormat(message)