from database import get_conn


def print_log():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, granted, method, timestamp FROM access_log ORDER BY timestamp DESC"
        ).fetchall()
    if not rows:
        print("No access attempts recorded.")
        return
    print("\n--- Access Log ---")
    for row in rows:
        status = "GRANTED" if row['granted'] else "DENIED"
        print(f"  [{row['timestamp']}] {row['username']} — {status} ({row['method']})")
