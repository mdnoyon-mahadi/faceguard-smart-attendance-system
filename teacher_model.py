# ============================================================
# teacher_model.py — Teacher CRUD Operations
# ============================================================

from database.db_connection import execute_query


def add_teacher(name, department, designation, face_encoding_bytes, teacher_id: str = ""):
    # Teacher ID unique check
    if teacher_id:
        existing_id = execute_query(
            "SELECT id FROM teachers WHERE teacher_id=%s",
            (teacher_id,), fetch="one"
        )
        if existing_id:
            raise ValueError(f"Teacher ID '{teacher_id}'   exist .")

    # Name + Department duplicate check
    existing = execute_query(
        "SELECT id FROM teachers WHERE name=%s AND department=%s",
        (name, department), fetch="one"
    )
    if existing:
        raise ValueError(f"'{name}' ({department})   .")

    return execute_query(
        """INSERT INTO teachers (teacher_id, name, department, designation, face_encoding)
           VALUES (%s, %s, %s, %s, %s)""",
        (teacher_id or None, name, department, designation, face_encoding_bytes)
    )


def get_all_teachers():
    return execute_query(
        """SELECT id, teacher_id, name, department, designation
           FROM teachers ORDER BY name""",
        fetch="all"
    )


def get_teacher_by_id(teacher_id):
    return execute_query(
        """SELECT id, teacher_id, name, department, designation
           FROM teachers WHERE id=%s""",
        (teacher_id,), fetch="one"
    )


def update_teacher(teacher_id, name, department, designation, custom_teacher_id: str = ""):
# Comment translated to English.
    if custom_teacher_id:
        existing = execute_query(
            "SELECT id FROM teachers WHERE teacher_id=%s AND id != %s",
            (custom_teacher_id, teacher_id), fetch="one"
        )
        if existing:
            raise ValueError(
                f"Teacher ID '{custom_teacher_id}'  teacher  .")

    execute_query(
        """UPDATE teachers
           SET teacher_id=%s, name=%s, department=%s, designation=%s
           WHERE id=%s""",
        (custom_teacher_id or None, name, department, designation, teacher_id)
    )


def delete_teacher(teacher_id):
    execute_query("DELETE FROM teachers WHERE id=%s", (teacher_id,))