# ==========================================================
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# 專案名稱 : 提醒備忘系統 - 背景排程器模組
# 檔案名稱 : scheduler.py
# 程式版本 : V2.2.7 (完美除錯與防呆版)
# 進版說明 :
#   1. 【維持】保留 15 分鐘「過期防護機制」，防休眠喚醒洗版。
#   2. 【維持】保留 processing 鎖定機制，從物理上阻絕同一秒雙重發送的可能。
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

# ==========================================================
# 區塊 1：週期任務時間推算邏輯
# ==========================================================
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

# ==========================================================
# 區塊 2：核心排程掃描與過期防護邏輯
# ==========================================================
def check_and_send_reminders():
    """檢查資料庫並發送提醒 (內建過期防護與處理鎖定)"""
    now = datetime.datetime.now(TW_TZ)
    reminders = db_manager.get_all_reminders()
    
    for r in reminders:
        if r['status'] == 'pending':
            remind_dt = datetime.datetime.strptime(r['remind_time'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=TW_TZ)
            diff_minutes = (now - remind_dt).total_seconds() / 60.0
            
            # 【核心防護 1】：過期超過 15 分鐘的任務直接作廢，不補發
            if diff_minutes > 15:
                print(f"[{now.strftime('%H:%M:%S')}] 🛡️ 攔截過期任務，避免洗版: {r['content']}")
                db_manager.update_status(r['id'], 'expired')
                continue
            
            # 時間到了，且在 15 分鐘有效期限內
            elif diff_minutes >= 0:
                # 【核心防護 2】：先鎖定狀態為 processing，避免其他執行緒或介面重複抓取
                db_manager.update_status(r['id'], 'processing')
                
                display_time = r['remind_time'][:16]
                if r.get('is_recurring'):
                    msg = f"🔄 {display_time}\n📝 {r['content']}"
                else:
                    msg = f"⏰ {display_time}\n📝 {r['content']}"
                
                success, _ = send_telegram(msg)
                
                if success:
                    if r.get('is_recurring'):
                        next_time = calculate_next_run(r['remind_time'], r['recurrence_type'], r['recurrence_value'])
                        db_manager.update_reminder_time(r['id'], next_time)
                    else:
                        db_manager.update_status(r['id'], 'sent')

# ==========================================================
# 區塊 3：背景執行緒常駐迴圈
# ==========================================================
def continuous_run():
    while True:
        check_and_send_reminders()
        time.sleep(30) # 每 30 秒掃描一次

def start_background_task():
    global _scheduler_started
    with _scheduler_lock:
        if not _scheduler_started:
            thread = threading.Thread(target=continuous_run, daemon=True, name="RMDR_Worker")
            thread.start()
            _scheduler_started = True
