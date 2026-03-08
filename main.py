
import sys
import os
import json
import threading
import time
import traceback
from PySide6.QtCore import Signal, QObject, Qt, QDir
from PySide6.QtGui import QKeySequence, QKeyEvent
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
    QAbstractItemView,
    QTextEdit,
    QSplitter,
    QTreeView,
    QFileSystemModel,
    QCheckBox
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import JavascriptException, WebDriverException, TimeoutException

# --- Stream Redirection for stdout --- #
class Stream(QObject):
    """Redirects console output (stdout) to a QTextEdit widget."""
    new_text = Signal(str)

    def write(self, text):
        self.new_text.emit(str(text))

    def flush(self):
        pass

class RecordingSignals(QObject):
    finished = Signal()
    action_recorded = Signal(dict)

class DeletableTableWidget(QTableWidget):
    delete_triggered = Signal()

    def keyPressEvent(self, event: QKeyEvent):
        is_delete_key = False
        if sys.platform == 'darwin' and event.key() == Qt.Key.Key_Backspace and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            is_delete_key = True
        elif event.key() == Qt.Key.Key_Delete:
            is_delete_key = True

        if is_delete_key:
            self.delete_triggered.emit()
        else:
            super().keyPressEvent(event)

class TestAutomationTool(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("QUATY Automation Tool")
        self.resize(1200, 800)
        self.driver = None
        self.test_driver = None
        self.is_recording = False
        self.is_asserting = False # State for assertion mode
        self.signals = RecordingSignals()
        self.signals.finished.connect(self.handle_recording_finished)
        self.signals.action_recorded.connect(self.add_action_to_table)

        # --- Main Layout -- #
        main_splitter = QSplitter(Qt.Vertical)
        self.setCentralWidget(main_splitter)

        # --- Top Half (File Explorer and Main Content) ---
        top_splitter = QSplitter(Qt.Horizontal)

        # --- Create Widgets First ---

        # Controls (URL, Buttons)
        controls_container = QWidget()
        controls_layout = QVBoxLayout(controls_container)
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL and save before recording...")
        save_url_button = QPushButton("Save URL")
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(save_url_button)
        controls_layout.addLayout(url_layout)

        buttons_layout = QHBoxLayout()
        self.record_button = QPushButton("Start Recording")
        self.record_button.setObjectName("record_button")
        self.start_button = QPushButton("Test Run")
        self.start_button.setObjectName("start_button")
        buttons_layout.addWidget(self.record_button)
        buttons_layout.addWidget(self.start_button)
        controls_layout.addLayout(buttons_layout)

        self.assertion_checkbox = QCheckBox("Assertion Mode")
        self.assertion_checkbox.setObjectName("assertion_checkbox")
        self.assertion_checkbox.setEnabled(True)
        controls_layout.addWidget(self.assertion_checkbox)

        file_ops_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Test")
        self.add_step_button = QPushButton("+ Step")
        self.delete_button = QPushButton("Delete Step")
        file_ops_layout.addWidget(self.save_button)
        file_ops_layout.addWidget(self.add_step_button)
        file_ops_layout.addWidget(self.delete_button)
        controls_layout.addLayout(file_ops_layout)

        # File Explorer (for the Left Panel)
        self.test_cases_dir = os.path.join(os.getcwd(), "test_cases")
        if not os.path.exists(self.test_cases_dir):
            os.makedirs(self.test_cases_dir)
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.test_cases_dir)
        self.file_model.setFilter(QDir.NoDotAndDotDot | QDir.Files)
        self.file_model.setNameFilters(["*.json"])
        self.file_model.setNameFilterDisables(False)
        self.file_explorer = QTreeView()
        self.file_explorer.setModel(self.file_model)
        self.file_explorer.setRootIndex(self.file_model.index(self.test_cases_dir))
        self.file_explorer.setHeaderHidden(True)
        for i in range(1, self.file_model.columnCount()):
            self.file_explorer.hideColumn(i)

        # Steps Table (for the Center Panel)
        self.steps_table = DeletableTableWidget()
        self.steps_table.setColumnCount(4)
        self.steps_table.setHorizontalHeaderLabels(["Step", "Action", "Selector", "Value"])
        self.steps_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        header = self.steps_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.steps_table.setEditTriggers(QAbstractItemView.DoubleClicked)

        # --- Assemble Layout ---

        # Left Panel (File Explorer Only)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.file_explorer)

        # Center Panel (Controls + Steps Table)
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(controls_container)
        center_layout.addWidget(self.steps_table)

        # Add left and center panels to the top splitter
        top_splitter.addWidget(left_panel)
        top_splitter.addWidget(center_panel)
        top_splitter.setSizes([250, 950]) # Adjusted for a smaller file explorer view

        # Bottom Half (Log Window)
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setObjectName("execution_log")

        # Add top splitter and log window to the main splitter
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.log_window)
        main_splitter.setSizes([600, 200])

        # --- Connections ---
        save_url_button.clicked.connect(self.save_url)
        self.record_button.clicked.connect(self.start_recording)
        self.assertion_checkbox.toggled.connect(self.toggle_assertion_mode)
        self.start_button.clicked.connect(self.start_test)
        self.save_button.clicked.connect(self.save_test)
        self.add_step_button.clicked.connect(self.add_manual_step)
        self.delete_button.clicked.connect(self.delete_selected_steps)
        self.steps_table.cellChanged.connect(self.update_step_data)
        self.steps_table.delete_triggered.connect(self.delete_selected_steps)
        self.file_explorer.clicked.connect(self.load_test_from_explorer)

        # --- Instance Variables ---
        self.saved_url = ""
        self.recorded_actions = []

        # Redirect stdout
        self.log_stream = Stream()
        self.log_stream.new_text.connect(self.append_log)
        sys.stdout = self.log_stream

        print("Application started. Logs will appear here.")

    def append_log(self, text):
        self.log_window.moveCursor(self.log_window.textCursor().End)
        self.log_window.insertPlainText(text)
        self.log_window.ensureCursorVisible()

    def save_url(self):
        url = self.url_input.text()
        if not url.startswith("https://") and not url.startswith("http://"):
            url = "https://" + url
        self.saved_url = url
        self.url_input.setText(self.saved_url)
        print(f"URL saved: {self.saved_url}")

    def toggle_assertion_mode(self, checked):
        self.is_asserting = checked
        if checked:
            print("Assertion mode will be active on next recording.")
        else:
            print("Assertion mode deactivated.")

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
        self.assertion_checkbox.setEnabled(False)
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
            print(f"Error starting browser: {e}")
            self.handle_recording_finished()

    def listen_for_actions(self, recorder_script):
        script_with_state = f"window.isAsserting = {str(self.is_asserting).lower()};\n{recorder_script}"

        while self.is_recording:
            try:
                self.driver.current_url
                action = self.driver.execute_async_script(script_with_state)
                if action:
                    self.signals.action_recorded.emit(action)
            except WebDriverException:
                self.is_recording = False
                break
            except JavascriptException:
                pass
        self.signals.finished.emit()

    def add_action_to_table(self, action, is_loading=False):
        self.steps_table.blockSignals(True)
        if not is_loading:
            self.recorded_actions.append(action)

        row_position = self.steps_table.rowCount()
        self.steps_table.insertRow(row_position)

        step_num = QTableWidgetItem(str(row_position + 1))
        action_type = QTableWidgetItem(action.get("type", ""))
        selector = QTableWidgetItem(action.get("selector", ""))
        value = QTableWidgetItem(action.get("value", ""))

        step_num.setFlags(step_num.flags() & ~Qt.ItemIsEditable)
        action_type.setFlags(action_type.flags() & ~Qt.ItemIsEditable)

        self.steps_table.setItem(row_position, 0, step_num)
        self.steps_table.setItem(row_position, 1, action_type)
        self.steps_table.setItem(row_position, 2, selector)
        self.steps_table.setItem(row_position, 3, value)
        self.steps_table.blockSignals(False)

    def add_manual_step(self):
        self.steps_table.blockSignals(True)
        new_action = {"type": "", "selector": "", "value": ""}
        self.recorded_actions.append(new_action)

        row_position = self.steps_table.rowCount()
        self.steps_table.insertRow(row_position)

        step_num = QTableWidgetItem(str(row_position + 1))
        step_num.setFlags(step_num.flags() & ~Qt.ItemIsEditable)

        action_type = QTableWidgetItem("")
        selector = QTableWidgetItem("")
        value = QTableWidgetItem("")

        self.steps_table.setItem(row_position, 0, step_num)
        self.steps_table.setItem(row_position, 1, action_type)
        self.steps_table.setItem(row_position, 2, selector)
        self.steps_table.setItem(row_position, 3, value)
        
        self.steps_table.blockSignals(False)
        print("Added a new empty step. Double-click cells to edit.")

    def handle_recording_finished(self):
        print("...Recording finished.")
        self.is_recording = False
        self.driver = None
        
        self.record_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.assertion_checkbox.setEnabled(True)

        if self.recorded_actions:
            print(f"\n--- Total Actions Recorded: {len(self.recorded_actions)} ---")
        else:
            print("No actions were recorded.")
            
    def delete_selected_steps(self):
        selected_rows_indices = self.steps_table.selectionModel().selectedRows()
        if not selected_rows_indices:
            print("No steps selected to delete.")
            return

        self.steps_table.blockSignals(True)
        rows_to_delete = sorted([index.row() for index in selected_rows_indices], reverse=True)

        for row_index in rows_to_delete:
            self.steps_table.removeRow(row_index)
            self.recorded_actions.pop(row_index)
        
        for i in range(self.steps_table.rowCount()):
            item = self.steps_table.item(i, 0)
            if item:
                item.setText(str(i + 1))
        
        self.steps_table.blockSignals(False)
        print(f"Deleted {len(rows_to_delete)} step(s).")

    def update_step_data(self, row, column):
        if not self.recorded_actions or row >= len(self.recorded_actions):
            return

        new_value = self.steps_table.item(row, column).text()
        key_map = {1: "type", 2: "selector", 3: "value"}

        if column in key_map:
            key_to_update = key_map[column]
            if self.recorded_actions[row].get(key_to_update) != new_value:
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
        self.assertion_checkbox.setEnabled(False)

        try:
            options = webdriver.ChromeOptions()
            options.browser_version = 'dev'
            self.test_driver = webdriver.Chrome(options=options)
            self.test_driver.get(self.saved_url)
            wait = WebDriverWait(self.test_driver, 10)

            for i, action in enumerate(self.recorded_actions, 1):
                action_type = action.get('type', '')
                print(f"Step {i}/{len(self.recorded_actions)}: {action_type} on '{action.get('selector', '')}'")
                
                if action_type.startswith('assert'):
                    print(f"  [Assertion Check] Action: {action_type}, Selector: {action.get('selector')}, Value: {action.get('value')}")
                    time.sleep(1)
                    continue

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
                    print(f"  Error: Element not found: {action['selector']}")
                    break
                except Exception as e:
                    print(f"  Error during action: {e}")
                    break

        except Exception as e:
            print(f"An error occurred during test setup: {e}")
        finally:
            print("--- Test Execution Finished ---")
            if self.test_driver:
                self.test_driver.quit()
            self.record_button.setEnabled(True)
            self.start_button.setEnabled(True)
            self.assertion_checkbox.setEnabled(True)
            
    def save_test(self):
        if not self.recorded_actions:
            print("No actions to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Test Case", 
            self.test_cases_dir,
            "Test Case Files (*.json)"
        )

        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'

            test_case = {
                "url": self.saved_url,
                "actions": self.recorded_actions
            }
            try:
                with open(file_path, 'w') as f:
                    json.dump(test_case, f, indent=4)
                print(f"Test case saved to {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error saving file: {e}")

    def load_test_from_explorer(self, index):
        file_path = self.file_model.filePath(index)
        if not file_path or not os.path.isfile(file_path):
            return

        print(f"--- Loading Test Case from {os.path.basename(file_path)} ---")
        self.steps_table.blockSignals(True)
        self.steps_table.setRowCount(0)

        try:
            with open(file_path, 'r') as f:
                test_case = json.load(f)

            self.saved_url = test_case.get("url", "")
            self.url_input.setText(self.saved_url)
            
            self.recorded_actions = test_case.get("actions", [])
                            
            for action in self.recorded_actions:
                self.add_action_to_table(action, is_loading=True)
            print(f"Test case loaded successfully.")

        except Exception as e:
            print(f"Error loading test case: {e}")
        finally:
            self.steps_table.blockSignals(False)

    def closeEvent(self, event):
        print("Closing application...")
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
        
        sys.stdout = sys.__stdout__
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        with open("stylesheet.qss", "r") as f:
            stylesheet = f.read()
        app.setStyleSheet(stylesheet)
    except FileNotFoundError:
        print("stylesheet.qss not found, using default style.")

    window = TestAutomationTool()

    def handle_exception(exc_type, exc_value, exc_traceback):
        sys.__stderr__.write("\n--- UNCAUGHT EXCEPTION ---\n")
        sys.__stderr__.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        
        if hasattr(window, 'log_window'):
            error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            window.append_log(f"--- UNCAUGHT EXCEPTION ---\n{error_msg}")

    sys.excepthook = handle_exception
    
    window.show()
    sys.exit(app.exec())
