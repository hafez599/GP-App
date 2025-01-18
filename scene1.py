from PySide6.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QCheckBox, QFileDialog
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QFontDatabase


class Scene1(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.video_path = None

        # Load the custom font
        font_id = QFontDatabase.addApplicationFont(
            'DancingScript-VariableFont_wght.ttf')

        # Check if the font was successfully loaded
        if font_id == -1:
            print("Failed to load font!")
        else:
            # Get the font family name (it might be different from the font file name)
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

        # Create a QFont object and set the font properties
        font = QFont()
        font.setFamily(font_family)  # Set the font family
        font.setPointSize(36)    # Set the font size
        font.setBold(True)       # Set the font to bold
        font.setItalic(False)    # Set the font to not italic
        font.setUnderline(False)  # Set the font to not underlined

        layout = QVBoxLayout()
        label = QLabel("Please Select The Target Language")
        # Apply the font to the label
        label.setFont(font)
        label.setObjectName("language-label")  # Set an object name
        label.setAlignment(Qt.AlignCenter)  # Center-align the label\

        self.checkbox1 = QCheckBox("Arabic")
        self.checkbox2 = QCheckBox("English")

        # Create a sub-layout to hold the checkboxes
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.checkbox1)
        checkbox_layout.addWidget(self.checkbox2)
        self.checkbox1.stateChanged.connect(
            lambda: self.disable_other_checkbox(self.checkbox1, self.checkbox2))
        self.checkbox2.stateChanged.connect(
            lambda: self.disable_other_checkbox(self.checkbox2, self.checkbox1))

        # Add the label and checkbox sub-layout to the main layout
        layout.addWidget(label, alignment=Qt.AlignCenter)
        layout.addLayout(checkbox_layout, Qt.AlignCenter)

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
