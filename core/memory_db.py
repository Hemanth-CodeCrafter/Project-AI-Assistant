import sqlite3


class MemoryDB:

    def __init__(self):
        self.conn = sqlite3.connect(
            "jarvis_memory.db",
            check_same_thread=False
        )

        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory TEXT UNIQUE,
            category TEXT,
            importance INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()

    def save(self, memory, category="general", importance=5):

        self.cursor.execute("""
        INSERT OR IGNORE INTO memories
        (memory, category, importance)
        VALUES (?, ?, ?)
        """, (
            memory,
            category,
            importance
        ))

        self.conn.commit()

    def search(self, keyword):

        self.cursor.execute("""
        SELECT memory, category, importance
        FROM memories
        WHERE memory LIKE ?
        ORDER BY importance DESC
        """, (
            f"%{keyword}%",
        ))

        return self.cursor.fetchall()

    def get_all(self):

        self.cursor.execute("""
        SELECT memory, category, importance
        FROM memories
        ORDER BY importance DESC
        """)

        return self.cursor.fetchall()

    def delete(self, memory):

        self.cursor.execute("""
        DELETE FROM memories
        WHERE memory=?
        """, (memory,))

        self.conn.commit()

    def clear(self):

        self.cursor.execute("""
        DELETE FROM memories
        """)

        self.conn.commit()


memory_db = MemoryDB()