import subprocess
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import ( QMainWindow, QVBoxLayout, QPushButton, 
                             QWidget, QSlider, QHBoxLayout, QProgressBar,
                             QLabel)
from PySide6.QtCore import QUrl, Qt, QTimer

class VideoPlayer(QMainWindow):
    def __init__(self,main_window):
        super().__init__()
        self.main_window = main_window
        self.resize(800, 600)

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
        video_layout.addWidget(self.video_widget)

        # Subtitle label
        self.subtitle_label = QLabel()
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 0.5);
                padding: 10px;
                border-radius: 5px;
                margin: 10px;
            }
        """)
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
        self.timer.timeout.connect(self.update_subtitle)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.positionChanged.connect(self.update_position_slider)
        
        # Set default volume
        self.audio_output.setVolume(0.5)
        
        # Store transcript segments
        self.transcript_segments = []

    def load_video(self,video_path):
        # Start playing video
        self.media_player.setSource(QUrl.fromLocalFile(video_path))
        self.media_player.play()
        self.timer.start(100)  # Update more frequently for smoother subtitles
        self.play_pause_button.setText("Pause")

        # Try to load existing transcription
        transcript_path = "transcription.txt"
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcription = f.read()
            self.handle_transcription(transcription)


    def handle_transcription(self, transcription):
        # Parse and store transcript segments
        self.transcript_segments = []
        for line in transcription.strip().split('\n'):
            if line:
                try:
                    time_str, text = line.split(']', 1)
                    time_str = time_str[1:]  # Remove leading '['
                    start_str, end_str = time_str.split('-')
                    start = float(start_str.strip())
                    end = float(end_str.strip())
                    self.transcript_segments.append({
                        'start': start,
                        'end': end,
                        'text': text.strip(),
                        'full_line': line
                    })
                except Exception as e:
                    print(f"Error parsing line: {line}")
                    continue
        
        # Save transcription to file
        with open("transcription.txt", "w", encoding="utf-8") as file:
            file.write(transcription)
        
        # Hide progress bar
        self.progress_bar.hide()
        self.progress_bar.setValue(0)

    def update_subtitle(self):
        current_time = self.media_player.position() / 1000.0  # Convert to seconds
        
        # Find the current segment
        current_text = ""
        for segment in self.transcript_segments:
            if segment['start'] <= current_time <= segment['end']:
                current_text = segment['text']
                break
        self.subtitle_label.setText(current_text)

    def update_progress(self, message):
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

    def update_position_slider(self):
        self.position_slider.setValue(self.media_player.position())

    def set_video_position(self, position):
        self.media_player.setPosition(position)