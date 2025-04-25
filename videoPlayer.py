import os
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QPushButton,
                               QWidget, QSlider, QHBoxLayout, QProgressBar, QSizePolicy,
                               QLabel)
from PySide6.QtCore import QUrl, Qt, QTimer
from filelock import FileLock, Timeout


class VideoPlayer(QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.resize(800, 600)
        self.update_counter = 0
        # Check every 10 ticks = ~1 second (timer is 100ms)
        self.update_interval = 10
        self.manual_position_update = False

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create a container widget for video and subtitles
        video_container = QWidget()
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)

        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        video_layout.addWidget(self.video_widget)

        # Subtitle label
        self.subtitle_label = QLabel()
        self.subtitle_label.setStyleSheet(
            "background-color: rgba(0, 0, 0, 128); color: white; font-size: 16px; padding: 4px;")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setObjectName("subtitle_label")
        self.subtitle_label.setWordWrap(True)
        video_layout.addWidget(self.subtitle_label)
        video_layout.setAlignment(self.subtitle_label, Qt.AlignBottom)

        layout.addWidget(video_container)

        # Media player setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # Controls layout
        controls_layout = QHBoxLayout()

        # Play/Pause button
        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        controls_layout.addWidget(self.play_pause_button)

        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.sliderMoved.connect(self.set_video_position)
        controls_layout.addWidget(self.position_slider)

        layout.addLayout(controls_layout)

        # Progress bar for transcription
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Volume slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.change_volume)
        layout.addWidget(self.volume_slider)

        # Timer and signals
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position_slider)
        self.timer.timeout.connect(self.check_subtitle)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.positionChanged.connect(self.update_position)

        # Set default volume
        self.audio_output.setVolume(0.5)

        # Store transcript segments
        self.transcript_segments = []

    def load_video(self, video_path, language):
        # Start playing video
        self.media_player.setSource(QUrl.fromLocalFile(video_path))
        self.media_player.play()
        self.timer.start(100)
        self.play_pause_button.setText("Pause")

        # Initialize transcript segments
        self.transcript_segments = []

        # Try to read existing transcription if available
        try:
            transcript_path = "transcription.txt"
            if os.path.exists(transcript_path):
                with open(transcript_path, "r", encoding="utf-8") as f:
                    transcription = f.read()
                    self.parse_transcription(transcription)
        except Exception as e:
            print(f"Error reading initial transcription: {e}")

    def parse_transcription(self, transcription):
        """Parse transcription without affecting playback state"""
        new_segments = []
        for line in transcription.strip().split('\n'):
            if line:
                try:
                    time_str, text = line.split(']', 1)
                    time_str = time_str[1:]  # Remove leading '['
                    start_str, end_str = time_str.split('-')
                    start = float(start_str.strip())
                    end = float(end_str.strip())
                    new_segments.append({
                        'start': start,
                        'end': end,
                        'text': text.strip()
                    })
                except Exception as e:
                    print(f"Error parsing line: {line}")
                    continue

        # Only update if we have new segments
        if new_segments:
            self.transcript_segments = new_segments
            self.progress_bar.hide()

    def check_subtitle(self):
        """Check for new transcription file and update subtitle display"""
        current_time = self.media_player.position() / 1000.0
        current_text = ""
        for segment in self.transcript_segments:
            if segment['start'] <= current_time <= segment['end']:
                current_text = segment['text']
                break

        # Update only if text changes
        if self.subtitle_label.text() != current_text:
            self.subtitle_label.setText(current_text)

        self.update_counter += 1
        if self.update_counter >= self.update_interval:
            self.update_counter = 0
            self.refresh_transcription()

    def refresh_transcription(self):
        """Read the transcription file without affecting playback"""
        try:
            transcript_path = "transcription.txt"
            if not os.path.exists(transcript_path):
                return

            # Store current position
            current_position = self.media_player.position()

            try:
                lock = FileLock(transcript_path + ".lock", timeout=0.5)
                with lock:
                    with open(transcript_path, "r", encoding="utf-8") as f:
                        transcription = f.read()
                        new_segments = []
                        for line in transcription.strip().split('\n'):
                            if line:
                                try:
                                    time_str, text = line.split(']', 1)
                                    # Remove leading '['
                                    time_str = time_str[1:]
                                    start_str, end_str = time_str.split('-')
                                    start = float(start_str.strip())
                                    end = float(end_str.strip())
                                    new_segments.append({
                                        'start': start,
                                        'end': end,
                                        'text': text.strip()
                                    })
                                except Exception as e:
                                    print(f"Error parsing line: {line}")
                                    continue

                        if new_segments:
                            self.transcript_segments = new_segments
                            self.progress_bar.hide()
            except Timeout:
                print("Transcription file locked, will retry later")
                return

            # Restore position if changed
            if self.media_player.position() != current_position:
                self.manual_position_update = True
                self.media_player.setPosition(current_position)
                QTimer.singleShot(100, self._reset_position_flag)
        except Exception as e:
            print(f"Error refreshing transcription: {e}")

    def update_progress(self, message):
        self.progress_bar.show()
        self.progress_bar.setFormat(message)

    def toggle_play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_pause_button.setText("Play")
        else:
            self.media_player.play()
            self.play_pause_button.setText("Pause")

    def change_volume(self, value):
        self.audio_output.setVolume(value / 100)

    def update_duration(self, duration):
        self.position_slider.setRange(0, duration)

    def update_position(self, position):
        if position == 0 and self.media_player.playbackState() == QMediaPlayer.PlayingState:
            print("Warning: Video position reset to 0 unexpectedly")
        if not self.manual_position_update:
            self.position_slider.setValue(position)

    def update_position_slider(self):
        if not self.manual_position_update:
            self.position_slider.setValue(self.media_player.position())

    def set_video_position(self, position):
        self.manual_position_update = True
        self.media_player.setPosition(position)
        QTimer.singleShot(100, self._reset_position_flag)

    def _reset_position_flag(self):
        self.manual_position_update = False
