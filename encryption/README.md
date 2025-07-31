# AMS – Autonomous Monitoring & Supervision

AMS is an intelligent surveillance and attendance management system designed for schools and academies. It leverages real-time face recognition using CCTV/IP cameras, and assigns each student or staff member a unique encrypted ID for automated attendance and monitoring — all without the need for manual input or external databases.

## 🔍 Features

- 🎥 **Live Camera Feeds** (Webcam & IP/RTSP)
- 🧠 **Face Detection & Embedding Extraction**
- 🔐 **Unique Encrypted Key Generation**
- 🗂️ **Local JSON-Based Database**
- ✅ **Automated Attendance Marking**
- 📊 **Real-Time Dashboard with Alerts & Logs**
- 👤 **Student Registration & Retrieval**
- 🚨 **Unknown Face Alerts**

---

## 🛠️ Project Structure

```bash
AMS/
├── dashboard/              # PyQt6-based surveillance GUI
├── embeddings/             # Stores face embeddings as JSON
├── encryption/             # Encryption logic for unique keys
├── faces/                  # Registered face images
├── logs/                   # Attendance and alert logs
├── utils/                  # Helper functions
├── main.py                 # Launch point for the GUI dashboard
└── README.md               # This file

⚙️ How It Works
Face Registration:

Capture student's face via webcam

Generate face embeddings

Create a unique encrypted key using name, register number, and embeddings

Save data locally in a JSON database

Live Monitoring:

Camera feeds are displayed in a grid view

Real-time face matching with stored embeddings

If matched, attendance is marked

If unknown, an alert is triggered

Encryption:

Each face is mapped to a unique, irreversible alphanumeric key

Ensures identity protection and data consistency

📦 Requirements
Python 3.9+

OpenCV

face_recognition

numpy

PyQt6

json

datetime

Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
🖥️ Dashboard Preview
Screenshots or sample UI can be added here.

📁 Local Data Handling
This project does not use any external database. All data is managed securely in local .json files:

known_faces.json: Embeddings and encrypted keys

attendance_log.json: Attendance entries with timestamps

alerts.json: Unknown face alerts

student_details.json: Mapped student metadata

🔐 Encryption Logic
Face embeddings + name + register number → Hashed using SHA-256 (or similar) to generate a consistent, secure key.

🚀 Getting Started
bash
Copy
Edit
cd AMS
python main.py
Use the sidebar in the GUI to:

Register new faces

Monitor live feeds

View attendance logs

Review alerts

🙋‍♂️ Author
Kingston J.

GitHub: @Kingston141

Project Lead: Face encryption, database handling, system architecture

📄 License
This project is open source and available under the MIT License.

🌟 Acknowledgements
Special thanks to:

face_recognition for face processing

The academic staff & peers supporting the development