# 🛡️ AMS – Autonomous Monitoring & Supervision

![Python](https://img.shields.io/badge/Built%20With-Python-blue)
![Face Recognition](https://img.shields.io/badge/AI-Face%20Recognition-brightgreen)
![UI Framework](https://img.shields.io/badge/UI-PyQt6-orange)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 📌 About the Project

> **AMS** is an advanced AI-powered system for **automated surveillance, face recognition, and attendance marking** in schools and academies.  
It transforms traditional CCTV infrastructure into an intelligent, real-time attendance and monitoring system using **face embeddings + encrypted keys**, all handled **locally** without external databases.

---

## 🚀 Key Features

- 🎥 **Live Camera Feed Grid** (Webcam + IP/RTSP support)
- 🧠 **Real-Time Face Detection & Embedding Matching**
- 🔐 **Encrypted Key Generation for Each Face**
- 🧾 **Automated Attendance Logging**
- ⚠️ **Unknown Face Alerts**
- 🗂 **JSON-based Local Data Storage**
- 📊 **Dashboard with Tabs for Monitoring, Logs, and Settings**

---

## 🧠 How It Works

```mermaid
graph TD;
    A[Face Capture] --> B[Face Embedding Generator];
    B --> C[Encrypted Key Generator];
    C --> D[Store in JSON DB];
    E[Live Camera Feed] --> F[Face Matcher];
    F --> G{Match Found?};
    G -- Yes --> H[Mark Attendance];
    G -- No --> I[Trigger Unknown Face Alert];

AMS/
├── dashboard/              # PyQt6 GUI files
├── encryption/             # Key generation logic
├── embeddings/             # Stored face encodings
├── faces/                  # Registered face images
├── logs/                   # Attendance and alerts
├── utils/                  # Helper scripts
├── main.py                 # Run this to launch dashboard
└── README.md               # Project overview

⚙️ Technologies Used
| Category      | Tools/Frameworks          |
| ------------- | ------------------------- |
| Language      | Python 3.9+               |
| GUI Framework | PyQt6                     |
| AI Library    | face\_recognition, OpenCV |
| Encryption    | SHA-256, hashlib          |
| Storage       | JSON (local)              |
