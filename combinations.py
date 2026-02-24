from PyQt6.QtWidgets import * # type: ignore
from PyQt6.QtGui import * # type: ignore
from PyQt6.QtCore import * # type: ignore
import sys
import math


class DarkWindow(QWidget):
    def __init__(self):
        super().__init__()

        # ----- Window setup -----
        self.setWindowTitle("Combinations Calculator")
        self.setFixedSize(380, 360)
        self.setStyleSheet("background-color: #121212;")

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # ----- Title -----
        title = QLabel("C(n, r) Combinations Calculator")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #ffffff;
        """)
        layout.addWidget(title)

        # ----- Input: n -----
        self.n_input = QLineEdit()
        self.n_input.setPlaceholderText("Enter n")
        self.n_input.setStyleSheet(self.input_style())
        layout.addWidget(self.n_input)

        # ----- Input: r -----
        self.r_input = QLineEdit()
        self.r_input.setPlaceholderText("Enter r")
        self.r_input.setStyleSheet(self.input_style())
        layout.addWidget(self.r_input)

        # ----- Calculate button -----
        btn = QPushButton("Calculate")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1f1f1f;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                padding: 12px;
                font-size: 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2b2b2b;
                border: 1px solid #5a5a5a;
            }
        """)
        btn.clicked.connect(self.calculate)
        layout.addWidget(btn)

        # ----- Result -----
        self.result = QLabel(" ")
        self.result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result.setStyleSheet("""
            font-size: 18px;
            color: #cfcfcf;
            padding-top: 10px;
        """)
        layout.addWidget(self.result)

        self.setLayout(layout)

    # Global styling function for inputs
    def input_style(self):
        return """
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                color: #ffffff;
                padding: 10px;
                font-size: 16px;
                border-radius: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #6a6a6a;
            }
        """

    # Calculate factorial combinations
    def calculate(self):
        try:
            n = int(self.n_input.text())
            r = int(self.r_input.text())

            if r > n or n < 0 or r < 0:
                self.show_error("Invalid: r cannot be greater than n.")
                return

            result = math.comb(n, r)

            # --- scientific notation threshold ---
            threshold = 10**10

            if result >= threshold:
                scientific = f"{result:.4e}"    # e.g. "3.6241e+42"
                base, exp = scientific.split("e")
                exp = int(exp)                 # remove leading zeros

                # HTML superscript formatting
                display = f"{base} (10<sup>{exp}</sup>)"
            else:
                display = str(result)

            self.result.setStyleSheet("color: #72e07f; font-size: 20px;")
            self.result.setText(f"Result: {display}")

        except:
            self.show_error("Please enter valid integers.")

    # Unified error styling
    def show_error(self, text):
        self.result.setStyleSheet("color: #e57373; font-size: 18px;")
        self.result.setText(text)


# Run the app
app = QApplication(sys.argv)
window = DarkWindow()
window.show()
sys.exit(app.exec())