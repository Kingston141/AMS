# ams_dashboard_final.py
import sys
import random
import sqlite3
import json
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox, QLineEdit, QGridLayout,
    QListWidget
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

DB_NAME = "ams_dashboard_full.db"
CLASS_NAMES = [f"Class {i}" for i in range(1, 11)]
STANDARDS = ["VI", "VII", "VIII", "IX", "X", "XI", "XII"]
CAMERA_ZONES = [
    "Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6",
    "Class 7", "Class 8", "Class 9", "Class 10",
    "Playground", "Library", "Computer Lab", "Entrance", "Corridor", "Principal Office",
    "Parking Lot", "Cafeteria"
]
GENDERS = ["Male", "Female"]
STUDENTS_PER_CLASS = 50

def initialize_db(seed=True):
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
    if seed:
        c.execute("SELECT COUNT(*) FROM students")
        if c.fetchone()[0] == 0:
            surnames = ["Rao", "Kumar", "Patel", "Singh", "Das", "Gupta", "Meena", "Nair", "Iyer", "Joseph"]
            streets = ["MG Road", "Anna Nagar", "Park Street", "Ashok Vihar", "Nehru Colony", "Station Road"]
            for cl in CLASS_NAMES:
                for n in range(1, STUDENTS_PER_CLASS+1):
                    gender = random.choice(GENDERS)
                    std = random.choice(STANDARDS)
                    dob = (datetime(2007,1,1) + timedelta(days=random.randint(0,365*7))).strftime("%Y-%m-%d")
                    surname = random.choice(surnames)
                    fname = "Suresh" if gender == "Male" else "Anil"
                    mname = "Latha" if gender == "Male" else "Sudha"
                    reg_no = f"{cl.replace(' ','')}_{n:03d}"
                    name = f"{'Arun' if gender=='Male' else 'Priya'} {surname}"
                    address = f"{random.randint(1,88)} {random.choice(streets)}, City"
                    status = random.choice(["Present"]*8 + ["Absent", "Late", "Leave"])
                    last_seen = (datetime.now() - timedelta(minutes=random.randint(1,300))).strftime("%Y-%m-%d %H:%M")
                    c.execute("INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (None, name, gender, dob, reg_no, cl, status, last_seen, std, address, fname+" "+surname, mname+" "+surname))
                    student_id = c.lastrowid
                    for day in range(1,8):
                        att_date = (datetime.now() - timedelta(days=7-day)).strftime("%Y-%m-%d")
                        status_a = random.choices(
                            ["Present", "Absent", "Late", "Leave"], [0.7,0.14,0.1,0.06])[0]
                        c.execute("INSERT INTO attendance (student_id, class, status, time) VALUES (?,?,?,?)",
                            (student_id, cl, status_a, f"{att_date} {random.randint(8,16)}:{random.randint(0,59):02d}"))
                # Weekly trends: one per class x week day
                for i in range(7):
                    date = (datetime.now() - timedelta(days=6-i)).strftime("%a")
                    c.execute("INSERT INTO weekly_trend (class, day, present, absent, late, leave) VALUES (?,?,?,?,?,?)",
                        (cl, date, random.randint(35,50), random.randint(0,6), random.randint(2,7), random.randint(0,4)))
        c.execute("SELECT COUNT(*) FROM cameras")
        if c.fetchone()[0] == 0:
            for z in CAMERA_ZONES:
                c.execute("INSERT INTO cameras VALUES (?,?)", (z, ""))
        conn.commit()
    conn.close()

def get_camera_config():
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT zone, ip_address FROM cameras ORDER BY rowid").fetchall()

def update_camera_ip(zone, ip_addr):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE cameras SET ip_address=? WHERE zone=?", (ip_addr, zone))

def get_stats(selected_class=None):
    with sqlite3.connect(DB_NAME) as conn:
        q = "SELECT SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END), "\
            "SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END), "\
            "SUM(CASE WHEN status='Late' THEN 1 ELSE 0 END), "\
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
        out = {"Male":0, "Female":0}
        for g,c in rows: out[g] = c
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
    return [f"{name} ({clas}): {status} at {time}" for name,clas,status,time in rows]

class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(6, 6, 6, 6)
        layout = QVBoxLayout(self)
        # Filters/slicers
        filters = QHBoxLayout()
        self.class_slicer = QComboBox()
        self.class_slicer.addItems(["All"] + CLASS_NAMES)
        self.class_slicer.currentTextChanged.connect(self.refresh)
        self.date_slicer = QComboBox()
        self.date_slicer.addItems(["This Week", "Today"])
        filters.addWidget(QLabel("Class:"))
        filters.addWidget(self.class_slicer)
        filters.addWidget(QLabel("Period:"))
        filters.addWidget(self.date_slicer)
        filters.addStretch()
        layout.addLayout(filters)

        # Mini Stats
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
            lbl.setStyleSheet("background:#f3f7ff;border-radius:9px;padding:7px 10px;color:#334b7c;font-size:13px;")
            ministat_row.addWidget(lbl)
        ministat_row.addStretch()
        layout.addLayout(ministat_row)

        # Summary Cards: small and compact
        self.card_row = QHBoxLayout()
        layout.addLayout(self.card_row)
        # Charts
        self.chart_row = QHBoxLayout()
        layout.addLayout(self.chart_row)
        # Recent events/alerts
        layout.addWidget(QLabel("Recent Events:"), alignment=Qt.AlignmentFlag.AlignLeft)
        self.alist = QListWidget()
        self.alist.setFixedHeight(85)
        layout.addWidget(self.alist)
        self.refresh()

    def refresh(self):
        for i in reversed(range(self.card_row.count())): self.card_row.itemAt(i).widget().setParent(None)
        for i in reversed(range(self.chart_row.count())): self.chart_row.itemAt(i).widget().setParent(None)
        # Data
        clas = self.class_slicer.currentText()
        present, absent, late, leave = get_stats(clas)
        gm, gf = get_genders(clas)
        cards = [
            ("🟢 Present", "#29c46b", present),
            ("🔴 Absent", "#e25353", absent),
            ("🟡 Late", "#f8d53c", late),
            ("🔵 Leave", "#569aff", leave)
        ]
        for label, col, val in cards:
            c = QLabel(f"{label}: {val}")
            c.setStyleSheet(
                f"background:{col};color:white;border-radius:8px;padding:10px 12px;margin:4px;"
                "font-size:14px;font-weight:bold;min-width:90px;max-width:120px;text-align:center;"
            )
            self.card_row.addWidget(c)
        # Pie: Present/Absent/Late/Leave
        fig1, ax1 = plt.subplots(figsize=(2.2,2.2))
        canvas1 = FigureCanvas(fig1)
        ax1.pie([present, absent, late, leave], labels=["Present","Absent","Late","Leave"],
            colors=["#29c46b","#e25353","#f8d53c","#569aff"],autopct='%1.1f%%', startangle=140)
        ax1.axis('equal')
        fig1.subplots_adjust(left=0.15, right=0.85)
        self.chart_row.addWidget(canvas1)
        # Bar: Gender
        fig2, ax2 = plt.subplots(figsize=(2.2,2.2))
        canvas2 = FigureCanvas(fig2)
        ax2.bar(["Male","Female"], [gm,gf], color=["#1f77b4","#f69"])
        ax2.set_title("Gender")
        ax2.set_ylim(bottom=0)
        fig2.subplots_adjust(left=0.17, right=0.83)
        self.chart_row.addWidget(canvas2)
        # Line: Weekly Trend
        weekly = get_weekly(clas)
        fig4, ax4 = plt.subplots(figsize=(2.2,2.2))
        canvas4 = FigureCanvas(fig4)
        if weekly:
            days, pre, absn, latev = zip(*weekly)
            ax4.plot(days, pre, marker='o', color="#29c46b", label="Present")
            ax4.plot(days, absn, marker='o', color="#e25353", label="Absent")
            ax4.plot(days, latev, marker='o', color="#f8d53c", label="Late")
            ax4.legend()
        fig4.subplots_adjust(left=0.19, right=0.81)
        self.chart_row.addWidget(canvas4)
        # Bar: Class Present
        ca = get_class_attendance()
        fig3, ax3 = plt.subplots(figsize=(2.2,2.2))
        canvas3 = FigureCanvas(fig3)
        if ca:
            clss, clv = zip(*ca)
            ax3.bar(clss, clv, color="#266acf")
        fig3.subplots_adjust(left=0.15, right=0.85)
        self.chart_row.addWidget(canvas3)
        # Alerts/recent events
        self.alist.clear()
        for e in get_recent_events():
            self.alist.addItem(e)

class CamerasTab(QWidget):
    def __init__(self):
        super().__init__()
        self.current_page = 0
        self.cams_per_page = 6
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("📷 Camera Zones")
        title.setStyleSheet("font-size:19px;color:#266acf;font-weight:bold;")
        header.addWidget(title)
        header.addStretch()
        self.prev_btn = QPushButton("⏮ Prev")
        self.prev_btn.clicked.connect(lambda: self.change_page(-1))
        header.addWidget(self.prev_btn)
        self.next_btn = QPushButton("Next ⏭")
        self.next_btn.clicked.connect(lambda: self.change_page(1))
        header.addWidget(self.next_btn)
        layout.addLayout(header)
        self.grid = QGridLayout()
        layout.addLayout(self.grid)
        self.refresh()

    def refresh(self):
        # Remove old
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w: w.setParent(None)
        cams = get_camera_config()
        total_pages = (len(cams)+self.cams_per_page-1)//self.cams_per_page
        s = self.current_page*self.cams_per_page
        for idx, (zone, ip) in enumerate(cams[s:s+self.cams_per_page]):
            f = QFrame()
            f.setFixedSize(200, 120)
            f.setStyleSheet("background:#283c52;border-radius:12px;margin:8px;")
            v = QVBoxLayout(f)
            t = QLabel(zone)
            t.setStyleSheet("font-size:14px;color:#54a8ff;font-weight:bold;")
            v.addWidget(t, alignment=Qt.AlignmentFlag.AlignCenter)
            l = QLabel()
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if not ip:
                l.setText("🚫 No Signal\n(click settings to edit IP)")
                l.setStyleSheet("color:#e25353;font-size:14px;font-weight:bold;")
            else:
                l.setText(f"🔴 Live {ip}")
                l.setStyleSheet("color:#29c46b;font-size:14px;font-weight:bold;")
            v.addWidget(l)
            self.grid.addWidget(f, idx//3, idx%3)
        self.prev_btn.setDisabled(self.current_page == 0)
        self.next_btn.setDisabled(self.current_page+1 >= total_pages)

    def change_page(self, d):
        self.current_page += d
        self.refresh()

class StudentsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("👨‍🎓 Students Database")
        title.setStyleSheet("font-size:18px;font-weight:bold;color:#266acf;")
        layout.addWidget(title)
        # Filters
        f = QHBoxLayout()
        self.class_filter = QComboBox()
        self.class_filter.addItems(["All"]+CLASS_NAMES)
        f.addWidget(QLabel("Class:"))
        f.addWidget(self.class_filter)
        self.gender_filter = QComboBox()
        self.gender_filter.addItems(["All"]+GENDERS)
        f.addWidget(QLabel("Gender:"))
        f.addWidget(self.gender_filter)
        f.addStretch()
        layout.addLayout(f)
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID","Name","Gender","Class","Standard","Reg No","DOB","Father Name","Mother Name","Address"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.class_filter.currentTextChanged.connect(self.refresh)
        self.gender_filter.currentTextChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        # Ensure the database exists and is initialized
        initialize_db(seed=True)
        
        cl = self.class_filter.currentText()
        gen = self.gender_filter.currentText()
        with sqlite3.connect(DB_NAME) as conn:
            sql = "SELECT id, name, gender, class, class as standard, reg_no, dob, father, mother, address FROM students"
            wh = []
            args = []
            if cl != "All":
                wh.append("class=?")
                args.append(cl)
            if gen != "All":
                wh.append("gender=?")
                args.append(gen)
            if wh: sql += " WHERE " + " AND ".join(wh)
            students = conn.execute(sql, args).fetchall()
        self.table.setRowCount(0)
        for r, row in enumerate(students):
            self.table.insertRow(r)
            for col, val in enumerate(row):
                itm = QTableWidgetItem(str(val))
                self.table.setItem(r, col, itm)

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        t = QLabel("⚙️ System Settings")
        t.setStyleSheet("font-size:17px;font-weight:bold;color:#266acf;")
        layout.addWidget(t)
        self.cam_grid = QGridLayout()
        self.cams = []
        for idx, (z, ip) in enumerate(get_camera_config()):
            zlabel = QLabel(z)
            zlabel.setStyleSheet("font-weight:bold;color:#266acf;")
            ipl = QLineEdit(ip)
            self.cams.append((z, ipl))
            self.cam_grid.addWidget(zlabel,idx,0)
            self.cam_grid.addWidget(ipl,idx,1)
        layout.addLayout(self.cam_grid)
        sbtn = QPushButton("Save Camera IPs")
        sbtn.clicked.connect(self.save_cams)
        layout.addWidget(sbtn)
        rbtn = QPushButton("Reset / Clear All Data")
        rbtn.clicked.connect(lambda: (initialize_db(seed=True), QMessageBox.information(self,"Reset","Demo data reset!")))
        layout.addWidget(rbtn)
        thm = QPushButton("Toggle Theme (Not Implemented)")
        layout.addWidget(thm)
        layout.addStretch()

    def save_cams(self):
        for z, ipl in self.cams:
            update_camera_ip(z, ipl.text())
        QMessageBox.information(self,"Camera IP","Camera IP addresses saved.")

class AttendanceTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("📒 Attendance Logs")
        title.setStyleSheet("font-size:16px;font-weight:bold;color:#266acf;")
        layout.addWidget(title)
        # Filters
        f = QHBoxLayout()
        self.class_filter = QComboBox()
        self.class_filter.addItems(["All"]+CLASS_NAMES)
        f.addWidget(QLabel("Class:"))
        f.addWidget(self.class_filter)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All","Present","Absent","Late","Leave"])
        f.addWidget(QLabel("Status:"))
        f.addWidget(self.status_filter)
        f.addStretch()
        layout.addLayout(f)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID","Class","Status","Time","Reg No"])
        layout.addWidget(self.table)
        self.class_filter.currentTextChanged.connect(self.refresh)
        self.status_filter.currentTextChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        cl = self.class_filter.currentText()
        st = self.status_filter.currentText()
        with sqlite3.connect(DB_NAME) as conn:
            sql = "SELECT a.id, a.class, a.status, a.time, s.reg_no FROM attendance a JOIN students s ON a.student_id=s.id"
            wh = []
            args = []
            if cl != "All":
                wh.append("a.class=?")
                args.append(cl)
            if st != "All":
                wh.append("a.status=?")
                args.append(st)
            if wh: sql += " WHERE " + " AND ".join(wh)
            sql += " ORDER BY a.time DESC LIMIT 300"
            atts = conn.execute(sql, args).fetchall()
        self.table.setRowCount(0)
        for r, row in enumerate(atts):
            self.table.insertRow(r)
            for col, val in enumerate(row):
                itm = QTableWidgetItem(str(val))
                self.table.setItem(r, col, itm)

class ReportsTab(QWidget):
    def __init__(self):
        super().__init__()
        l = QVBoxLayout(self)
        t = QLabel("📝 Reports & History")
        t.setStyleSheet("font-size:15px;font-weight:bold;color:#266acf;")
        l.addWidget(t)
        l.addWidget(QLabel("• Export as CSV (simulated)\n• Trend and class graphs\n• View attendance and alert history"))
        l.addStretch()
        btn = QPushButton("Export Data (Demo)")
        btn.clicked.connect(lambda: QMessageBox.information(self, "Export", "Export to CSV is a demo placeholder!"))
        l.addWidget(btn)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMS Surveillance Dashboard")
        self.setMinimumSize(1200, 780)
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
                "QPushButton {color:#e4eaf6; background: transparent; font-size:14px; text-align:left;"
                "padding: 9px 17px; border:none; border-radius:7px;}"
                "QPushButton:hover {background:#39516d; color:#fff; font-weight:bold;}")
            if name=="Logout": btn.clicked.connect(QApplication.instance().quit)
            else: btn.clicked.connect(lambda checked, idx=i: self.stack.setCurrentIndex(idx))
            sidebar.addWidget(btn)
        sidebar.addStretch()
        nav_frame = QFrame()
        nav_frame.setStyleSheet("background:#283c52;")
        nav_frame.setFixedWidth(215)
        nav_frame.setLayout(sidebar)
        root_layout.addWidget(nav_frame)
        root_layout.addWidget(self.stack, 3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())
