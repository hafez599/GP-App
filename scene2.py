from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt
from TranscriptionWorkerAPI import TranscriptionWorkerAPI


class Scene2(QWidget):
    def __init__(self, main_window, video_path=None, language=None):
        super().__init__()
        self.main_window = main_window

        # Create layout
        layout = QVBoxLayout()

        # Web Engine View for SVG Animation
        self.webview = QWebEngineView()
        self.webview.setFixedSize(300, 300)

        # Create a horizontal layout to center the Web Engine View
        svg_layout = QHBoxLayout()
        svg_layout.addWidget(self.webview)
        svg_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter)  # Fixed alignment

        # Add the centered layout to the main layout
        layout.addLayout(svg_layout)

        html_file = "animationLoader.html"
        svg_file = "fade-stagger-circles.svg"

        # Read the SVG file
        with open(svg_file, "r", encoding="utf-8") as file:
            svg_content = file.read()

        # Read the HTML template
        with open(html_file, "r", encoding="utf-8") as file:
            html_template = file.read()

        # Insert the SVG content into the HTML
        final_html = html_template.replace("{SVG_CONTENT}", svg_content)

        # Load into QWebEngineView
        self.webview.setHtml(final_html)

        # Back button
        button = QPushButton("Back")
        button.clicked.connect(self.main_window.switch_to_scene1)
        layout.addWidget(button)

        self.setLayout(layout)

    def transcript(self, video_path, language):
        """Handles video transcription process"""
        self.video_path = video_path
        self.language = language
        print(f"Starting transcription for: {video_path}")  # Debug print

        if not video_path:
            print("Error: No video file selected")  # Debug print
            return

        self.transcription_worker = TranscriptionWorkerAPI(
            video_path, self.language)
        self.transcription_worker.progress.connect(self.update_progress)
        self.transcription_worker.receive_first_segment.connect(self.handle_transcription) # test this line Finished
        self.transcription_worker.error.connect(self.handle_error)
        self.transcription_worker.start()
        print("TranscriptionWorker started")  # Debug print

    def handle_transcription(self, transcription):
        """Handles transcription completion"""
        print("Received transcription")  # Debug print
        self.main_window.switch_to_VideoPlayer(self.video_path, self.language)

    def handle_error(self, error_message):
        """Handles errors during transcription"""
        print(f"Error received: {error_message}")  # Debug print

    def update_progress(self, message):
        """Updates transcription progress"""
        print(f"Progress update: {message}")  # Debug print
