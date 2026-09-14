import sqlite3


def get_db():
    db = sqlite3.connect(
        "campus.db",
        timeout=30,
        check_same_thread=False
    )

    db.row_factory = sqlite3.Row

    return db


def create_table():

    db = get_db()

    # =========================================================
    # COMPLAINT TABLE
    # =========================================================

    db.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            department TEXT,
            description TEXT,
            category TEXT,
            priority TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT,
            escalated INTEGER DEFAULT 0,
            rating INTEGER DEFAULT NULL,
            feedback TEXT,
            photo TEXT,
            email TEXT,
            location TEXT
        )
    """)


    # =========================================================
    # USER TABLE
    # =========================================================
    # username = student's personal email
    #
    # Example:
    # roshini@gmail.com
    # nithya@gmail.com
    #
    # Each student has their own account.
    # =========================================================

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            name TEXT
        )
    """)


    # =========================================================
    # SETTINGS TABLE
    # =========================================================

    db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            admin_name TEXT DEFAULT 'Admin',
            notifications INTEGER DEFAULT 1,
            auto_escalation INTEGER DEFAULT 1
        )
    """)


    db.execute("""
        INSERT OR IGNORE INTO settings
        (id, admin_name, notifications, auto_escalation)
        VALUES (1, 'Admin', 1, 1)
    """)


    # =========================================================
    # NOTIFICATION TABLE
    # =========================================================

    db.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            status TEXT DEFAULT 'Unread',
            created_at TEXT
        )
    """)


    # =========================================================
    # CHECK COMPLAINT COLUMNS
    # =========================================================

    columns = [
        row["name"]
        for row in db.execute(
            "PRAGMA table_info(complaints)"
        ).fetchall()
    ]


    if "created_at" not in columns:

        db.execute("""
            ALTER TABLE complaints
            ADD COLUMN created_at TEXT
        """)


    if "escalated" not in columns:

        db.execute("""
            ALTER TABLE complaints
            ADD COLUMN escalated INTEGER DEFAULT 0
        """)


    if "rating" not in columns:

        db.execute("""
            ALTER TABLE complaints
            ADD COLUMN rating INTEGER DEFAULT NULL
        """)


    if "feedback" not in columns:

        db.execute("""
            ALTER TABLE complaints
            ADD COLUMN feedback TEXT
        """)


    if "photo" not in columns:

        db.execute("""
            ALTER TABLE complaints
            ADD COLUMN photo TEXT
        """)


    if "email" not in columns:

        db.execute("""
            ALTER TABLE complaints
            ADD COLUMN email TEXT
        """)


    if "location" not in columns:

        db.execute("""
            ALTER TABLE complaints
            ADD COLUMN location TEXT
        """)


    # =========================================================
    # DEFAULT ADMIN ACCOUNT
    # =========================================================

    db.execute("""
        INSERT OR IGNORE INTO users
        (username, password, role, name)
        VALUES (?, ?, ?, ?)
    """, (
        "admin",
        "admin123",
        "admin",
        "Administrator"
    ))


    # =========================================================
    # REMOVE OLD COMMON STUDENT ACCOUNT
    # =========================================================
    # No common student login anymore.
    # Every student will use their own email/password.
    # =========================================================

    db.execute("""
        DELETE FROM users
        WHERE username = 'student'
        AND role = 'student'
    """)


    db.commit()

    db.close()