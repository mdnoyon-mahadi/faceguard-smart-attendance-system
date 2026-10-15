# ============================================================
# db_connection.py — MySQL connection manager
# ============================================================
# Comment translated to English.
# Comment translated to English.
# ============================================================

import pymysql
import pymysql.cursors
import mysql.connector
from mysql.connector import pooling, Error
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# ── Connection Pool Setup ─────────────────────────────────────
_pool_config = {
    "pool_name":    "face_attendance_pool",
    "pool_size":    5,
    "host":         DB_HOST,
    "port":         DB_PORT,
    "user":         DB_USER,
    "password":     DB_PASSWORD,
    "database":     DB_NAME,
    "charset":      "utf8mb4",
    "autocommit":   False,
}

_connection_pool = None


def _get_pool():
    """Pool   ,  same pool return ."""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = pooling.MySQLConnectionPool(**_pool_config)
            print("[DB] Connection pool  .")
        except Error as e:
            print(f"[DB ERROR] Pool   : {e}")
            raise
    return _connection_pool


def get_connection():
    """
    Pool   connection .
    :
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        ...
        conn.commit()
        cursor.close()
        conn.close()   # pool   
    """
    return _get_pool().get_connection()


def execute_query(query: str, params: tuple = None, fetch: str = None):
    """
    Single query execute  shortcut.

    fetch:
        None      → INSERT/UPDATE/DELETE (lastrowid return )
        "one"     → fetchone()
        "all"     → fetchall()

    :
        rows = execute_query("SELECT * FROM users WHERE status=%s", ('approved',), fetch="all")
        lid  = execute_query("INSERT INTO users (...) VALUES (...)", (val1, val2))
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if fetch == "one":
            result = cursor.fetchone()
        elif fetch == "all":
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid

        return result

    except Error as e:
        if conn:
            conn.rollback()
        print(f"[DB ERROR] Query  : {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def test_connection():
    """
    DB connection     check .
    main.py  app start   call  .
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        print("[DB] ✓ Database connection  .")
        return True
    except Error as e:
        print(f"[DB ERROR] ✗ Database connect  : {e}")
        print("  → .env file  DB_PASSWORD     .")
        print("  → MySQL service    .")
        return False
# ============================================================
# db_connection.py — PyMySQL connection manager
# ============================================================


def get_connection():
    """
      DB connection return .
    :
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(...)
        conn.commit()
        conn.close()
    """
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=10,
    )


def execute_query(query: str, params: tuple = None, fetch: str = None):
    """
    Single query execute  shortcut.

    fetch:
        None  → INSERT/UPDATE/DELETE (lastrowid return )
        "one" → fetchone()
        "all" → fetchall()

    :
        rows = execute_query("SELECT * FROM users WHERE status=%s", ('approved',), fetch="all")
        lid  = execute_query("INSERT INTO users (...) VALUES (...)", (val1, val2))
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())

            if fetch == "one":
                result = cursor.fetchone()
            elif fetch == "all":
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.lastrowid

        return result

    except pymysql.Error as e:
        if conn:
            conn.rollback()
        print(f"[DB ERROR] Query  : {e}")
        raise
    finally:
        if conn:
            conn.close()


def execute_many(query: str, params_list: list):
    """
      row insert/update  .
    :
        execute_many("INSERT INTO table (a,b) VALUES (%s,%s)", [(1,2),(3,4)])
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.executemany(query, params_list)
        conn.commit()
    except pymysql.Error as e:
        if conn:
            conn.rollback()
        print(f"[DB ERROR] executemany : {e}")
        raise
    finally:
        if conn:
            conn.close()


def test_connection():
    """
    DB connection     check .
    main.py  app start   call .
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        conn.close()
        print("[DB] [OK] Database connection successful.")
        return True
    except pymysql.Error as e:
        print(f"[DB ERROR] [FAIL] Connect failed: {e}")
        print("  -> MySQL service is running? (services.msc)")
        print("  -> .env DB_PASSWORD is correct?")
        print("  -> MySQL 'face_attendance_db' database exists?")
        return False