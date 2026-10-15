# ============================================================
# user_model.py — Student CRUD Operations
# ============================================================
# Comment translated to English.
# Comment translated to English.
# Comment translated to English.
#   - Login validation
# ============================================================

from database.db_connection import execute_query


# ── Registration Request ──────────────────────────────────────

def create_registration_request(roll, name, department, semester, shift, phone, face_encoding_bytes):
    """
    Student self-register  registration_requests  insert .
    Admin approve     .
    Return: new row id
    """
# Comment translated to English.
    existing = execute_query(
        "SELECT id, status FROM registration_requests WHERE roll=%s ORDER BY submitted_at DESC LIMIT 1",
        (roll,), fetch="one"
    )
    if existing:
        if existing["status"] == "pending":
            raise ValueError(
                f"A pending request already exists for Roll '{roll}'.")
# Comment translated to English.

# Comment translated to English.
    user = execute_query(
        "SELECT id FROM users WHERE roll=%s", (roll,), fetch="one")
    if user:
        raise ValueError(f"An account with Roll '{roll}' already exists.")

    return execute_query(
        """INSERT INTO registration_requests
           (roll, name, department, semester,shift, phone, face_encoding, status)
           VALUES (%s, %s, %s, %s, %s,%s, %s, 'pending')""",
        (roll, name, department, semester, shift, phone, face_encoding_bytes)
    )


def get_all_pending_requests():
    """Admin pending requests page  ."""
    return execute_query(
        """SELECT id, roll, name, department, semester, shift, phone, submitted_at
           FROM registration_requests WHERE status='pending'
           ORDER BY submitted_at DESC""",
        fetch="all"
    )


def approve_request(request_id: int):
    """
    Admin approve :
      1. registration_requests  data 
      2. users table  insert 
      3. request status = 'approved' 
    """
    req = execute_query(
        "SELECT * FROM registration_requests WHERE id=%s", (request_id,), fetch="one"
    )
    if not req:
        raise ValueError("Request not found.")

# Comment translated to English.
    execute_query(
        """INSERT INTO users (roll, name, department, semester,shift, phone, face_encoding, status)
           VALUES (%s, %s, %s, %s, %s,%s, %s, 'approved')""",
        (req["roll"], req["name"], req["department"],
         req["semester"], req["shift"], req["phone"], req["face_encoding"])
    )

    # request mark as approved
    execute_query(
        "UPDATE registration_requests SET status='approved' WHERE id=%s", (
            request_id,)
    )


def reject_request(request_id: int):
    execute_query(
        "UPDATE registration_requests SET status='rejected' WHERE id=%s", (
            request_id,)
    )


# ── Users Table ───────────────────────────────────────────────

def get_user_by_roll(roll: str):
    return execute_query(
        "SELECT id, roll, name, department, semester,shift, phone, status FROM users WHERE roll=%s",
        (roll,), fetch="one"
    )


def get_user_by_id(user_id: int):
    return execute_query(
        "SELECT id, roll, name, department, semester, shift, phone, status FROM users WHERE id=%s",
        (user_id,), fetch="one"
    )


def get_all_users():
    return execute_query(
        "SELECT id, roll, name, department, semester, shift, phone, status FROM users ORDER BY name",
        fetch="all"
    )


def validate_student_login(roll: str, name: str):
    """
    Student login: roll + name  validate .
    Return: user dict  None
    """
    user = execute_query(
        "SELECT id, roll, name, department, semester, shift, status FROM users WHERE roll=%s",
        (roll,), fetch="one"
    )
    if not user:
        return None, "No account found with this Roll Number."
    if user["name"].strip().lower() != name.strip().lower():
        return None, "Name does not match."
    if user["status"] == "pending":
        return None, "Your account is still awaiting Admin approval."
    if user["status"] == "rejected":
        return None, "Your account has been rejected. Please contact Admin."
    return user, None


def add_user_by_admin(roll, name, department, semester, shift, phone, face_encoding_bytes):
    """Admin directly student add   users  insert ."""
    existing = execute_query(
        "SELECT id FROM users WHERE roll=%s", (roll,), fetch="one")
    if existing:
        raise ValueError(f"An account with Roll '{roll}' already exists.")

    return execute_query(
        """INSERT INTO users (roll, name, department, semester,shift, phone, face_encoding, status)
           VALUES (%s, %s, %s, %s, %s,%s, %s, 'approved')""",
        (roll, name, department, semester, shift, phone, face_encoding_bytes)
    )


def update_user(user_id, name, department, semester, shift, phone):
    execute_query(
        """UPDATE users SET name=%s, department=%s, semester=%s, shift=%s, phone=%s
           WHERE id=%s""",
        (name, department, semester, shift, phone, user_id)
    )


def delete_user(user_id: int):
    execute_query("DELETE FROM users WHERE id=%s", (user_id,))
