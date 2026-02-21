
import sys
import threading
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
from selenium.common.exceptions import JavascriptException, WebDriverException


class TestAutomationTool(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Test Automation Tool")
        self.driver = None
        self.is_recording = False

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
        self.record_button = QPushButton("Test Recording")
        start_button = QPushButton("Test Start")
        buttons_layout.addWidget(self.record_button)
        buttons_layout.addWidget(start_button)

        main_layout.addLayout(url_layout)
        main_layout.addLayout(buttons_layout)

        save_button.clicked.connect(self.save_url)
        self.record_button.clicked.connect(self.toggle_recording)
        start_button.clicked.connect(self.start_test)

        self.saved_url = ""
        self.recorded_actions = []

    def save_url(self):
        url = self.url_input.text()
        if not url.startswith("https://") and not url.startswith("http://"):
            url = "https://" + url
        self.saved_url = url
        self.url_input.setText(self.saved_url)
        print(f"URL saved: {self.saved_url}")

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if not self.saved_url:
            print("Please enter and save a URL first.")
            return

        print("Start recording test actions...")
        self.is_recording = True
        self.record_button.setText("Stop Recording")
        self.recorded_actions = []  # Clear previous actions

        try:
            options = webdriver.ChromeOptions()
            options.browser_version = 'dev'
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(self.saved_url)

            with open("recorder.js", "r") as f:
                recorder_script = f.read()

            # Start a separate thread to listen for actions
            self.recording_thread = threading.Thread(target=self.listen_for_actions, args=(recorder_script,))
            self.recording_thread.daemon = True
            self.recording_thread.start()

        except Exception as e:
            print(f"Error starting browser: {e}")
            self.stop_recording()

    def listen_for_actions(self, recorder_script):
        while self.is_recording:
            try:
                action = self.driver.execute_async_script(recorder_script)
                if action:
                    self.recorded_actions.append(action)
                    print(f"Action recorded: {action}")
            except (JavascriptException, WebDriverException) as e:
                # This can happen if the page reloads or the browser is closed.
                if self.is_recording:
                    print(f"An error occurred during recording: {e}")
                break
            except Exception as e:
                if self.is_recording:
                    print(f"An unexpected error occurred: {e}")
                break

    def stop_recording(self):
        if not self.is_recording:
            return

        print("...Stopping recording.")
        self.is_recording = False
        self.record_button.setText("Test Recording")
        if self.driver:
            self.driver.quit()
            self.driver = None
        print(f"\n--- Total Actions Recorded: {len(self.recorded_actions)} ---")
        print(self.recorded_actions)
        print("----------------------------------------------------")

    def start_test(self):
        if not self.recorded_actions:
            print("No actions recorded to test. Please record a session first.")
            return
        print("Start running the test...")

    def closeEvent(self, event):
        self.stop_recording()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestAutomationTool()
    window.show()
    sys.exit(app.exec())
