from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel)
from transcriptionWorker import TranscriptionWorker
from nmtModel import NmtModel
from PySide6.QtMultimedia import QAudioOutput
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt


class Scene2(QWidget):
    def __init__(self, main_window, video_path=None, language=None):
        super().__init__()
        self.main_window = main_window

        # Create layout
        layout = QVBoxLayout()
        self.data_label = QLabel()
        self.data_label.setWordWrap(True)
        # layout.addWidget(self.data_label)

        # SVG display widget
        self.svg_widget = QSvgWidget()
        self.svg_widget.setFixedSize(300, 300)
        # Create a horizontal layout to center the SVG widget
        svg_layout = QHBoxLayout()
        svg_layout.addWidget(self.svg_widget)
        svg_layout.setAlignment(
            self.svg_widget, Qt.AlignmentFlag.AlignCenter)  # Center the widget

        # Add the centered layout to the main layout
        layout.addLayout(svg_layout)
        # Load the base SVG content
        svg_file = "infinite-spinner.svg"
        with open(svg_file, "r", encoding="utf-8") as file:
            self.base_svg = file.read()

        # Animation parameters
        self.current_offset = 0  # Stroke-dashoffset value
        self.offset_increment = 20  # Amount to change in each frame
        self.dasharray = 300  # Stroke-dasharray value

        # Timer for updating SVG dynamically
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_svg_frame)
        self.timer.start(30)  # Update every 30 ms

        # Initial update
        self.update_svg_frame()

        # Back button
        button = QPushButton("Back")
        button.clicked.connect(self.main_window.switch_to_scene1)
        layout.addWidget(button)

        self.setLayout(layout)

    def update_svg_frame(self):
        """Update the SVG content dynamically."""
        # Update the dashoffset value
        self.current_offset = (self.current_offset +
                               self.offset_increment) % (2.3 * self.dasharray)

        # Update the path dynamically by replacing its stroke-dashoffset
        updated_svg = self.base_svg.replace(
            'stroke-dashoffset="0"',
            f'stroke-dashoffset="{self.current_offset}"'
        )

        # Load the updated SVG content into the widget
        self.svg_widget.load(updated_svg.encode("utf-8"))

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

    # you can delete this function
    def load_styles(self):
        """Load styles from an external CSS file."""
        try:
            with open("styles.css", "r") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            print("Error: styles.css file not found.")
