import sqlite3
from werkzeug.security import generate_password_hash

# Database file
DB_FILE = "cipher.db"

def create_tables():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON;")

    # User Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            qualification TEXT,
            dob TEXT
        )
    ''')

    # Admin Table (Pre-existing Superuser)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Subject Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subject (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    ''')

    # Chapter Table (Belongs to Subject)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chapter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY(subject_id) REFERENCES subject(id) ON DELETE CASCADE
        )
    ''')

    # Quiz Table (Belongs to Chapter)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id INTEGER NOT NULL,
            date_of_quiz DATETIME DEFAULT CURRENT_TIMESTAMP,
            time_duration TEXT,
            remarks TEXT,
            FOREIGN KEY(chapter_id) REFERENCES chapter(id) ON DELETE CASCADE
        )
    ''')

    # Question Table (Belongs to Quiz)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS question (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            question_statement TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            option4 TEXT NOT NULL,
            correct_option INTEGER NOT NULL CHECK(correct_option BETWEEN 1 AND 4),
            FOREIGN KEY(quiz_id) REFERENCES quiz(id) ON DELETE CASCADE
        )
    ''')

    # Score Table (Stores User Quiz Attempts)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS score (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            time_stamp_of_attempt DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_scored INTEGER NOT NULL,
            FOREIGN KEY(quiz_id) REFERENCES quiz(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE
        )
    ''')

    # Insert a Default Admin User (Pre-existing Admin)
    admin_password = generate_password_hash('admin123', method='pbkdf2:sha256')
    cursor.execute('''
        INSERT OR IGNORE INTO admin (id, username, password) 
        VALUES (1, 'admin', ?)
    ''', (admin_password,))

    conn.commit()
    conn.close()
def update_admin_credentials():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Change username and password
    new_admin_username = "admin@gmail.com"
    new_admin_password = generate_password_hash("admin123", method="pbkdf2:sha256")

    cursor.execute('''
        UPDATE admin SET username = ?, password = ? WHERE id = 1
    ''', (new_admin_username, new_admin_password))

    conn.commit()
    conn.close()
    print("Admin credentials updated successfully!")

if __name__ == "__main__":
    create_tables()
    print("Database schema created successfully!")
    update_admin_credentials()
