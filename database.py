import sqlite3
from datetime import datetime

DB_NAME = "bot.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tariffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            days INTEGER NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            tariff_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            approved_at TEXT,
            expires_at TEXT
        )
    """)

    conn.commit()

    # Boshlang‘ich tariflar
    cursor.execute("SELECT COUNT(*) FROM tariffs")
    count = cursor.fetchone()[0]

    if count == 0:
        tariffs = [
            ("🥉 START", 10000, 1),
            ("🥈 STANDARD", 30000, 7),
            ("🥇 PREMIUM", 70000, 30),
        ]

        cursor.executemany("""
            INSERT INTO tariffs (name, price, days)
            VALUES (?, ?, ?)
        """, tariffs)

        conn.commit()

    conn.close()


def save_user(user):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users
        (telegram_id, username, first_name, last_name, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name
    """, (
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_tariffs():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, price, days
        FROM tariffs
        WHERE active = 1
        ORDER BY price ASC
    """)

    result = cursor.fetchall()
    conn.close()

    return result


def get_tariff(tariff_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, price, days
        FROM tariffs
        WHERE id = ? AND active = 1
    """, (tariff_id,))

    result = cursor.fetchone()
    conn.close()

    return result


def create_purchase(telegram_id, tariff_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO purchases
        (telegram_id, tariff_id, status, created_at)
        VALUES (?, ?, 'pending', ?)
    """, (
        telegram_id,
        tariff_id,
        datetime.now().isoformat()
    ))

    purchase_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return purchase_id


def get_purchase(purchase_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.id,
            p.telegram_id,
            p.tariff_id,
            p.status,
            p.created_at,
            p.approved_at,
            p.expires_at,
            t.name,
            t.price,
            t.days
        FROM purchases p
        JOIN tariffs t ON t.id = p.tariff_id
        WHERE p.id = ?
    """, (purchase_id,))

    result = cursor.fetchone()
    conn.close()

    return result


def approve_purchase(purchase_id):
    conn = get_connection()
    cursor = conn.cursor()

    purchase = get_purchase(purchase_id)

    if not purchase:
        conn.close()
        return False

    days = purchase[9]

    from datetime import timedelta

    now = datetime.now()
    expires = now + timedelta(days=days)
    cursor.execute("""
        UPDATE purchases
        SET status = 'approved',
            approved_at = ?,
            expires_at = ?
        WHERE id = ?
    """, (
        now.isoformat(),
        expires.isoformat(),
        purchase_id
    ))

    conn.commit()
    conn.close()

    return True


def reject_purchase(purchase_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE purchases
        SET status = 'rejected'
        WHERE id = ?
    """, (purchase_id,))

    conn.commit()
    conn.close()

    return True


def has_active_tariff(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM purchases
        WHERE telegram_id = ?
          AND status = 'approved'
          AND expires_at > ?
        ORDER BY expires_at DESC
        LIMIT 1
    """, (
        telegram_id,
        datetime.now().isoformat()
    ))

    result = cursor.fetchone()
    conn.close()

    return result is not None
