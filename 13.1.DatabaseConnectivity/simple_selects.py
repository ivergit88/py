import sqlite3

class DataBaseHandler:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                email TEXT UNIQUE
            )''')
        self.conn.commit()

    def insert_user(self, name: str, age: int, email: str):
        self.cursor.execute('''
            INSERT INTO users (name, age, email) VALUES (?, ?, ?)
        ''', (name, age, email))
        self.conn.commit()

    def get_all_users(self):
        self.cursor.execute('SELECT * FROM users')
        return self.cursor.fetchall()

    def get_user_by_id(self, user_id: int):
        self.cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return self.cursor.fetchone()

    def update_user_age(self, user_id: int, new_age: int):
        self.cursor.execute('''
            UPDATE users SET age = ? WHERE id = ?
        ''', (new_age, user_id))
        self.conn.commit()

    def delete_user(self, user_id: int):
        self.cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()