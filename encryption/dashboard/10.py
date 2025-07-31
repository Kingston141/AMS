
import sys
import random
import sqlite3
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QStackedWidget, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QLineEdit, QListWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import cv2
from PyQt6.QtGui import QImage, QPixmap


DB_NAME = "ams_dashboard_full.db"
CLASS_NAMES = [f"Class {i}" for i in range(1, 11)]
CAMERA_ZONES = [
    "Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6",
    "Class 7", "Class 8", "Class 9", "Class 10",
    "Playground", "Library", "Computer Lab", "Entrance", "Corridor", "Principal Office",
    "Parking Lot", "Cafeteria"
]
STATUSES = ["Present", "Absent", "Late", "Leave"]
GENDERS = ["Male", "Female"]
STUDENTS_PER_CLASS = 50

# --- DATABASE UTILS ---
def initialize_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY, name TEXT, gender TEXT, dob TEXT, reg_no TEXT, class TEXT,
        status TEXT, last_seen TEXT, standard TEXT, address TEXT, father TEXT, mother TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY, student_id INTEGER, class TEXT, status TEXT, time TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS weekly_trend (
        id INTEGER PRIMARY KEY, class TEXT, day TEXT, present INTEGER, absent INTEGER, late INTEGER, leave INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS cameras (
        zone TEXT PRIMARY KEY, ip_address TEXT
    )""")
    conn.commit()
    if c.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        surnames = ["Rao", "Kumar", "Patel", "Singh", "Das", "Gupta", "Meena", "Nair", "Iyer", "Joseph"]
        male_first_names = ["Arun", "Suresh", "Rahul", "Vikram", "Amit", "Rohan", "Karthik", "Manoj", "Deepak", "Sanjay", "Ajay", "Ravi", "Prakash", "Sunil", "Vivek"]
        female_first_names = ["Priya", "Anita", "Latha", "Sudha", "Neha", "Divya", "Pooja", "Sneha", "Kavya", "Meera", "Asha", "Ritu", "Shreya", "Nisha", "Swati"]
        male_father_names = ["Suresh", "Rajesh", "Mahesh", "Ramesh", "Vijay", "Satish", "Anil", "Pradeep", "Naresh", "Dinesh"]
        female_mother_names = ["Latha", "Sudha", "Meena", "Kavitha", "Sunitha", "Radha", "Anjali", "Deepa", "Shobha", "Geetha"]
        streets = ["MG Road", "Anna Nagar", "Park Street", "Ashok Vihar", "Nehru Colony", "Station Road"]
        for cl in CLASS_NAMES:
            for n in range(1, STUDENTS_PER_CLASS+1):
                gender = random.choice(GENDERS)
                std = str(random.randint(6,12))
                dob = (datetime(2007, 1, 1) + timedelta(days=random.randint(0, 2600))).strftime("%Y-%m-%d")
                surname = random.choice(surnames)
                if gender == "Male":
                    fname = random.choice(male_first_names)
                    father = random.choice(male_father_names) + " " + surname
                    mother = random.choice(female_mother_names) + " " + surname
                else:
                    fname = random.choice(female_first_names)
                    father = random.choice(male_father_names) + " " + surname
                    mother = random.choice(female_mother_names) + " " + surname
                reg_no = f"{cl.replace(' ', '')}_{n:03d}"
                name = f"{fname} {surname}"
                address = f"{random.randint(1, 88)} {random.choice(streets)}, City"
                status = random.choice(["Present"] * 8 + ["Absent", "Late", "Leave"])
                last_seen = (datetime.now() - timedelta(minutes=random.randint(1, 300))).strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                          (None, name, gender, dob, reg_no, cl, status, last_seen, std, address, father, mother))
                student_id = c.lastrowid
                for day in range(1, 8):
                    att_date = (datetime.now() - timedelta(days=7-day)).strftime("%Y-%m-%d")
                    status_a = random.choices(["Present", "Absent", "Late", "Leave"], [0.7, 0.14, 0.1, 0.06])[0]
                    c.execute("INSERT INTO attendance (student_id, class, status, time) VALUES (?,?,?,?)",
                              (student_id, cl, status_a, f"{att_date} {random.randint(8,16)}:{random.randint(0, 59):02d}"))
            for i in range(7):
                date = (datetime.now() - timedelta(days=6-i)).strftime("%a")
                c.execute("INSERT INTO weekly_trend (class, day, present, absent, late, leave) VALUES (?,?,?,?,?,?)",
                          (cl, date, random.randint(35, 50), random.randint(0, 6), random.randint(2, 7), random.randint(0, 4)))
        if c.execute("SELECT COUNT(*) FROM cameras").fetchone()[0] == 0:
            for z in CAMERA_ZONES:
                c.execute("INSERT INTO cameras VALUES (?,?)", (z, ""))
    conn.commit()
    conn.close()

def get_camera_config():
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT zone, ip_address FROM cameras ORDER BY rowid").fetchall()
def get_stats(selected_class=None):
    with sqlite3.connect(DB_NAME) as conn:
        q = "SELECT SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END), " \
            "SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END), " \
            "SUM(CASE WHEN status='Late' THEN 1 ELSE 0 END), " \
            "SUM(CASE WHEN status='Leave' THEN 1 ELSE 0 END) FROM students"
        if selected_class and selected_class != "All":
            r = conn.execute(q + " WHERE class=?", (selected_class,)).fetchone()
        else:
            r = conn.execute(q).fetchone()
        return tuple(map(lambda x: x or 0, r))
def get_genders(selected_class=None):
    with sqlite3.connect(DB_NAME) as conn:
        if selected_class and selected_class != "All":
            rows = conn.execute("SELECT gender, COUNT(*) FROM students WHERE class=? GROUP BY gender", (selected_class,)).fetchall()
        else:
            rows = conn.execute("SELECT gender, COUNT(*) FROM students GROUP BY gender").fetchall()
        out = {"Male": 0, "Female": 0}
        for g, c in rows:
            out[g] = c
        return out["Male"], out["Female"]
def get_weekly(selected_class=None):
    with sqlite3.connect(DB_NAME) as conn:
        if selected_class and selected_class != "All":
            q = "SELECT day, SUM(present), SUM(absent), SUM(late) FROM weekly_trend WHERE class=? GROUP BY day ORDER BY id"
            data = conn.execute(q, (selected_class,)).fetchall()
        else:
            q = "SELECT day, SUM(present), SUM(absent), SUM(late) FROM weekly_trend GROUP BY day ORDER BY id"
            data = conn.execute(q).fetchall()
    return data
def get_class_attendance():
    with sqlite3.connect(DB_NAME) as conn:
        data = conn.execute("SELECT class, COUNT(*) FROM students WHERE status='Present' GROUP BY class").fetchall()
    return data
def get_recent_events(limit=8):
    with sqlite3.connect(DB_NAME) as conn:
        rows = conn.execute("SELECT s.name, s.class, a.status, a.time FROM attendance a JOIN students s ON a.student_id=s.id ORDER BY a.time DESC LIMIT ?", (limit,)).fetchall()
    return [f"{name} ({clas}): {status} at {time}" for name, clas, status, time in rows]

# --- DASHBOARD ---
class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        # Filters
        filters = QHBoxLayout()
        self.class_slicer = QComboBox()
        self.class_slicer.addItems(["All"] + CLASS_NAMES)
        self.class_slicer.currentTextChanged.connect(self.refresh)
        filters.addWidget(QLabel("Class:"))
        filters.addWidget(self.class_slicer)
        filters.addStretch()
        layout.addLayout(filters)
        # Mini-stats row
        ministat_row = QHBoxLayout()
        mini_labels = [
            ("Active Cameras", len([i for z,i in get_camera_config() if i])),
            ("Total Cameras", len(CAMERA_ZONES)),
            ("Unknown Alerts", random.randint(0,8)),
            ("Attendance Rate", f"{random.randint(80,99)}%"),
            ("System Uptime", f"{random.randint(2,8)}d {random.randint(0,24)}h")
        ]
        for k,v in mini_labels:
            lbl = QLabel(f"{k}: {v}")
            lbl.setStyleSheet("background:#e8f3fc;border-radius:6px;padding:6px 10px;color:#265b82;font-size:13px;")
            ministat_row.addWidget(lbl)
        ministat_row.addStretch()
        layout.addLayout(ministat_row)

        # Unified grid for cards and analytics (6 columns, no gaps, equal size, white bg)
        grid_frame = QFrame()
        grid_frame.setStyleSheet("background:#fff; border-radius:13px; margin:0; padding:0;")
        grid_layout = QVBoxLayout(grid_frame)
        grid_layout.setContentsMargins(0,0,0,0)
        self.top_grid = QGridLayout()
        self.top_grid.setHorizontalSpacing(0)
        self.top_grid.setVerticalSpacing(0)
        self.top_grid.setContentsMargins(0,0,0,0)
        for i in range(6):
            self.top_grid.setColumnStretch(i, 1)
        grid_layout.addLayout(self.top_grid)
        layout.addWidget(grid_frame)
        # Recent events/alerts
        layout.addWidget(QLabel("Recent Events:"), alignment=Qt.AlignmentFlag.AlignLeft)
        self.alist = QListWidget()
        self.alist.setFixedHeight(95)
        layout.addWidget(self.alist)
        self.setLayout(layout)
        self.refresh()

    def refresh(self):
        # Clear old widgets
        # Clear old widgets
        for i in reversed(range(self.top_grid.count())):
            w = self.top_grid.itemAt(i).widget()
            if w:
                w.setParent(None)
        # Summary cards (Present, Absent, Late, Leave - compact, equal, modern)
        present, absent, late, leave = get_stats(self.class_slicer.currentText())
        cards = [
            ("🟢 Present", "#29c46b", present),
            ("🔴 Absent", "#e25353", absent),
            ("🟡 Late", "#fbc531", late),
            ("🔵 Leave", "#569aff", leave)
        ]
        for idx, (label, color, value) in enumerate(cards):
            frame = QFrame()
            frame.setStyleSheet(f"background:{color}; color:white; border-radius:10px; border:1.5px solid #e6e6e6; min-width:0; min-height:0; margin:0; padding:0; box-shadow:0 2px 8px #e6e6e6;")
            frame.setFixedHeight(80)
            frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            v = QVBoxLayout(frame)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(0)
            big = QLabel(f"{value}")
            big.setStyleSheet("font-size:22px;font-weight:600;color:white; margin-bottom:0px;")
            txt = QLabel(label)
            txt.setStyleSheet("font-size:13px;font-weight:500;color:white; margin-top:0px;")
            big.setAlignment(Qt.AlignmentFlag.AlignCenter)
            txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(big)
            v.addWidget(txt)
            self.top_grid.addWidget(frame, 0, idx)
        # Analytics widgets: Gender pie, Classwise bar, Status pie
        gm, gf = get_genders(self.class_slicer.currentText())
        fig_g, ax_g = plt.subplots(figsize=(2.1,2.1))
        canvas_g = FigureCanvas(fig_g)
        ax_g.pie([gm, gf], labels=["Male", "Female"], colors=["#4292f7", "#f693ce"], autopct='%1.0f%%', startangle=135)
        ax_g.set_title("Gender Mix", fontsize=10)
        fig_g.tight_layout()
        canvas_g.setStyleSheet("background:#fff; border-radius:10px; border:1.5px solid #e6e6e6; margin:0; padding:0;")
        self.top_grid.addWidget(canvas_g, 0, 4)
        class_att = get_class_attendance()
        fig_c, ax_c = plt.subplots(figsize=(2.1,2.1))
        canvas_c = FigureCanvas(fig_c)
        if class_att:
            cls, clsvals = zip(*class_att)
            ax_c.bar(cls, clsvals, color="#2677c4")
        ax_c.set_title("Classwise Presence", fontsize=10)
        fig_c.tight_layout()
        canvas_c.setStyleSheet("background:#fff; border-radius:10px; border:1.5px solid #e6e6e6; margin:0; padding:0;")
        self.top_grid.addWidget(canvas_c, 0, 5)
        # Status pie (Present/Absent/Late/Leave)
        fig_s, ax_s = plt.subplots(figsize=(2.1,2.1))
        canvas_s = FigureCanvas(fig_s)
        ax_s.pie([present, absent, late, leave], labels=["Present", "Absent", "Late", "Leave"],
                 colors=["#29c46b", "#e25353", "#fbc531", "#569aff"], autopct='%1.0f%%', startangle=140)
        ax_s.set_title("Status Split", fontsize=10)
        fig_s.tight_layout()
        canvas_s.setStyleSheet("background:#fff; border-radius:10px; border:1.5px solid #e6e6e6; margin:0; padding:0;")
        self.top_grid.addWidget(canvas_s, 1, 0, 1, 2)
        # Weekly trend line chart (wide, below)
        weekly = get_weekly(self.class_slicer.currentText())
        fig3, ax3 = plt.subplots(figsize=(6.5,2.5))
        canvas3 = FigureCanvas(fig3)
        if weekly:
            days, pre, absn, latev = zip(*weekly)
            ax3.plot(days, pre, marker='o', color="#29c46b", label="Present")
            ax3.plot(days, absn, marker='o', color="#e25353", label="Absent")
            ax3.plot(days, latev, marker='o', color="#fbc531", label="Late")
            ax3.set_title("Weekly Trend", fontsize=12)
            ax3.legend()
        fig3.tight_layout()
        canvas3.setStyleSheet("background:#fff; border-radius:10px; border:1.5px solid #e6e6e6; margin:0; padding:0;")
        self.top_grid.addWidget(canvas3, 1, 2, 1, 4)
        # Recent events
        self.alist.clear()
        for e in get_recent_events():
            self.alist.addItem(e)

# --- CAMERA PAGE with COLORFUL TILES ---
class CameraTile(QFrame):
    tile_colors = [
        "#f8cec3", "#e6faff", "#fff5cc", "#ffdbf0", "#d1fbe1", "#d8eaff",
        "#f5e1c0", "#e3cfff", "#f9ebeb", "#e0feea", "#e0e8fc", "#f9edda",
        "#cce7ff", "#f7d3f6", "#e4ffd9", "#e2f5fc", "#ffe0e0", "#e0ffd8"
    ]
    def __init__(self, zone, idx, is_webcam=False):
        super().__init__()
        color = CameraTile.tile_colors[idx % len(CameraTile.tile_colors)]
        self.setStyleSheet(
            f"background:{color}; border:3.2px solid #2973cf; border-radius:15px; margin:0;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0)
        if is_webcam:
            self.feed = QLabel()
            self.feed.setMinimumHeight(190)
            self.cap = cv2.VideoCapture(0)
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.next_frame)
            self.timer.start(40)
            v.addWidget(self.feed, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            lbl = QLabel("🚫 No Signal")
            lbl.setStyleSheet("color:#e25353; font-size:26px; font-weight:bold;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        zone_lbl = QLabel(zone)
        zone_lbl.setStyleSheet(
            "background:#202836; color:#fff; font-size:16px; font-weight:bold; padding:10px 15px; border-bottom-left-radius:10px; border-bottom-right-radius:10px;")
        v.addWidget(zone_lbl, alignment=Qt.AlignmentFlag.AlignBottom)
    def next_frame(self):
        ok, frame = self.cap.read()
        if ok:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h,w,ch = frame.shape
            img = QImage(frame.data, w, h, w*ch, QImage.Format.Format_RGB888)
            self.feed.setPixmap(QPixmap.fromImage(img).scaled(345,190, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

class CamerasTab(QWidget):
    def __init__(self):
        super().__init__()
        self.cams_per_page = 6
        self.current_page = 0
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("📷 Camera Wall")
        title.setStyleSheet("font-size:17px;color:#2677c4;font-weight:bold;")
        header.addWidget(title)
        header.addStretch()
        self.prev_btn = QPushButton("Prev")
        self.prev_btn.clicked.connect(lambda: self.change_page(-1))
        header.addWidget(self.prev_btn)
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(lambda: self.change_page(1))
        header.addWidget(self.next_btn)
        layout.addLayout(header)
        self.grid = QGridLayout()
        self.grid.setContentsMargins(0,0,0,0)
        self.grid.setHorizontalSpacing(20)
        self.grid.setVerticalSpacing(20)
        layout.addLayout(self.grid)
        self.refresh()
    def refresh(self):
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.setParent(None)
        cams = CAMERA_ZONES
        idx0 = self.current_page * self.cams_per_page
        for idx in range(self.cams_per_page):
            zidx = idx0 + idx
            if zidx < len(cams):
                tile = CameraTile(cams[zidx], zidx, is_webcam=(self.current_page == 0 and idx == 0))
                self.grid.addWidget(tile, idx // 3, idx % 3)
        for r in range(2): self.grid.setRowStretch(r, 1)
        for c in range(3): self.grid.setColumnStretch(c, 1)
        self.prev_btn.setDisabled(self.current_page == 0)
        self.next_btn.setDisabled(self.current_page >= (len(cams)-1)//self.cams_per_page)
    def change_page(self, d): self.current_page += d; self.refresh()

# --- Placeholder tab classes ---
class AttendanceTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Attendance Records")
        title.setStyleSheet("font-size:17px;color:#2677c4;font-weight:bold;")
        layout.addWidget(title)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Class", "Status", "Time"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.refresh()
    def refresh(self):
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute("SELECT s.name, s.class, a.status, a.time FROM attendance a JOIN students s ON a.student_id=s.id ORDER BY a.time DESC LIMIT 100").fetchall()
        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

class ReportsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Attendance Summary by Class")
        title.setStyleSheet("font-size:17px;color:#2677c4;font-weight:bold;")
        layout.addWidget(title)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Class", "Present", "Absent", "Late", "Leave"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.refresh()
    def refresh(self):
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute("SELECT class, SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END), SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END), SUM(CASE WHEN status='Late' THEN 1 ELSE 0 END), SUM(CASE WHEN status='Leave' THEN 1 ELSE 0 END) FROM students GROUP BY class ORDER BY class").fetchall()
        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

class StudentsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Student Directory")
        title.setStyleSheet("font-size:17px;color:#2677c4;font-weight:bold;")
        layout.addWidget(title)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Name", "Gender", "Class", "Reg No", "Status", "Last Seen", "Address"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.refresh()
    def refresh(self):
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute("SELECT name, gender, class, reg_no, status, last_seen, address FROM students ORDER BY class, name").fetchall()
        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("SettingsTab Placeholder"))

# --- OTHER TABS (Your previous versions) ---
# StudentsTab, AttendanceTab, SettingsTab, ReportsTab all as you had them before

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMS Surveillance Dashboard")
        self.setMinimumSize(1500, 900)
        initialize_db()
        root_widget = QWidget()
        root_layout = QHBoxLayout(root_widget)
        self.setCentralWidget(root_widget)
        sidebar = QVBoxLayout()
        navs = [
            ("Dashboard", "📊"),
            ("Cameras", "📷"),
            ("Attendance", "📒"),
            ("Reports", "📝"),
            ("Students", "👨‍🎓"),
            ("Settings", "⚙️"),
            ("Logout", "🚪")
        ]
        self.stack = QStackedWidget()
        self.tabs = [
            DashboardTab(),
            CamerasTab(),
            AttendanceTab(),
            ReportsTab(),
            StudentsTab(),
            SettingsTab()
        ]
        for w in self.tabs:
            self.stack.addWidget(w)
        for i, (name, icon) in enumerate(navs):
            btn = QPushButton(f"{icon}  {name}")
            btn.setStyleSheet(
                "QPushButton {color:#e4eaf6; background: transparent; font-size:16px; text-align:left;"
                "padding:13px 19px; border:none; border-radius:10px;}"
                "QPushButton:hover {background:#39516d; color:#fff; font-weight:bold;}")
            if name == "Logout": btn.clicked.connect(QApplication.instance().quit)
            else: btn.clicked.connect(lambda checked, idx=i: self.stack.setCurrentIndex(idx))
            sidebar.addWidget(btn)
        sidebar.addStretch()
        nav_frame = QFrame()
        nav_frame.setStyleSheet("background:#283c52;")
        nav_frame.setFixedWidth(235)
        nav_frame.setLayout(sidebar)
        root_layout.addWidget(nav_frame)
        root_layout.addWidget(self.stack, 3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.showMaximized()
    sys.exit(app.exec())
