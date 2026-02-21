
import sys
import json
import threading
import time
from PySide6.QtCore import Signal, QObject, Qt
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QAbstractItemView
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import JavascriptException, WebDriverException, TimeoutException


class RecordingSignals(QObject):
    finished = Signal()
    action_recorded = Signal(dict)


class TestAutomationTool(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Test Automation Tool")
        self.resize(800, 600)
        self.driver = None
        self.test_driver = None
        self.is_recording = False
        self.signals = RecordingSignals()
        self.signals.finished.connect(self.handle_recording_finished)
        self.signals.action_recorded.connect(self.add_action_to_table)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # --- Controls Layout ---
        controls_layout = QVBoxLayout()
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL and save before recording...")
        save_url_button = QPushButton("Save URL")
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(save_url_button)
        controls_layout.addLayout(url_layout)

        buttons_layout = QHBoxLayout()
        self.record_button = QPushButton("Test Recording")
        self.start_button = QPushButton("Test Start")
        buttons_layout.addWidget(self.record_button)
        buttons_layout.addWidget(self.start_button)
        controls_layout.addLayout(buttons_layout)

        file_ops_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Test")
        self.load_button = QPushButton("Load Test")
        self.delete_button = QPushButton("Delete Step")
        file_ops_layout.addWidget(self.save_button)
        file_ops_layout.addWidget(self.load_button)
        file_ops_layout.addWidget(self.delete_button)
        controls_layout.addLayout(file_ops_layout)

        main_layout.addLayout(controls_layout)

        # --- Steps Table ---
        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(4)
        self.steps_table.setHorizontalHeaderLabels(["Step", "Action", "Selector", "Value"])
        header = self.steps_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.steps_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        main_layout.addWidget(self.steps_table)

        # --- Connections ---
        save_url_button.clicked.connect(self.save_url)
        self.record_button.clicked.connect(self.start_recording)
        self.start_button.clicked.connect(self.start_test)
        self.save_button.clicked.connect(self.save_test)
        self.load_button.clicked.connect(self.load_test)
        self.delete_button.clicked.connect(self.delete_selected_steps)
        self.steps_table.cellChanged.connect(self.update_step_data)

        # --- Shortcuts for Deletion ---
        delete_shortcut_del = QShortcut(QKeySequence.StandardKey.Delete, self)
        delete_shortcut_del.activated.connect(self.delete_selected_steps)

        if sys.platform == 'darwin':
            mac_delete_shortcut = QShortcut(QKeySequence("Meta+Backspace"), self)
            mac_delete_shortcut.activated.connect(self.delete_selected_steps)
        else:
            # For non-macOS, Backspace might also be a convenient delete key
            delete_shortcut_bsp = QShortcut(QKeySequence(Qt.Key.Key_Backspace), self)
            delete_shortcut_bsp.activated.connect(self.delete_selected_steps)

        self.saved_url = ""
        self.recorded_actions = []

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
        if self.is_recording:
            print("Recording is already in progress.")
            return

        print("Start recording... Please close the browser window to stop.")
        self.is_recording = True
        self.record_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.recorded_actions = []
        self.steps_table.setRowCount(0)

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
            self.handle_recording_finished()

    def listen_for_actions(self, recorder_script):
        while self.is_recording:
            try:
                self.driver.current_url
                action = self.driver.execute_async_script(recorder_script)
                if action:
                    self.signals.action_recorded.emit(action)
            except WebDriverException:
                self.is_recording = False
                break
            except JavascriptException:
                pass
        self.signals.finished.emit()

    def add_action_to_table(self, action, is_loading=False):
        if not is_loading:
            self.recorded_actions.append(action)

        row_position = self.steps_table.rowCount()
        self.steps_table.insertRow(row_position)

        step_num = QTableWidgetItem(str(row_position + 1))
        action_type = QTableWidgetItem(action.get("type", ""))
        selector = QTableWidgetItem(action.get("selector", ""))
        value = QTableWidgetItem(action.get("value", ""))

        # Make "Step" and "Action" columns read-only
        step_num.setFlags(step_num.flags() & ~Qt.ItemIsEditable)
        action_type.setFlags(action_type.flags() & ~Qt.ItemIsEditable)

        self.steps_table.setItem(row_position, 0, step_num)
        self.steps_table.setItem(row_position, 1, action_type)
        self.steps_table.setItem(row_position, 2, selector)
        self.steps_table.setItem(row_position, 3, value)

    def handle_recording_finished(self):
        print("...Recording finished.")
        self.is_recording = False
        self.driver = None
        self.record_button.setEnabled(True)
        self.start_button.setEnabled(True)

        if self.recorded_actions:
            print(f"\n--- Total Actions Recorded: {len(self.recorded_actions)} ---")
        else:
            print("No actions were recorded.")
            
    def delete_selected_steps(self):
        selected_rows_indices = self.steps_table.selectionModel().selectedRows()
        if not selected_rows_indices:
            return

        # Block signals to prevent cellChanged from firing during row removal
        self.steps_table.blockSignals(True)
        rows_to_delete = sorted(list(set(index.row() for index in selected_rows_indices)), reverse=True)

        for row_index in rows_to_delete:
            self.steps_table.removeRow(row_index)
            self.recorded_actions.pop(row_index)
        
        # Re-number the steps
        for i in range(self.steps_table.rowCount()):
            self.steps_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
        
        self.steps_table.blockSignals(False)
        print(f"Deleted {len(rows_to_delete)} step(s).")

    def update_step_data(self, row, column):
        # Ensure the action list is not empty and row is within bounds
        if not self.recorded_actions or row >= len(self.recorded_actions):
            return

        new_value = self.steps_table.item(row, column).text()
        key_map = {2: "selector", 3: "value"}

        if column in key_map:
            key_to_update = key_map[column]
            if self.recorded_actions[row][key_to_update] != new_value:
                self.recorded_actions[row][key_to_update] = new_value
                print(f"Updated Step {row + 1}: Set '{key_to_update}' to '{new_value}'")

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
            wait = WebDriverWait(self.test_driver, 10)

            for i, action in enumerate(self.recorded_actions, 1):
                print(f"Step {i}/{len(self.recorded_actions)}: {action['type']} on '{action['selector']}'")
                try:
                    selector = action['selector']
                    element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

                    if action['type'] == 'click':
                        element.click()
                    elif action['type'] == 'input':
                        element.clear()
                        element.send_keys(action['value'])

                    time.sleep(1)

                except TimeoutException:
                    print(f"  \033[91mError: Element not found: {action['selector']}\033[0m")
                    break
                except Exception as e:
                    print(f"  \033[91mError during action: {e}\033[0m")
                    break

        except Exception as e:
            print(f"\033[91mAn error occurred setting up the test browser: {e}\033[0m")
        finally:
            print("--- Test Execution Finished ---")
            if self.test_driver:
                self.test_driver.quit()
            self.record_button.setEnabled(True)
            self.start_button.setEnabled(True)
            
    def save_test(self):
        if not self.recorded_actions:
            print("No actions to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Test Case", 
            "", 
            "Test Case Files (*.json);;All Files (*)"
        )

        if file_path:
            test_case = {
                "url": self.saved_url,
                "actions": self.recorded_actions
            }
            try:
                with open(file_path, 'w') as f:
                    json.dump(test_case, f, indent=4)
                print(f"Test case saved to {file_path}")
            except Exception as e:
                print(f"Error saving file: {e}")

    def load_test(self):
        self.steps_table.blockSignals(True) # Block signals during load
        self.steps_table.setRowCount(0)

        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Load Test Case", 
            "", 
            "Test Case Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    test_case = json.load(f)

                self.saved_url = test_case.get("url", "")
                self.url_input.setText(self.saved_url)
                
                self.recorded_actions = test_case.get("actions", [])
                                
                print("--- Loading Test Case ---")
                for action in self.recorded_actions:
                    self.add_action_to_table(action, is_loading=True)
                print(f"Test case loaded from {file_path}")

            except Exception as e:
                print(f"Error loading file: {e}")
        self.steps_table.blockSignals(False) # Unblock signals after load

    def closeEvent(self, event):
        self.is_recording = False
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException:
                pass
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
