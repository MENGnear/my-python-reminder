# ==========================================================
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# 專案名稱 : 提醒備忘系統 - 背景排程器模組
# 檔案名稱 : scheduler.py
# 程式版本 : v2.1.0 (改用 Telegram 發送，支援週期任務推算)
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# ==========================================================

import time
import datetime
import threading
from modules import db_manager

# 引用主程式的發送函式 (使用 local import 避免循環依賴)
def send_telegram(msg):
    from app import send_telegram_rmdr
    return send_telegram_rmdr(msg)

TW_TZ = datetime.timezone(datetime.timedelta(hours=8))

def calculate_next_run(remind_time_str, recur_type, recur_val):
    """計算週期任務下一次觸發的時間"""
    now = datetime.datetime.now(TW_TZ)
    # 取出設定的目標「時間」(時:分:秒)
    target_time_str = remind_time_str[-8:] 
    
    if recur_type == "每天":
        next_date = now + datetime.timedelta(days=1)
        return f"{next_date.strftime('%Y-%m-%d')} {target_time_str}"
        
    elif recur_type == "每月":
        month = now.month + 1
        year = now.year
        if month > 12:
            month = 1
            year += 1
        day = int(recur_val)
        return f"{year}-{month:02d}-{day:02d} {target_time_str}"
        
    elif recur_type == "每年":
        year = now.year + 1
        return f"{year}-{recur_val} {target_time_str}"
        
    return remind_time_str

def check_and_send_reminders():
    """檢查資料庫並發送提醒"""
    now = datetime.datetime.now(TW_TZ)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # 撈取所有備忘錄
    reminders = db_manager.get_all_reminders()
    
    for r in reminders:
        # 判斷邏輯：狀態是 pending 且 現在時間 >= 提醒時間
        if r['status'] == 'pending' and now_str >= r['remind_time']:
            
            # 組合推播訊息
            msg_type = "🔁 [週期任務]" if r.get('is_recurring') else "📝 [單次任務]"
            msg = f"⏰ <b>【備忘提醒】</b>\n{msg_type}\n內容：{r['content']}\n設定時間：{r['remind_time']}"
            
            # 觸發 Telegram 發送 (接回 app.py 的函式)
            success, _ = send_telegram(msg)
            
            # 如果發送成功，依照任務類型進行後續處理
            if success:
                if r.get('is_recurring'):
                    # 週期任務：計算下次時間並更新 (狀態會自動被重置為 pending)
                    next_time = calculate_next_run(r['remind_time'], r['recurrence_type'], r['recurrence_value'])
                    db_manager.update_reminder_time(r['id'], next_time)
                    print(f"🔁 週期任務已發送並推算下次時間: {r['content']} -> {next_time}")
                else:
                    # 單次任務：狀態更新為已發送 (sent)
                    db_manager.update_status(r['id'], 'sent')
                    print(f"✅ 單次推播成功: {r['content']}")

def continuous_run():
    """背景持續執行的迴圈"""
    while True:
        check_and_send_reminders()
        time.sleep(30)  # 每 30 秒掃描一次資料庫

def start_background_task():
    """啟動背景執行緒 (Daemon Thread)"""
    thread = threading.Thread(target=continuous_run, daemon=True)
    thread.start()
