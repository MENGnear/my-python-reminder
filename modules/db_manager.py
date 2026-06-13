"""
提醒備忘系統 - 資料庫管理模組
Version: v1.0.0
"""
import sqlite3
from datetime import datetime

# 設定資料庫檔案名稱
DB_PATH = 'reminders.db'

def get_connection():
    """建立資料庫連線"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    """初始化資料庫與資料表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            remind_time DATETIME NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_reminder(content, remind_time):
    """新增備忘錄 (Create)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reminders (content, remind_time, status) VALUES (?, ?, 'pending')",
        (content, remind_time)
    )
    conn.commit()
    conn.close()

def get_all_reminders():
    """取得所有備忘錄 (Read)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reminders ORDER BY remind_time ASC")
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return results

def update_status(reminder_id, status):
    """更新備忘錄狀態 (Update) - 推播後使用"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reminders SET status = ? WHERE id = ?", (status, reminder_id))
    conn.commit()
    conn.close()

def edit_reminder(reminder_id, new_content, new_time):
    """修改備忘錄內容與時間 (Update) - 網頁編輯使用"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reminders SET content = ?, remind_time = ? WHERE id = ?", 
        (new_content, new_time, reminder_id)
    )
    conn.commit()
    conn.close()

def delete_reminder(reminder_id):
    """刪除備忘錄 (Delete)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()
