
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
from selenium import webdriver

class TestAutomationTool(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Test Automation Tool")
        self.driver = None

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL here...")
        save_button = QPushButton("Save URL")
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(save_button)

        buttons_layout = QHBoxLayout()
        record_button = QPushButton("Test Recording")
        start_button = QPushButton("Test Start")
        buttons_layout.addWidget(record_button)
        buttons_layout.addWidget(start_button)

        main_layout.addLayout(url_layout)
        main_layout.addLayout(buttons_layout)

        save_button.clicked.connect(self.save_url)
        record_button.clicked.connect(self.start_recording)
        start_button.clicked.connect(self.start_test)
        
        self.saved_url = ""

    def save_url(self):
        url = self.url_input.text()
        if not url.startswith("https://") and not url.startswith("http://"):
            url = "https://" + url
        self.saved_url = url
        self.url_input.setText(self.saved_url)
        print(f"URL saved: {self.saved_url}")

    def start_recording(self):
        if not self.saved_url:
            print("Please enter and save a URL first.")
            return
        print("Start recording test actions...")
        
        try:
            options = webdriver.ChromeOptions()
            options.browser_version = 'dev'

            self.driver = webdriver.Chrome(options=options)
            self.driver.get(self.saved_url)

            # --- DIAGNOSTIC CODE START ---
            print("\n--- WebDriver Capabilities ---")
            print(self.driver.capabilities)
            print("----------------------------\n")
            # --- DIAGNOSTIC CODE END ---

        except Exception as e:
            print(f"Error starting browser: {e}")
            print("This may be due to a network issue or permissions. Please check your connection and try again.")


    def start_test(self):
        if not self.saved_url:
            print("Please enter and save a URL first.")
            return
        print("Start running the test...")

    def closeEvent(self, event):
        if self.driver:
            self.driver.quit()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestAutomationTool()
    window.show()
    sys.exit(app.exec())
