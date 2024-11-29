from PySide6.QtWidgets import QMainWindow, QStackedWidget
from scene1 import Scene1
from scene2 import Scene2
from videoPlayer import VideoPlayer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.resize(800, 600)
        self.setWindowTitle("Video Player with Subtitles")
        self.scene1 = Scene1(self)
        self.scene2 = Scene2(self)
        self.videoPlayer = VideoPlayer(self)
        
        self.stacked_widget.addWidget(self.scene1)
        self.stacked_widget.addWidget(self.scene2)
        self.stacked_widget.addWidget(self.videoPlayer)

    def switch_to_scene2(self, path,language):
        self.scene2.transcript(path,language)
        self.stacked_widget.setCurrentIndex(1)

    def switch_to_VideoPlayer(self, path):
        self.videoPlayer.load_video(path)
        self.stacked_widget.setCurrentIndex(2)




    def switch_to_scene1(self):
        self.stacked_widget.setCurrentIndex(0)