from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget, QLineEdit, QCheckBox, QFileDialog
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPalette, QColor
import sys

class Scene1(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.video_path = None

        layout = QVBoxLayout()
        label = QLabel("Please Select The Target Language")
        label.setObjectName("language-label")  # Set an object name
        label.setAlignment(Qt.AlignCenter)  # Center-align the label\

        self.checkbox1 = QCheckBox("Arabic")
        self.checkbox2 = QCheckBox("English")

        # Create a sub-layout to hold the checkboxes
        checkbox_layout = QVBoxLayout()
        checkbox_layout.addWidget(self.checkbox1)
        checkbox_layout.addWidget(self.checkbox2)
        self.checkbox1.stateChanged.connect(
            lambda: self.disable_other_checkbox(self.checkbox1, self.checkbox2))
        self.checkbox2.stateChanged.connect(
            lambda: self.disable_other_checkbox(self.checkbox2, self.checkbox1))

        # Add the label and checkbox sub-layout to the main layout
        layout.addWidget(label, alignment=Qt.AlignCenter)
        layout.addLayout(checkbox_layout)

        # Create Add Media button
        add_button = QPushButton("Add Media")
        add_button.setIcon(QIcon(
            "./skip-to-end-dark-mode-glyph-ui-icon-vector-44134816.jpg"))  # Add your icon
        add_button.setIconSize(QSize(24, 24))
        add_button.clicked.connect(self.load_video)

        layout.addWidget(add_button, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        self.input_field = QLineEdit()
        button = QPushButton("Start")
        button.clicked.connect(self.send_data)

        layout.addWidget(self.input_field)
        layout.addWidget(button)
        self.setLayout(layout)

    def load_video(self):
        file_dialog = QFileDialog(self)
        self.video_path, _ = file_dialog.getOpenFileName(
            self, "Open Video File", "", "Videos (*.mp4 *.avi *.mkv)")
        print(self.video_path)

    def disable_other_checkbox(self, checked_checkbox, other_checkbox):
        if checked_checkbox.isChecked():
            other_checkbox.setChecked(False)
            other_checkbox.setEnabled(False)
        else:
            other_checkbox.setEnabled(True)

    def send_data(self):
        self.main_window.switch_to_scene2(
            self.video_path, self.checkbox2.isChecked())
