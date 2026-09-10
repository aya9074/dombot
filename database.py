import sqlite3
from datetime import datetime, timedelta
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        role TEXT,
        room_code TEXT
    );

    CREATE TABLE IF NOT EXISTS rooms (
        code TEXT PRIMARY KEY,
        dominant_id INTEGER,
        sub_id INTEGER,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT,
        title TEXT,
        description TEXT,
        schedule_type TEXT,
        deadline TEXT,
        daily_time TEXT,
        reminder_minutes INTEGER DEFAULT 15,
        created_at TEXT,
        expires_at TEXT
    );

    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        sub_id INTEGER,
        caption TEXT,
        media_markers TEXT,
        submitted_at TEXT,
        status TEXT DEFAULT 'pending',
        reviewed_at TEXT
    );
    """)

    conn.commit()
    conn.close()


# ---------- USERS ----------

def get_user(user_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def upsert_user(user_id: int, username: str, role: str, room_code: str):
    conn = get_conn()
    conn.execute("""
        INSERT INTO users (user_id, username, role, room_code)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            role = excluded.role,
            room_code = excluded.room_code
    """, (user_id, username, role, room_code))
    conn.commit()
    conn.close()


def delete_user(user_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ---------- ROOMS ----------

def create_room(code: str, dominant_id: int):
    conn = get_conn()
    conn.execute("""
        INSERT INTO rooms (code, dominant_id, sub_id, created_at)
        VALUES (?, ?, NULL, ?)
    """, (code, dominant_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_room(code: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM rooms WHERE code = ?", (code,)).fetchone()
    conn.close()
    return row


def set_sub_to_room(code: str, sub_id: int):
    conn = get_conn()
    conn.execute("UPDATE rooms SET sub_id = ? WHERE code = ?", (sub_id, code))
    conn.commit()
    conn.close()


def delete_room(code: str):
    conn = get_conn()
    conn.execute("DELETE FROM rooms WHERE code = ?", (code,))
    conn.execute("DELETE FROM users WHERE room_code = ?", (code,))
    conn.execute("DELETE FROM tasks WHERE room_code = ?", (code,))
    conn.commit()
    conn.close()


# ---------- TASKS ----------

def create_task(room_code, title, description, schedule_type,
                deadline=None, daily_time=None, reminder_minutes=15):
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO tasks (room_code, title, description, schedule_type,
                           deadline, daily_time, reminder_minutes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (room_code, title, description, schedule_type,
          deadline, daily_time, reminder_minutes, datetime.now().isoformat()))
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return task_id


def get_tasks_for_room(room_code: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE room_code = ? AND expires_at IS NULL ORDER BY id DESC",
        (room_code,)
    ).fetchall()
    conn.close()
    return rows


def get_task(task_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return row


def delete_task(task_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.execute("DELETE FROM reports WHERE task_id = ?", (task_id,))
    conn.commit()
    conn.close()


def mark_task_expired(task_id: int):
    conn = get_conn()
    expires = (datetime.now() + timedelta(hours=48)).isoformat()
    conn.execute("UPDATE tasks SET expires_at = ? WHERE id = ?", (expires, task_id))
    conn.commit()
    conn.close()


# ---------- REPORTS ----------

def create_report(task_id, sub_id, caption, media_markers):
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO reports (task_id, sub_id, caption, media_markers, submitted_at, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
    """, (task_id, sub_id, caption, media_markers, datetime.now().isoformat()))
    report_id = cur.lastrowid
    conn.commit()
    conn.close()
    return report_id


def get_report(report_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()
    return row


def set_report_status(report_id: int, status: str):
    conn = get_conn()
    conn.execute(
        "UPDATE reports SET status = ?, reviewed_at = ? WHERE id = ?",
        (status, datetime.now().isoformat(), report_id)
    )
    conn.commit()
    conn.close()


def get_pending_reports(room_code: str):
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.* FROM reports r
        JOIN tasks t ON t.id = r.task_id
        WHERE t.room_code = ? AND r.status = 'pending'
        ORDER BY r.submitted_at ASC
    """, (room_code,)).fetchall()
    conn.close()
    return rows


def cleanup_old_reports():
    """Удаляет отчёты старше 48 часов и прошедшие one_time задачи."""
    conn = get_conn()
    cutoff = (datetime.now() - timedelta(hours=48)).isoformat()

    # Удаляем старые отчёты
    conn.execute("DELETE FROM reports WHERE submitted_at < ?", (cutoff,))

    # Удаляем one_time задачи, у которых expires_at прошёл
    conn.execute("""
        DELETE FROM tasks
        WHERE schedule_type = 'one_time'
          AND expires_at IS NOT NULL
          AND expires_at < ?
    """, (datetime.now().isoformat(),))

    conn.commit()
    conn.close()
