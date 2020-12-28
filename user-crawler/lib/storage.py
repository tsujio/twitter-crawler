import contextlib
from datetime import datetime
import json
import logging
import os
import sqlite3


@contextlib.contextmanager
def open_db(data_dir):
    conn = sqlite3.connect(os.path.join(data_dir, 'app.db'))
    conn.row_factory = sqlite3.Row
    cursor = None
    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys=true")

        yield cursor

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()


class Storage:

    def __init__(self, data_dir):
        self.data_dir = data_dir

        with open_db(self.data_dir) as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT NOT NULL,
                raw_data JSON NOT NULL,
                retrieved_at DATETIME NOT NULL,
                PRIMARY KEY (id)
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS followings (
                src TEXT NOT NULL,
                dest TEXT NOT NULL,
                retrieved_at DATETIME NOT NULL,
                PRIMARY KEY (src, dest),
                FOREIGN KEY (src) REFERENCES users(id),
                FOREIGN KEY (dest) REFERENCES users(id)
            )
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_followings__dest
            ON followings(dest)
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                timestamp DATETIME NOT NULL,
                user_count INT UNSIGNED NOT NULL,
                following_count BIGINT UNSIGNED NOT NULL,
                PRIMARY KEY (timestamp)
            )
            """)

    def select_user(self):
        with open_db(self.data_dir) as cursor:
            cursor.execute("""
            SELECT raw_data FROM users
            WHERE JSON_EXTRACT(raw_data, '$.protected') = 0
            ORDER BY RANDOM()
            LIMIT 1
            """)

            user = cursor.fetchone()

        return json.loads(user['raw_data']) if user else None

    def save_followings(self, user, followings):
        with open_db(self.data_dir) as cursor:
            cursor.execute("""
            REPLACE INTO users(id, raw_data, retrieved_at)
            VALUES (?, ?, ?)
            """, (user['id'], json.dumps(user), datetime.now()))

            cursor.execute("""
            DELETE FROM followings
            WHERE src = ?
            """, (user['id'],))

            count = 0
            for following in followings:
                cursor.execute("""
                REPLACE INTO users(id, raw_data, retrieved_at)
                VALUES (?, ?, ?)
                """, (following['id'],
                      json.dumps(following),
                      datetime.now()))

                cursor.execute("""
                INSERT INTO followings(src, dest, retrieved_at)
                VALUES (?, ?, ?)
                """, (user['id'],
                      following['id'],
                      datetime.now()))

                count += 1

            logging.info(f"{count} records inserted")

    def save_stats(self):
        with open_db(self.data_dir) as cursor:
            cursor.execute("""
            INSERT INTO stats(timestamp, user_count, following_count)
            VALUES (?,
                    (SELECT COUNT(*) FROM users),
                    (SELECT COUNT(*) FROM followings))
            """, (datetime.now(),))

            cursor.execute("""
            SELECT timestamp, user_count, following_count
            FROM stats
            ORDER BY timestamp DESC
            LIMIT 1
            """)

            stats = cursor.fetchone()

        logging.debug(f"stats: user_count={stats['user_count']}, "
                      f"following_count={stats['following_count']}")
