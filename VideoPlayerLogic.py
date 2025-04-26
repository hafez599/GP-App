import os
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtCore import QTimer, QUrl
from filelock import FileLock, Timeout
from VideoPlayerUI import VideoPlayerUI


class VideoPlayerLogic(VideoPlayerUI):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.update_counter = 0
        # Check every 10 ticks = ~1 second (timer is 100ms)
        self.update_interval = 10
        self.manual_position_update = False

        # Store transcript segments
        self.transcript_segments = []

        # Connect signals
        self.play_button.clicked.connect(self.toggle_play_pause)
        self.progress_slider.sliderMoved.connect(self.set_video_position)
        self.volume_button.clicked.connect(self.toggle_volume_slider)
        self.volume_slider.valueChanged.connect(self.change_volume)

        # Timer for slider tracking and subtitle updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position_slider)
        self.timer.timeout.connect(self.check_subtitle)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.positionChanged.connect(self.update_position)

        # Set default volume and update icon
        self.audio_output.setVolume(0.5)  # Corresponds to 50% on the slider
        self.update_volume_icon(50)  # Set initial icon based on default volume

    def toggle_volume_slider(self):
        """Show or hide the volume slider when the volume button is clicked"""
        self.volume_slider.setVisible(not self.volume_slider.isVisible())

    def update_volume_icon(self, volume):
        """Update the volume button icon based on the volume level"""
        if volume == 0:
            self.volume_button.setText("🔇")
        elif volume < 50:
            self.volume_button.setText("🔉")
        else:
            self.volume_button.setText("🔊")

    def change_volume(self, value):
        """Adjust the volume based on the slider value and update the icon"""
        self.audio_output.setVolume(value / 100.0)
        self.update_volume_icon(value)

    def load_video(self, video_path, language):
        # Start playing video
        self.media_player.setSource(QUrl.fromLocalFile(video_path))
        self.media_player.play()
        self.timer.start(100)  # Start timer to update slider
        self.play_button.setText("⏸")

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
        # Note: progress_bar is not defined in this version
        pass

    def toggle_play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_button.setText("▶")
        else:
            self.media_player.play()
            self.play_button.setText("⏸")

    def update_duration(self, duration):
        """Set the slider range to the video duration"""
        self.progress_slider.setRange(0, duration)

    def update_position(self, position):
        """Update the slider position as the video plays"""
        if position == 0 and self.media_player.playbackState() == QMediaPlayer.PlayingState:
            print("Warning: Video position reset to 0 unexpectedly")
        if not self.manual_position_update:
            self.progress_slider.setValue(position)

    def update_position_slider(self):
        """Update the slider position periodically"""
        if not self.manual_position_update:
            self.progress_slider.setValue(self.media_player.position())

    def set_video_position(self, position):
        """Seek the video when the slider is moved"""
        self.manual_position_update = True
        self.media_player.setPosition(position)
        QTimer.singleShot(100, self._reset_position_flag)

    def _reset_position_flag(self):
        self.manual_position_update = False
