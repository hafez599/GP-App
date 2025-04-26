import os
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QPushButton,
                               QWidget, QSlider, QHBoxLayout, QSizePolicy,
                               QLabel)
from PySide6.QtCore import Qt


class VideoPlayerUI(QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.resize(800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        central_widget.setObjectName("central_widget")
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create a container widget for video and subtitles
        video_container = QWidget()
        video_container.setObjectName("video_container")
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)

        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setObjectName("video_widget")
        self.video_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        video_layout.addWidget(self.video_widget)

        # Subtitle label
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("subtitle_label")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        video_layout.addWidget(self.subtitle_label)
        video_layout.setAlignment(self.subtitle_label, Qt.AlignBottom)

        layout.addWidget(video_container)

        # Media player setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # Control bar
        control_bar = QWidget()
        control_bar.setObjectName("control_bar")
        control_layout = QHBoxLayout(control_bar)
        control_layout.setContentsMargins(5, 5, 5, 5)
        control_layout.setSpacing(5)

        # Play/Pause button
        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("play_button")
        self.play_button.setFixedSize(30, 30)
        control_layout.addWidget(self.play_button)

        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setObjectName("progress_slider")
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(1000)  # Default range, will be updated
        self.progress_slider.setValue(0)
        control_layout.addWidget(self.progress_slider)

        # Volume button and slider container
        volume_container = QWidget()
        volume_container.setObjectName("volume_container")
        volume_layout = QHBoxLayout(volume_container)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(-50)

        # Volume button (toggles volume slider)
        self.volume_button = QPushButton("🔊")
        self.volume_button.setObjectName("volume_button")
        self.volume_button.setFixedSize(30, 30)
        volume_layout.addWidget(self.volume_button)

        # Volume slider (hidden by default)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setObjectName("volume_slider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)  # Default volume at 50%
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setVisible(False)  # Hidden initially
        volume_layout.addWidget(self.volume_slider)

        control_layout.addWidget(volume_container)

        layout.addWidget(control_bar)
