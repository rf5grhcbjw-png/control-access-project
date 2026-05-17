from database import get_conn, BLOCKS, next_reg_code


def add_resident(username: str, password: str, block: str, biometric_id: str = None):
    block = block.upper()
    if block not in BLOCKS:
        return False, f"Invalid block. Valid blocks: {', '.join(BLOCKS)}"
    with get_conn() as conn:
        if conn.execute("SELECT 1 FROM residents WHERE username = ?", (username,)).fetchone():
            return False, "Resident already exists."
        reg_code = next_reg_code(block)
        conn.execute(
            "INSERT INTO residents (username, password, block, biometric_id, reg_code) VALUES (?, ?, ?, ?, ?)",
            (username, password, block, biometric_id, reg_code)
        )
    return True, f"Resident '{username}' registered in Block {block}. Registration code: {reg_code}"


def remove_resident(username: str):
    with get_conn() as conn:
        result = conn.execute("DELETE FROM residents WHERE username = ?", (username,))
        if result.rowcount == 0:
            return False, "Resident not found."
    return True, f"Resident '{username}' removed."


def add_visitor(username: str, block: str, host: str, reason: str):
    block = block.upper()
    if block not in BLOCKS:
        return False, f"Invalid block. Valid blocks: {', '.join(BLOCKS)}"
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO visitors (username, block, host, reason, temporary_access) VALUES (?, ?, ?, ?, 'active')",
            (username, block, host, reason)
        )
    return True, f"Visitor '{username}' registered with active access in Block {block}."


def deactivate_visitor(username: str):
    with get_conn() as conn:
        result = conn.execute(
            "UPDATE visitors SET temporary_access = 'inactive' WHERE username = ?", (username,)
        )
        if result.rowcount == 0:
            return False, "Visitor not found."
    return True, f"Visitor '{username}' access deactivated."


def list_residents_by_block(block: str):
    block = block.upper()
    if block not in BLOCKS:
        print(f"Invalid block. Valid blocks: {', '.join(BLOCKS)}")
        return
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, reg_code, created_at FROM residents WHERE block = ? ORDER BY reg_code",
            (block,)
        ).fetchall()
    if not rows:
        print(f"No residents in Block {block}.")
        return
    print(f"\n--- Block {block} Residents ---")
    for i, row in enumerate(rows, 1):
        print(f"  {i}. {row['username']} | Reg: {row['reg_code']} | Registered: {row['created_at']}")


def list_all_residents():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, block, reg_code FROM residents ORDER BY block, reg_code"
        ).fetchall()
    if not rows:
        print("No residents registered.")
        return
    print("\n--- All Residents by Block ---")
    current_block = None
    counter = 0
    for row in rows:
        if row['block'] != current_block:
            current_block = row['block']
            print(f"\n  Block {current_block}:")
            counter = 0
        counter += 1
        print(f"    {counter}. {row['username']} | Reg: {row['reg_code']}")


def list_all_visitors():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, block, host, temporary_access, created_at FROM visitors ORDER BY block, username"
        ).fetchall()
    if not rows:
        print("No visitors registered.")
        return
    print("\n--- Visitors ---")
    for i, row in enumerate(rows, 1):
        print(f"  {i}. {row['username']} | Block: {row['block']} | Status: {row['temporary_access']} | Host: {row['host']}")
