# encryption_gui_lookup_colored.py

import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtGui import QFont

DB_FILE = r"C:\Users\kings\Desktop\AMS\Encodings and Embeddings\encryption\face_encryption_db.json"

class EncryptionLookupApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔐 Encryption Key Lookup")
        self.setFixedSize(430, 270)
        self.setStyleSheet("""
            QWidget {
                background-color: #e6f2ff;
                font-family: Arial;
            }
            QLineEdit {
                background-color: white;
                color: black;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #a0c4ff;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2679ff;
                color: white;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #005ce6;
            }
            QLabel#title {
                font-size: 18px;
                color: #004d99;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QLabel#result {
                color: #003366;
                font-size: 14px;
                padding-top: 12px;
            }
        """)

        layout = QVBoxLayout()

        self.title = QLabel("🔍 Enter Encryption Key")
        self.title.setObjectName("title")
        layout.addWidget(self.title)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter 16-digit encryption key...")
        layout.addWidget(self.input_field)

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_key)
        layout.addWidget(self.search_btn)

        self.result_label = QLabel("")
        self.result_label.setObjectName("result")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def search_key(self):
        key = self.input_field.text().strip()
        if not key:
            QMessageBox.warning(self, "Input Missing", "Please enter an encryption key.")
            return

        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Database file not found.")
            return

        for entry in data:
            if entry["encryption_key"] == key:
                self.result_label.setText(
                    f"✅ Match Found:\n👤 Name: {entry['name']}\n🔐 Key: {entry['encryption_key']}"
                )
                return

        self.result_label.setText("❌ No match found for this encryption key.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EncryptionLookupApp()
    window.show()
    sys.exit(app.exec())
