from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFileDialog,
    QRadioButton, QTextEdit, QProgressBar, QSizePolicy, QButtonGroup
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class Scene1(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.video_path = None
        self.is_arabic = None  # True for Arabic, False for English

        # Main layout
        main_layout = QVBoxLayout(self)

        # Title
        title = QLabel("Auto Subtitle Generator")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Language Selection (Radio buttons styled like checkboxes)
        lang_layout = QHBoxLayout()
        self.arabic_rb = QRadioButton("Arabic")
        self.english_rb = QRadioButton("English")

        lang_group = QButtonGroup(self)
        lang_group.setExclusive(True)
        lang_group.addButton(self.arabic_rb)
        lang_group.addButton(self.english_rb)

        for rb in (self.arabic_rb, self.english_rb):
            rb.setFixedSize(120, 60)
            rb.toggled.connect(self.set_language_selection)
            lang_layout.addWidget(rb)

        lang_layout.setSpacing(50)
        lang_layout.setAlignment(Qt.AlignCenter)
        main_layout.addLayout(lang_layout)

        # Add Media Button
        self.media_button = QPushButton("📁 Add Media")
        self.media_button.clicked.connect(self.upload_video)
        self.media_button.setObjectName("Add_Media_Button")
        self.media_button.setFixedHeight(40)
        self.media_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.media_button)

        # File path display
        self.file_path_display = QTextEdit()
        self.file_path_display.setReadOnly(True)
        self.file_path_display.setFixedHeight(50)
        self.file_path_display.setPlaceholderText("No video selected...")
        main_layout.addWidget(self.file_path_display)

        # Start button
        self.start_button = QPushButton("▶ Start Transcription")
        self.start_button.setObjectName("Start_button")
        self.start_button.setFixedHeight(50)
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.send_data)
        main_layout.addWidget(self.start_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

    def upload_video(self):
        file_dialog = QFileDialog()
        video_path, _ = file_dialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)"
        )
        if video_path:
            self.video_path = video_path  # Store selected video path
            self.file_path_display.clear()
            self.file_path_display.setText(video_path)
            self.start_button.setEnabled(True)

    def set_language_selection(self):
        if self.arabic_rb.isChecked():
            self.is_arabic = True
        elif self.english_rb.isChecked():
            self.is_arabic = False

    def send_data(self):
        if self.video_path is not None:
            self.main_window.switch_to_scene2(self.video_path, self.is_arabic)
