from database import get_conn


def simulate_biometric_scan(username: str) -> bool:
    """Pretends to read a fingerprint; passes if the user has a registered biometric_id."""
    print(f"[BIOMETRIC] Scanning fingerprint for '{username}'...")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT biometric_id FROM residents WHERE username = ?", (username,)
        ).fetchone()
    if row and row['biometric_id']:
        print("[BIOMETRIC] Match found.")
        return True
    print("[BIOMETRIC] No match.")
    return False


def check_resident(username: str, password: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM residents WHERE username = ? AND password = ?", (username, password)
        ).fetchone()
    return row is not None


def check_visitor(username: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM visitors WHERE username = ? AND temporary_access = 'active'", (username,)
        ).fetchone()
    return row is not None


def log_attempt(username: str, granted: bool, method: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO access_log (username, granted, method) VALUES (?, ?, ?)",
            (username, int(granted), method)
        )
