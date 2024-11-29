from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel,
                               QProgressBar)
from transcriptionWorker import TranscriptionWorker
from nmtModel import NmtModel
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl
from PySide6.QtMultimediaWidgets import QVideoWidget


class Scene2(QWidget):
    def __init__(self, main_window, video_path=None, language=None):
        super().__init__()
        self.main_window = main_window

        # Create layout
        layout = QVBoxLayout()
        self.data_label = QLabel()
        self.data_label.setWordWrap(True)
        layout.addWidget(self.data_label)

        # video spinner
        # Create a video widget
        self.video_widget = QVideoWidget()
        # Set the fixed width and height for the video
        # Set desired width and height
        self.video_widget.setFixedSize(150, 150)

        # Set up media player
        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)

        # Set up audio output
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        # Load the video file
        self.media_player.setSource(QUrl.fromLocalFile(
            "Animation - 1732909505431 (1).gif"))  # Replace with your video path

        # Connect the signal to loop the video
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)

        self.video_widget.setStyleSheet("""
            QVideoWidget{
                margin-left: 500px;
                height: 150px;
            }
            QMediaPlayer
            {
                width: 150px;
                height: 150px;
            }
            """
                                        )
        # Start playback
        self.media_player.play()

        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)  # Set range for progress
        layout.addWidget(self.progress_bar)

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
        layout.addWidget(self.video_widget)
        layout.addWidget(button)
        self.setLayout(layout)

    def transcript(self, video_path, language):
        self.video_path = video_path
        self.language = language
        print(f"Starting transcription for: {video_path}")  # Debug print

        if not video_path:
            self.data_label.setText("Error: No video file selected")
            return

        self.transcription_worker = TranscriptionWorker(video_path)

        # Connect signals
        self.transcription_worker.progress.connect(self.update_progress)
        self.transcription_worker.finished.connect(self.handle_transcription)
        # self.transcription_worker.error.connect(
        #     self.handle_error)  # Add error handler

        self.transcription_worker.start()
        print("TranscriptionWorker started")  # Debug print

    def handle_transcription(self, transcription):
        print("Received transcription")  # Debug print
        # Show first 100 chars
        self.data_label.setText(transcription[:100] + "...")

        if not self.language:
            self.nmtModel = NmtModel(transcription)
            self.nmtModel.progress.connect(self.update_progress)
            self.nmtModel.finished.connect(lambda translated_text: self.handle_transcription_forNmt(
                translated_text, self.video_path))
            self.nmtModel.start()
        else:
            # Save transcription to file
            try:
                with open("transcription.txt", "w", encoding="utf-8") as file:
                    file.write(transcription)
                print("Transcription saved to file")  # Debug print
            except Exception as e:
                print(f"Error saving file: {str(e)}")  # Debug print
                self.data_label.setText(
                    f"Error saving transcription: {str(e)}")

        self.main_window.switch_to_VideoPlayer(self.video_path)

    def update_progress(self, message):
        print(f"Progress update: {message}")  # Debug print
        # Update the progress bar. Assuming message contains a percentage.
        if message.isdigit():
            self.progress_bar.setValue(int(message))
            print(message)
        else:
            pass
            # print(message)

    def handle_media_status(self, status):
        """Restart the video when it ends."""
        if status == QMediaPlayer.EndOfMedia:
            self.media_player.stop()
            self.media_player.play()
