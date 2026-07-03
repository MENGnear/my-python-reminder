# ==========================================================
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# 專案名稱 : 提醒備忘系統 - 資料庫管理模組
# 檔案名稱 : db_manager.py
# 程式版本 : v2.1.0 (擴充週期任務支援與對齊 app.py 命名)
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# ==========================================================

import sqlite3
from datetime import datetime

# 設定資料庫檔案名稱
DB_PATH = 'reminders.db'

def get_connection():
    """建立資料庫連線"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    """初始化資料庫與資料表 (v2.1.0 擴充週期任務欄位)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            remind_time DATETIME NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_recurring BOOLEAN DEFAULT 0,
            recurrence_type TEXT,
            recurrence_value TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_reminder(content, remind_time, is_recurring=0, recurrence_type="", recurrence_value=""):
    """新增備忘錄 (Create)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO reminders 
           (content, remind_time, status, is_recurring, recurrence_type, recurrence_value) 
           VALUES (?, ?, 'pending', ?, ?, ?)''',
        (content, remind_time, is_recurring, recurrence_type, recurrence_value)
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

def update_reminder(reminder_id, new_content, new_time):
    """修改備忘錄內容與時間 (Update) - 網頁編輯使用 (已對齊 app.py 的命名)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reminders SET content = ?, remind_time = ? WHERE id = ?", 
        (new_content, new_time, reminder_id)
    )
    conn.commit()
    conn.close()
    
def update_reminder_time(reminder_id, new_time):
    """更新備忘錄觸發時間 (Update) - 排程器週期推算使用"""
    conn = get_connection()
    cursor = conn.cursor()
    # 週期任務自動推算下次時間後，需要將狀態重設回 pending，排程器才會再次抓取
    cursor.execute(
        "UPDATE reminders SET remind_time = ?, status = 'pending' WHERE id = ?", 
        (new_time, reminder_id)
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
