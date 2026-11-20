from flask import Flask, render_template, jsonify, request
from database import init_db, get_connection
from simulator import add_demo_event
from datetime import datetime

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Create the local SQLite database and sample records on first run.
init_db()


@app.route("/")
def dashboard():
    return render_template("index.html", page="dashboard")


@app.route("/clients")
def clients_page():
    return render_template("clients.html", page="clients")


@app.route("/monitoring")
def monitoring_page():
    return render_template("monitoring.html", page="monitoring")


@app.route("/alerts")
def alerts_page():
    return render_template("alerts.html", page="alerts")


@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html", page="analytics")


@app.route("/settings")
def settings_page():
    return render_template("settings.html", page="settings")


@app.get("/api/stats")
def api_stats():
    con = get_connection()
    clients_total = con.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    clients_online = con.execute("SELECT COUNT(*) FROM clients WHERE status='Online'").fetchone()[0]
    event_total = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    alert_open = con.execute("SELECT COUNT(*) FROM alerts WHERE status='Open'").fetchone()[0]
    con.close()
    return jsonify({
        "clients_total": clients_total,
        "clients_online": clients_online,
        "events_total": event_total,
        "alerts_open": alert_open,
        "server_status": "ONLINE"
    })


@app.get("/api/clients")
def api_clients():
    con = get_connection()
    rows = con.execute("SELECT * FROM clients ORDER BY id DESC").fetchall()
    con.close()
    return jsonify([dict(row) for row in rows])


@app.post("/api/clients")
def api_add_client():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()[:40]
    if not name:
        return jsonify({"error": "Client name is required"}), 400
    con = get_connection()
    count = con.execute("SELECT COUNT(*) FROM clients").fetchone()[0] + 1
    client_id = f"DEMO-{count:03d}"
    con.execute(
        "INSERT INTO clients (client_id, name, ip_address, operating_system, status, last_seen) VALUES (?, ?, ?, ?, 'Online', ?)",
        (client_id, name, "192.0.2.25", "Demo OS", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    con.commit()
    con.close()
    return jsonify({"message": "Demo client added", "client_id": client_id})


@app.post("/api/clients/<int:client_pk>/toggle")
def api_toggle_client(client_pk):
    con = get_connection()
    row = con.execute("SELECT status FROM clients WHERE id=?", (client_pk,)).fetchone()
    if row is None:
        con.close()
        return jsonify({"error": "Client not found"}), 404
    new_status = "Offline" if row["status"] == "Online" else "Online"
    con.execute("UPDATE clients SET status=?, last_seen=? WHERE id=?",
                (new_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), client_pk))
    con.commit()
    con.close()
    return jsonify({"status": new_status})


@app.get("/api/events")
def api_events():
    con = get_connection()
    rows = con.execute("""
        SELECT events.id, events.event_id, clients.client_id, events.timestamp,
               events.interval_seconds, events.result
        FROM events JOIN clients ON clients.id=events.client_pk
        ORDER BY events.id DESC LIMIT 100
    """).fetchall()
    con.close()
    return jsonify([dict(row) for row in rows])


@app.post("/api/demo-event")
def api_demo_event():
    result = add_demo_event()
    return jsonify(result)


@app.get("/api/alerts")
def api_alerts():
    con = get_connection()
    rows = con.execute("SELECT * FROM alerts ORDER BY id DESC").fetchall()
    con.close()
    return jsonify([dict(row) for row in rows])


@app.post("/api/alerts/<int:alert_id>/resolve")
def api_resolve_alert(alert_id):
    con = get_connection()
    cur = con.execute("UPDATE alerts SET status='Resolved' WHERE id=?", (alert_id,))
    con.commit()
    con.close()
    if cur.rowcount == 0:
        return jsonify({"error": "Alert not found"}), 404
    return jsonify({"message": "Alert resolved"})


@app.post("/api/alerts/resolve-all")
def api_resolve_all():
    con = get_connection()
    con.execute("UPDATE alerts SET status='Resolved' WHERE status='Open'")
    con.commit()
    con.close()
    return jsonify({"message": "All alerts resolved"})


@app.get("/api/analytics")
def api_analytics():
    con = get_connection()
    rows = con.execute("""
        SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS total
        FROM events GROUP BY day ORDER BY day
    """).fetchall()
    con.close()
    return jsonify([dict(row) for row in rows])


if __name__ == "__main__":
    # Local-only demo server. It does not listen on the public network.
    app.run(host="127.0.0.1", port=5000, debug=True)
