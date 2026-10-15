# ============================================================
# report_model.py — Report Fetch & Delete Operations
# ============================================================
# নতুন:
#   - get_report_detail() → teacher attendance row ও include করে
#   - get_teacher_attendance_detail() → শুধু teacher এর record
#   - set_session_report_status() → pending/complete report status update
#   - get_filtered_reports() → report_status column include করে
#   - get_absent_students() → যারা scan করেনি তাদের list (FIXED)
# ============================================================

from database.db_connection import execute_query
from datetime import datetime
from services.attendance_service import sync_session_attendance_statuses


def _session_teacher_join_sql():
    return """LEFT JOIN teachers t_pk ON s.teacher_id = t_pk.id
           LEFT JOIN teachers t_emp
                  ON t_pk.id IS NULL AND s.teacher_id = t_emp.teacher_id"""


def _session_teacher_name_sql():
    return "COALESCE(t_pk.name, t_emp.name)"


def get_all_reports():
    """সব closed session এর report।"""
    return execute_query(
        f"""SELECT
               s.id          AS session_id,
               s.session_date,
               s.subject,
               s.status      AS session_status,
               s.report_status,
               s.pending_report_generated_at,
               s.complete_report_generated_at,
               {_session_teacher_name_sql()} AS teacher_name,
               ro.department,
               ro.semester,
               ro.shift,
               COUNT(DISTINCT CASE
                   WHEN r.status='complete'
                    AND (r.scan_in_time IS NOT NULL OR r.scan_out_time IS NOT NULL)
                   THEN r.id END)                                           AS attended,
               COUNT(DISTINCT CASE
                   WHEN r.scan_in_time IS NOT NULL OR r.scan_out_time IS NOT NULL
                   THEN r.id END)                                           AS total_scanned
           FROM attendance_sessions s
           {_session_teacher_join_sql()}
           LEFT JOIN routines ro       ON s.routine_id  = ro.id
           LEFT JOIN attendance_records r ON r.session_id = s.id
           WHERE s.status = 'closed'
           GROUP BY s.id
           ORDER BY s.session_date DESC, s.subject""",
        fetch="all"
    )


def get_departments():
    """routines table থেকে unique department list।"""
    rows = execute_query(
        "SELECT DISTINCT department FROM routines ORDER BY department",
        fetch="all"
    )
    return [r["department"] for r in rows] if rows else []


def get_semesters_by_dept(department: str):
    rows = execute_query(
        """SELECT DISTINCT semester FROM routines
           WHERE department = %s ORDER BY semester""",
        (department,), fetch="all"
    )
    return [r["semester"] for r in rows] if rows else []


def get_subjects_by_dept_sem(department: str, semester: str):
    rows = execute_query(
        """SELECT DISTINCT subject FROM routines
           WHERE department = %s AND semester = %s
           ORDER BY subject""",
        (department, semester), fetch="all"
    )
    return [r["subject"] for r in rows] if rows else []


def get_shifts_by_dept_sem(department: str, semester: str):
    try:
        rows = execute_query(
            """SELECT DISTINCT shift FROM routines
               WHERE department = %s AND semester = %s
                 AND shift IS NOT NULL
               ORDER BY shift""",
            (department, semester), fetch="all"
        )
        shifts = [r["shift"] for r in rows if r.get("shift")] if rows else []
        return shifts if shifts else ["morning"]
    except Exception:
        return ["morning"]


def get_filtered_reports(department: str, semester: str,
                         subject: str, shift: str):
    """
    Filter করা reports।
    - closed + complete → Complete Report ✅
    - open + pending   → Pending Report ⏳
    session_date DESC (recent first)।
    """
    try:
        rows = execute_query(
            f"""SELECT
                   s.id          AS session_id,
                   s.session_date,
                   s.subject,
                   s.status      AS session_status,
                   s.report_status,
                   s.pending_report_generated_at,
                   s.complete_report_generated_at,
                   {_session_teacher_name_sql()} AS teacher_name,
                   ro.department,
                   ro.semester,
                   ro.shift,
                   COUNT(DISTINCT CASE
                       WHEN r.status='complete'
                        AND (r.scan_in_time IS NOT NULL OR r.scan_out_time IS NOT NULL)
                       THEN r.id END)                                           AS attended,
                   COUNT(DISTINCT CASE
                       WHEN r.status='pending'
                        AND (r.scan_in_time IS NOT NULL OR r.scan_out_time IS NOT NULL)
                       THEN r.id END)                                           AS pending_count,
                   COUNT(DISTINCT CASE
                       WHEN r.scan_in_time IS NOT NULL OR r.scan_out_time IS NOT NULL
                       THEN r.id END)                                           AS total_scanned
               FROM attendance_sessions s
               {_session_teacher_join_sql()}
               LEFT JOIN routines ro       ON s.routine_id  = ro.id
               LEFT JOIN attendance_records r ON r.session_id = s.id
               WHERE (s.status = 'closed' OR s.report_status = 'pending')
                 AND ro.department = %s
                 AND ro.semester   = %s
                 AND s.subject     = %s
                 AND ro.shift      = %s
               GROUP BY s.id
               ORDER BY s.session_date DESC""",
            (department, semester, subject, shift), fetch="all"
        )
        if not rows:
            rows = _get_filtered_no_shift(department, semester, subject)
        return rows
    except Exception:
        return _get_filtered_no_shift(department, semester, subject)


def _get_filtered_no_shift(department: str, semester: str, subject: str):
    """shift ছাড়া fallback query।"""
    return execute_query(
        f"""SELECT
               s.id          AS session_id,
               s.session_date,
               s.subject,
               s.status      AS session_status,
               s.report_status,
               s.pending_report_generated_at,
               s.complete_report_generated_at,
               {_session_teacher_name_sql()} AS teacher_name,
               ro.department,
               ro.semester,
               NULL          AS shift,
               COUNT(DISTINCT CASE
                   WHEN r.status='complete'
                    AND (r.scan_in_time IS NOT NULL OR r.scan_out_time IS NOT NULL)
                   THEN r.id END)                                           AS attended,
               COUNT(DISTINCT CASE
                   WHEN r.status='pending'
                    AND (r.scan_in_time IS NOT NULL OR r.scan_out_time IS NOT NULL)
                   THEN r.id END)                                           AS pending_count,
               COUNT(DISTINCT CASE
                   WHEN r.scan_in_time IS NOT NULL OR r.scan_out_time IS NOT NULL
                   THEN r.id END)                                           AS total_scanned
           FROM attendance_sessions s
           {_session_teacher_join_sql()}
           LEFT JOIN routines ro       ON s.routine_id  = ro.id
           LEFT JOIN attendance_records r ON r.session_id = s.id
           WHERE (s.status = 'closed' OR s.report_status = 'pending')
             AND ro.department = %s
             AND ro.semester   = %s
             AND s.subject     = %s
           GROUP BY s.id
           ORDER BY s.session_date DESC""",
        (department, semester, subject), fetch="all"
    )


def get_report_detail(session_id: int):
    """
    একটা session এর সব student detail।
    Includes absent students from the session roster.
    """
    sync_session_attendance_statuses(session_id)
    return execute_query(
        f"""SELECT
               u.roll, u.name, u.department, u.semester,
               r.scan_in_time,
               r.scan_out_time,
               CASE
                   WHEN r.scan_in_time IS NULL AND r.scan_out_time IS NULL
                   THEN 'absent'
                   ELSE r.status
               END AS status,
               'student' AS person_type
           FROM attendance_sessions s
           JOIN routines ro ON s.routine_id = ro.id
           JOIN users u
             ON u.department = ro.department
            AND u.semester   = ro.semester
           LEFT JOIN attendance_records r
             ON r.session_id = s.id
            AND r.user_id    = u.id
           WHERE s.id = %s
           ORDER BY
               CASE
                   WHEN r.scan_in_time IS NULL AND r.scan_out_time IS NULL THEN 2
                   WHEN r.status = 'pending' THEN 0
                   ELSE 1
               END,
               u.roll""",
        (session_id,), fetch="all"
    )


def get_teacher_attendance_detail(session_id: int):
    """
    একটা session এর teacher attendance record।
    Return: dict {name, scan_in_time, scan_out_time, status} অথবা None
    """
    try:
        return execute_query(
            """SELECT
                   t.name,
                   ta.scan_in_time,
                   ta.scan_out_time,
                   ta.status
               FROM teacher_attendance_records ta
               JOIN teachers t ON ta.teacher_id = t.id
               WHERE ta.session_id = %s
               LIMIT 1""",
            (session_id,), fetch="one"
        )
    except Exception:
        return None


def get_absent_students(session_id: int):
    """
    Session এ যারা scan করেনি তাদের list।

    Logic:
      1. session_id → routine → department + semester বের করো
      2. users table থেকে same department + semester এর সব student নাও
      3. যাদের scan_in_time এবং scan_out_time দুটোই NULL → ABSENT

    পুরনো bug: routines এ multiple rows থাকায় JOIN এ duplicate হতো।
    Fix: subquery দিয়ে department/semester আলাদাভাবে নেওয়া হয়েছে।

    Return: list of dict with the same student detail shape as get_report_detail().
    """
    try:
        sync_session_attendance_statuses(session_id)
        return execute_query(
            """SELECT
                   u.id,
                   u.roll,
                   u.name,
                   u.department,
                   u.semester,
                   r.scan_in_time,
                   r.scan_out_time,
                   'absent' AS status,
                   'student' AS person_type
               FROM attendance_sessions s
               JOIN routines ro ON s.routine_id = ro.id
               JOIN users u
                 ON u.department = ro.department
                AND u.semester   = ro.semester
               LEFT JOIN attendance_records r
                 ON r.session_id = s.id
                AND r.user_id    = u.id
               WHERE s.id = %s
                 AND r.scan_in_time IS NULL
                 AND r.scan_out_time IS NULL
               ORDER BY u.roll""",
            (session_id,), fetch="all"
        )
    except Exception:
        return []


def set_session_report_status(session_id: int, status: str):
    """
    Session এর report_status update করো।
    status: 'pending' → Entry phase শেষে
            'complete' → Exit phase শেষে
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if status == "pending":
        execute_query(
            """UPDATE attendance_sessions
               SET report_status = 'pending',
                   pending_report_generated_at = %s
               WHERE id = %s""",
            (now, session_id)
        )
    elif status == "complete":
        execute_query(
            """UPDATE attendance_sessions
               SET report_status = 'complete',
                   complete_report_generated_at = %s
               WHERE id = %s""",
            (now, session_id)
        )


def delete_report(session_id: int):
    """Session + সব records delete করো।"""
    try:
        execute_query(
            "DELETE FROM teacher_attendance_records WHERE session_id=%s",
            (session_id,)
        )
    except Exception:
        pass
    execute_query(
        "DELETE FROM attendance_records WHERE session_id=%s", (session_id,)
    )
    execute_query(
        "DELETE FROM attendance_sessions WHERE id=%s", (session_id,)
    )
