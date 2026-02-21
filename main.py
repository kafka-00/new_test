
import sys
import os
import json
import threading
import time
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
    QFileSystemModel
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import JavascriptException, WebDriverException, TimeoutException

# --- Stream Redirection --- #
class Stream(QObject):
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

        self.setWindowTitle("Test Automation Tool")
        self.resize(1000, 700)
        self.driver = None
        self.test_driver = None
        self.is_recording = False
        self.signals = RecordingSignals()
        self.signals.finished.connect(self.handle_recording_finished)
        self.signals.action_recorded.connect(self.add_action_to_table)

        # --- Main Layout (Horizontal Splitter) --- #
        main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main_splitter)

        # --- Left Panel (File Explorer) --- #
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
        # Hide all columns except the name
        for i in range(1, self.file_model.columnCount()):
            self.file_explorer.hideColumn(i)
        main_splitter.addWidget(self.file_explorer)

        # --- Right Panel (Main Content) --- #
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        main_splitter.addWidget(right_panel)

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
        self.delete_button = QPushButton("Delete Step")
        file_ops_layout.addWidget(self.save_button)
        file_ops_layout.addWidget(self.delete_button)
        controls_layout.addLayout(file_ops_layout)
        right_layout.addLayout(controls_layout)

        # --- Content Area (Vertical Splitter) ---
        content_splitter = QSplitter(Qt.Vertical)
        right_layout.addWidget(content_splitter)

        # --- Steps Table ---
        self.steps_table = DeletableTableWidget()
        self.steps_table.setColumnCount(4)
        self.steps_table.setHorizontalHeaderLabels(["Step", "Action", "Selector", "Value"])
        # ... table header setup ...
        content_splitter.addWidget(self.steps_table)

        # --- Log Window ---
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        content_splitter.addWidget(self.log_window)
        content_splitter.setSizes([400, 300])

        main_splitter.setSizes([200, 800]) # Initial size for explorer and main content

        # --- Connections ---
        save_url_button.clicked.connect(self.save_url)
        self.record_button.clicked.connect(self.start_recording)
        self.start_button.clicked.connect(self.start_test)
        self.save_button.clicked.connect(self.save_test)
        self.delete_button.clicked.connect(self.delete_selected_steps)
        self.steps_table.cellChanged.connect(self.update_step_data)
        self.steps_table.delete_triggered.connect(self.delete_selected_steps)
        self.file_explorer.clicked.connect(self.load_test_from_explorer)

        self.saved_url = ""
        self.recorded_actions = []

        self.log_stream = Stream()
        self.log_stream.new_text.connect(self.append_log)
        sys.stdout = self.log_stream
        sys.stderr = self.log_stream

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

    def start_recording(self):
        if not self.saved_url:
            print("Please enter and save a URL first.")
            return
        # ... rest of the function ...

    def listen_for_actions(self, recorder_script):
        # ... same as before ...

    def add_action_to_table(self, action, is_loading=False):
        # ... same as before ...

    def handle_recording_finished(self):
        # ... same as before ...
            
    def delete_selected_steps(self):
        # ... same as before ...

    def update_step_data(self, row, column):
        # ... same as before ...

    def start_test(self):
        # ... same as before ...
            
    def save_test(self):
        if not self.recorded_actions:
            print("No actions to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Test Case", 
            self.test_cases_dir, # Default directory
            "Test Case Files (*.json)"
        )

        if file_path:
            # Ensure the file has a .json extension
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
            print(f"Error loading file: {e}")
        finally:
            self.steps_table.blockSignals(False)

    def closeEvent(self, event):
        # ... same as before ...


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestAutomationTool()
    window.show()
    sys.exit(app.exec())
