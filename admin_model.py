# ============================================================
# admin_model.py — Admin Authentication & Stats
# ============================================================

import bcrypt
from database.db_connection import execute_query


def verify_admin_login(username: str, password: str):
    """
    Username + password check .
    Return: (admin_dict, None)  (None, error_msg)
    """
    admin = execute_query(
        "SELECT id, username, password_hash FROM admins WHERE username=%s",
        (username,), fetch="one"
    )
    if not admin:
        return None, "Username not found."

    stored_hash = admin["password_hash"]

# Comment translated to English.
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("utf-8")

# Comment translated to English.
    if not (stored_hash.startswith(b"$2b$") or stored_hash.startswith(b"$2a$")):
        return None, "Password hash corrupted. Please reset Admin."

    if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        return admin, None
    return None, "Incorrect password."


def get_dashboard_stats():
    """Admin dashboard summary cards  data."""
    total_students = execute_query(
        "SELECT COUNT(*) AS cnt FROM users WHERE status='approved'", fetch="one"
    )["cnt"]
    total_teachers = execute_query(
        "SELECT COUNT(*) AS cnt FROM teachers", fetch="one"
    )["cnt"]
    pending_requests = execute_query(
        "SELECT COUNT(*) AS cnt FROM registration_requests WHERE status='pending'", fetch="one"
    )["cnt"]
    todays_classes = execute_query(
        "SELECT COUNT(*) AS cnt FROM attendance_sessions WHERE session_date=CURDATE()", fetch="one"
    )["cnt"]

    return {
        "total_students":   total_students,
        "total_teachers":   total_teachers,
        "pending_requests": pending_requests,
        "todays_classes":   todays_classes,
    }