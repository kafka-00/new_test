
import sys
import threading
import time
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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import JavascriptException, WebDriverException, TimeoutException


class TestAutomationTool(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Test Automation Tool")
        self.driver = None
        self.test_driver = None # Separate driver for running tests
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
        self.start_button = QPushButton("Test Start")
        buttons_layout.addWidget(self.record_button)
        buttons_layout.addWidget(self.start_button)

        main_layout.addLayout(url_layout)
        main_layout.addLayout(buttons_layout)

        save_button.clicked.connect(self.save_url)
        self.record_button.clicked.connect(self.toggle_recording)
        self.start_button.clicked.connect(self.start_test)

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
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        if not self.saved_url:
            print("Please enter and save a URL first.")
            return
        if self.is_recording:
            print("Recording is already in progress.")
            return

        print("Start recording test actions...")
        self.is_recording = True
        self.record_button.setText("Stop Recording")
        self.start_button.setEnabled(False) # Disable start button during recording
        self.recorded_actions = []

        try:
            options = webdriver.ChromeOptions()
            options.browser_version = 'dev'
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(self.saved_url)

            with open("recorder.js", "r") as f:
                recorder_script = f.read()

            self.recording_thread = threading.Thread(target=self.listen_for_actions, args=(recorder_script,))
            self.recording_thread.daemon = True
            self.recording_thread.start()

        except Exception as e:
            print(f"Error starting browser for recording: {e}")
            self.stop_recording()

    def listen_for_actions(self, recorder_script):
        while self.is_recording:
            try:
                action = self.driver.execute_async_script(recorder_script)
                if action:
                    self.recorded_actions.append(action)
                    print(f"Action recorded: {action}")
            except (JavascriptException, WebDriverException) as e:
                if self.is_recording:
                    print(f"Recording stopped due to an error or page navigation.")
                break

    def stop_recording(self):
        if not self.is_recording:
            return

        print("...Stopping recording.")
        self.is_recording = False
        self.record_button.setText("Test Recording")
        self.start_button.setEnabled(True)
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException:
                pass # Ignore errors if browser is already closed
            self.driver = None
        print(f"\n--- Total Actions Recorded: {len(self.recorded_actions)} ---")
        print(self.recorded_actions)
        print("----------------------------------------------------")

    def start_test(self):
        if not self.recorded_actions:
            print("No actions recorded to test. Please record a session first.")
            return
        if not self.saved_url:
            print("URL not set. Please save a URL before starting a test.")
            return

        print("--- Starting Test Execution ---")
        self.record_button.setEnabled(False)
        self.start_button.setEnabled(False)

        try:
            options = webdriver.ChromeOptions()
            options.browser_version = 'dev'
            self.test_driver = webdriver.Chrome(options=options)
            self.test_driver.get(self.saved_url)
            wait = WebDriverWait(self.test_driver, 10) # 10-second wait for elements

            for i, action in enumerate(self.recorded_actions, 1):
                print(f"Step {i}/{len(self.recorded_actions)}: {action['type']} on '{action['selector']}'")
                try:
                    selector = action['selector']
                    element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

                    if action['type'] == 'click':
                        element.click()
                    elif action['type'] == 'input':
                        element.clear() # Clear the field before typing
                        element.send_keys(action['value'])

                    time.sleep(1) # Wait a moment to observe the action

                except TimeoutException:
                    print(f"  \033[91mError: Element not found or timed out: {action['selector']}\033[0m")
                    break # Stop test on error
                except Exception as e:
                    print(f"  \033[91mAn error occurred during action execution: {e}\033[0m")
                    break

        except Exception as e:
            print(f"\033[91mAn error occurred setting up the test browser: {e}\033[0m")
        finally:
            print("--- Test Execution Finished ---")
            if self.test_driver:
                self.test_driver.quit()
                self.test_driver = None
            self.record_button.setEnabled(True)
            self.start_button.setEnabled(True)

    def closeEvent(self, event):
        self.stop_recording()
        if self.test_driver:
            try:
                self.test_driver.quit()
            except WebDriverException:
                pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestAutomationTool()
    window.show()
    sys.exit(app.exec())
