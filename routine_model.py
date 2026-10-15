# ============================================================
# routine_model.py — Routine CRUD Operations
# ============================================================

from database.db_connection import execute_query
from datetime import datetime

DAYS = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday",
    3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday",
}


def _today():
    return DAYS.get(datetime.now().weekday())


def _teacher_join_sql():
    return """LEFT JOIN teachers t_pk ON r.teacher_id = t_pk.id
           LEFT JOIN teachers t_emp
                  ON t_pk.id IS NULL AND r.teacher_id = t_emp.teacher_id"""


def _teacher_name_sql():
    return "COALESCE(t_pk.name, t_emp.name)"


def _teacher_uid_sql():
    return "COALESCE(t_pk.teacher_id, t_emp.teacher_id)"


def _teacher_db_id_sql():
    return "COALESCE(t_pk.id, t_emp.id)"


def add_routine(department, semester, day, subject, teacher_id,
                class_start, class_end, shift="morning"):
    return execute_query(
        """INSERT INTO routines
           (department, semester, day, subject, teacher_id,
            class_start, class_end, shift)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        (department, semester, day, subject, teacher_id,
         class_start, class_end, shift)
    )


def get_all_routines():
    return execute_query(
        f"""SELECT r.id, r.department, r.semester, r.day, r.subject,
                  r.shift, {_teacher_name_sql()} AS teacher_name,
                  r.class_start, r.class_end
           FROM routines r
           {_teacher_join_sql()}
           ORDER BY FIELD(r.day,'Monday','Tuesday','Wednesday',
                          'Thursday','Friday','Saturday','Sunday'),
                    r.class_start""",
        fetch="all"
    )


def search_routines_for_student(department, semester, shift):
    return execute_query(
        f"""SELECT r.id, r.department, r.semester, r.day, r.subject,
                  r.shift, r.class_start, r.class_end,
                  {_teacher_name_sql()} AS teacher_name
           FROM routines r
           {_teacher_join_sql()}
           WHERE r.department = %s
             AND r.semester   = %s
             AND r.shift      = %s
           ORDER BY FIELD(r.day,'Monday','Tuesday','Wednesday',
                          'Thursday','Friday','Saturday','Sunday'),
                    r.class_start""",
        (department, semester, shift), fetch="all"
    )


def search_routines_for_teacher(teacher_id: str = "", teacher_name: str = "", shift: str = ""):
    params = []
    where_parts = []

    if teacher_id:
        where_parts.append(f"{_teacher_uid_sql()} = %s")
        params.append(teacher_id)
    elif teacher_name:
        where_parts.append(f"{_teacher_name_sql()} LIKE %s")
        params.append(f"%{teacher_name}%")

    if shift:
        where_parts.append("r.shift = %s")
        params.append(shift)

    where_clause = ("WHERE " + " AND ".join(where_parts)
                    ) if where_parts else ""

    return execute_query(
        f"""SELECT r.id, r.department, r.semester, r.day, r.subject,
                   r.shift, r.class_start, r.class_end,
                   {_teacher_name_sql()} AS teacher_name,
                   {_teacher_uid_sql()} AS teacher_uid,
                   {_teacher_db_id_sql()} AS teacher_db_id
            FROM routines r
            {_teacher_join_sql()}
            {where_clause}
            ORDER BY FIELD(r.day,'Monday','Tuesday','Wednesday',
                           'Thursday','Friday','Saturday','Sunday'),
                     r.class_start""",
        tuple(params), fetch="all"
    )


def get_routine_by_id(routine_id):
    return execute_query(
        f"""SELECT r.*, {_teacher_name_sql()} AS teacher_name
           FROM routines r
           {_teacher_join_sql()}
           WHERE r.id=%s""",
        (routine_id,), fetch="one"
    )


def update_routine(routine_id, department, semester, day, subject,
                   teacher_id, class_start, class_end, shift="morning"):
    execute_query(
        """UPDATE routines SET
           department=%s, semester=%s, day=%s, subject=%s, teacher_id=%s,
           class_start=%s, class_end=%s, shift=%s
           WHERE id=%s""",
        (department, semester, day, subject, teacher_id,
         class_start, class_end, shift, routine_id)
    )


def delete_routine(routine_id):
    execute_query("DELETE FROM routines WHERE id=%s", (routine_id,))
