# ==========================================================
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# 專案名稱 : 提醒備忘系統 - 背景排程器模組
# 檔案名稱 : scheduler.py
# 程式版本 : v2.2.4 (優化自動發送訊息格式與圖示空格)
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# ==========================================================

import time
import datetime
import threading
from modules import db_manager

# 防護機制：避免幽靈執行緒重複啟動
_scheduler_started = False
_scheduler_lock = threading.Lock()

def send_telegram(msg):
    from app import send_telegram_rmdr
    return send_telegram_rmdr(msg)

TW_TZ = datetime.timezone(datetime.timedelta(hours=8))

def calculate_next_run(remind_time_str, recur_type, recur_val):
    """計算週期任務下一次觸發的時間"""
    now = datetime.datetime.now(TW_TZ)
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

    reminders = db_manager.get_all_reminders()
    
    for r in reminders:
        if r['status'] == 'pending' and now_str >= r['remind_time']:
            
            # 先鎖定狀態為 processing，避免其他執行緒重複抓取
            db_manager.update_status(r['id'], 'processing')
            
            # 切片去掉秒數 (取前16碼: 2026-07-05 20:30)
            display_time = r['remind_time'][:16]
            
            # 【格式優化】套用新版自動發送格式 (補上空格，更新圖示)
            if r.get('is_recurring'):
                msg = f"🔄 {display_time}\n📝 {r['content']}"
            else:
                msg = f"⏰ {display_time}\n📝 {r['content']}"
            
            # 觸發發送
            success, _ = send_telegram(msg)
            
            if success:
                if r.get('is_recurring'):
                    next_time = calculate_next_run(r['remind_time'], r['recurrence_type'], r['recurrence_value'])
                    db_manager.update_reminder_time(r['id'], next_time)
                else:
                    db_manager.update_status(r['id'], 'sent')

def continuous_run():
    while True:
        check_and_send_reminders()
        time.sleep(30)

def start_background_task():
    global _scheduler_started
    with _scheduler_lock:
        if not _scheduler_started:
            thread = threading.Thread(target=continuous_run, daemon=True, name="RMDR_Worker")
            thread.start()
            _scheduler_started = True
