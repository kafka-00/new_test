
import sys
import subprocess
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit
from PySide6.QtCore import QTimer

class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QUATY Updater & Launcher")
        self.resize(500, 250)

        layout = QVBoxLayout(self)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setText("Click the button to update and launch the application.")

        self.launch_button = QPushButton("Update & Launch QUATY")
        self.launch_button.clicked.connect(self.update_and_launch)
        # Apply some basic styling to the button
        self.launch_button.setStyleSheet("""
            QPushButton {
                background-color: #558055;
                color: #f0f0f0;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #659065;
            }
            QPushButton:pressed {
                background-color: #457045;
            }
        """)

        layout.addWidget(self.log_output)
        layout.addWidget(self.launch_button)

    def run_command(self, command):
        self.log_output.append(f"\n> {' '.join(command)}")
        QApplication.processEvents()
        try:
            # Execute command
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            
            # Display stdout
            if result.stdout:
                self.log_output.append("--- Output ---")
                self.log_output.append(result.stdout)
            
            # Display stderr
            if result.stderr:
                self.log_output.append("--- Warnings/Errors ---")
                self.log_output.append(result.stderr)

            QApplication.processEvents()
            return True
        except subprocess.CalledProcessError as e:
            self.log_output.append("\n--- COMMAND FAILED ---")
            self.log_output.append(e.stdout)
            self.log_output.append(e.stderr)
            return False
        except FileNotFoundError:
            self.log_output.append(f"\n--- ERROR: 'git' command not found ---")
            self.log_output.append("Please ensure Git is installed and in your system's PATH.")
            return False
        except Exception as e:
            self.log_output.append(f"\n--- AN UNEXPECTED ERROR OCCURRED --- \n{str(e)}")
            return False

    def update_and_launch(self):
        self.log_output.clear()
        self.launch_button.setEnabled(False)
        self.launch_button.setText("Updating...")
        
        # Step 1: Git Pull
        update_success = self.run_command(["git", "pull", "origin", "main"])

        if update_success:
            self.log_output.append("\n--- UPDATE SUCCESSFUL ---")
            self.launch_button.setText("Launching...")
            QApplication.processEvents()
            
            # Step 2: Launch main application
            self.log_output.append("\n> Launching main application...")
            subprocess.Popen(["python3", "main.py"])
            
            # Close the launcher after a delay
            self.log_output.append("\nApplication started. This launcher will close automatically.")
            QTimer.singleShot(2000, self.close) # Close after 2 seconds
        else:
            self.log_output.append("\n--- UPDATE FAILED ---")
            self.log_output.append("Could not launch application. Please check the errors above.")
            self.launch_button.setText("Update Failed. Try Again.")
            self.launch_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Try to apply the main stylesheet for consistency
    try:
        with open("stylesheet.qss", "r") as f:
            stylesheet = f.read()
        app.setStyleSheet(stylesheet)
    except FileNotFoundError:
        pass # It's okay if it's not found, we have fallback styles

    window = Launcher()
    window.show()
    sys.exit(app.exec())
