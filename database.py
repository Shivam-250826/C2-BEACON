import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join("instance", "c2_beacon_demo.db")


def get_connection():
    os.makedirs("instance", exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = get_connection()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        operating_system TEXT NOT NULL,
        status TEXT NOT NULL,
        last_seen TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL,
        client_pk INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        interval_seconds INTEGER NOT NULL,
        result TEXT NOT NULL,
        FOREIGN KEY(client_pk) REFERENCES clients(id)
    );

    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_code TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        severity TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        status TEXT NOT NULL
    );
    """)
    existing = con.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    if existing == 0:
        now = datetime.now()
        sample_clients = [
            ("LAB-001", "Workstation Alpha", "192.0.2.10", "Windows 11", "Online", now),
            ("LAB-002", "Analyst Laptop", "192.0.2.11", "Windows 10", "Online", now - timedelta(minutes=1)),
            ("LAB-003", "Test Node 03", "192.0.2.12", "Ubuntu 22.04", "Online", now - timedelta(minutes=3)),
            ("LAB-004", "Demo Endpoint 04", "192.0.2.13", "macOS", "Offline", now - timedelta(hours=2)),
            ("LAB-005", "QA Sandbox", "192.0.2.14", "Windows 11", "Online", now - timedelta(minutes=5)),
            ("LAB-006", "Training VM", "192.0.2.15", "Ubuntu 20.04", "Offline", now - timedelta(hours=1)),
            ("LAB-007", "Research Node", "192.0.2.16", "Debian", "Online", now - timedelta(minutes=8)),
            ("LAB-008", "Demo Client 08", "192.0.2.17", "Windows 10", "Online", now - timedelta(minutes=2)),
            ("LAB-009", "Demo Client 09", "192.0.2.18", "macOS", "Offline", now - timedelta(hours=4)),
            ("LAB-010", "Training Client", "192.0.2.19", "Ubuntu 22.04", "Online", now - timedelta(minutes=12)),
            ("LAB-011", "Sandbox Node", "192.0.2.20", "Windows 11", "Offline", now - timedelta(hours=3)),
            ("LAB-012", "Test Endpoint", "192.0.2.21", "Debian", "Online", now - timedelta(minutes=7)),
        ]
        for cid, name, ip, os_name, status, seen in sample_clients:
            con.execute(
                "INSERT INTO clients (client_id,name,ip_address,operating_system,status,last_seen) VALUES (?,?,?,?,?,?)",
                (cid, name, ip, os_name, status, seen.strftime("%Y-%m-%d %H:%M:%S"))
            )

        client_ids = [r["id"] for r in con.execute("SELECT id FROM clients ORDER BY id").fetchall()]
        for i in range(24):
            stamp = now - timedelta(minutes=i * 7)
            client_pk = client_ids[i % len(client_ids)]
            con.execute(
                "INSERT INTO events (event_id,client_pk,timestamp,interval_seconds,result) VALUES (?,?,?,?,?)",
                (f"EVT-{1001+i}", client_pk, stamp.strftime("%Y-%m-%d %H:%M:%S"), 30 if i % 5 else 5,
                 "Delayed" if i % 7 == 0 else "Received")
            )

        sample_alerts = [
            ("ALT-501", "Unusual beacon frequency", "Sample client LAB-003 showed a shorter-than-usual demo interval.", "High", now - timedelta(minutes=12), "Open"),
            ("ALT-502", "Irregular timing pattern", "A fictional endpoint displayed inconsistent sample event timing.", "Medium", now - timedelta(minutes=35), "Open"),
            ("ALT-503", "Inactive demo endpoint", "LAB-004 has not checked in during the sample observation window.", "Low", now - timedelta(hours=1), "Open"),
            ("ALT-504", "Repeated event pattern", "Repeated sample events were included for detection demonstration.", "Medium", now - timedelta(hours=2), "Resolved"),
            ("ALT-505", "Offline endpoint", "LAB-006 is marked offline in the fictional inventory.", "Low", now - timedelta(hours=3), "Open"),
        ]
        for code, title, desc, severity, stamp, status in sample_alerts:
            con.execute(
                "INSERT INTO alerts (alert_code,title,description,severity,timestamp,status) VALUES (?,?,?,?,?,?)",
                (code, title, desc, severity, stamp.strftime("%Y-%m-%d %H:%M:%S"), status)
            )
    con.commit()
    con.close()
