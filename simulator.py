from datetime import datetime
from database import get_connection


def add_demo_event():
    """Add one fictional event to the local demo database."""
    con = get_connection()
    client = con.execute(
        "SELECT id, client_id FROM clients WHERE status='Online' ORDER BY RANDOM() LIMIT 1"
    ).fetchone()
    if client is None:
        con.close()
        return {"message": "No online demo clients available"}
    count = con.execute("SELECT COUNT(*) FROM events").fetchone()[0] + 1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = "Delayed" if count % 4 == 0 else "Received"
    con.execute(
        "INSERT INTO events (event_id,client_pk,timestamp,interval_seconds,result) VALUES (?,?,?,?,?)",
        (f"EVT-{1000+count}", client["id"], timestamp, 30, result)
    )
    con.execute("UPDATE clients SET last_seen=? WHERE id=?", (timestamp, client["id"]))
    con.commit()
    con.close()
    return {"message": "Sample event added", "client_id": client["client_id"], "result": result}
