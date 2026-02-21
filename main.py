
import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
)

class TestAutomationTool(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Test Automation Tool")

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # URL input layout
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL here...")
        save_button = QPushButton("Save URL")
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(save_button)

        # Control buttons layout
        buttons_layout = QHBoxLayout()
        record_button = QPushButton("Test Recording")
        start_button = QPushButton("Test Start")
        buttons_layout.addWidget(record_button)
        buttons_layout.addWidget(start_button)

        # Add all layouts to the main layout
        main_layout.addLayout(url_layout)
        main_layout.addLayout(buttons_layout)

        # Connect signals to slots
        save_button.clicked.connect(self.save_url)
        record_button.clicked.connect(self.start_recording)
        start_button.clicked.connect(self.start_test)
        
        self.saved_url = ""

    def save_url(self):
        self.saved_url = self.url_input.text()
        print(f"URL saved: {self.saved_url}")

    def start_recording(self):
        if not self.saved_url:
            print("Please enter and save a URL first.")
            return
        print("Start recording test actions...")

    def start_test(self):
        if not self.saved_url:
            print("Please enter and save a URL first.")
            return
        print("Start running the test...")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestAutomationTool()
    window.show()
    sys.exit(app.exec())
