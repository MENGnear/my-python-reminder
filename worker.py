# ==========================================================
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# 專案名稱 : 提醒備忘系統 - 背景排程大腦 (獨立運行版)
# 檔案名稱 : worker.py
# 程式版本 : V3.0.0 
# 進版說明 : 
#   1. 從網頁端徹底分離，成為純背景常駐程式。
#   2. 內建 15 分鐘「過期防護機制」，避免休眠喚醒時瘋狂補發舊訊息。
#   3. 獨立讀取設定檔與 API，不依賴 Streamlit 運行。
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# ==========================================================

import time
import datetime
import urllib.request
import json
import os
from modules import db_manager

# ==========================================================
# 區塊 1：時區與通用設定
# ==========================================================
TW_TZ = datetime.timezone(datetime.timedelta(hours=8))

# ==========================================================
# 區塊 2：系統設定檔讀取 (脫離 Streamlit 獨立讀取 Secrets)
# 備註：此區塊能自動找尋環境變數或 .streamlit/secrets.toml
# ==========================================================
def get_secret(key):
    # 優先嘗試環境變數
    val = os.environ.get(key)
    if val: return val
    
    # 嘗試手動解析 Streamlit secrets 檔案
    try:
        with open(".streamlit/secrets.toml", "r", encoding="utf-8") as f:
            for line in f:
                if key in line and "=" in line:
                    return line.split("=")[1].strip().strip('"').strip("'")
    except:
        pass
    return None

def send_telegram_rmdr(message):
    token = get_secret("TELEGRAM_RMDR_TOKEN")
    chat_id = get_secret("TELEGRAM_RMDR_CHAT_ID")
    if not token or not chat_id: 
        print("⚠️ 錯誤：找不到 Telegram Token 或 Chat ID")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": str(chat_id), "text": message, "parse_mode": "HTML"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try: 
        urllib.request.urlopen(req)
        return True
    except Exception as e: 
        print(f"⚠️ Telegram 發送失敗: {e}")
        return False

# ==========================================================
# 區塊 3：週期任務時間推算邏輯
# ==========================================================
def calculate_next_run(remind_time_str, recur_type, recur_val):
    """計算週期任務下一次觸發的精準時間"""
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
# 區塊 4：核心排程掃描與過期防護邏輯
# ==========================================================
def check_and_send_reminders():
    now = datetime.datetime.now(TW_TZ)
    
    # 從資料庫抓取所有任務
    reminders = db_manager.get_all_reminders()
    
    for r in reminders:
        if r['status'] == 'pending':
            # 將資料庫字串轉換為時間物件，進行精準比對
            remind_dt = datetime.datetime.strptime(r['remind_time'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=TW_TZ)
            
            # 計算時間差 (分鐘)
            diff_minutes = (now - remind_dt).total_seconds() / 60.0
            
            # 【V3.0.0 核心防護】：過期超過 15 分鐘的任務直接作廢，不補發
            if diff_minutes > 15:
                print(f"[{now.strftime('%H:%M:%S')}] 🛡️ 攔截過期任務，標記為 expired: {r['content']}")
                db_manager.update_status(r['id'], 'expired')
                continue
                
            # 時間到了，且在 15 分鐘有效期限內 -> 進行發送
            elif diff_minutes >= 0:
                db_manager.update_status(r['id'], 'processing') # 狀態鎖定
                
                # 格式化時間與圖示
                display_time = r['remind_time'][:16]
                if r.get('is_recurring'):
                    msg = f"🔄 {display_time}\n📝 {r['content']}"
                else:
                    msg = f"⏰ {display_time}\n📝 {r['content']}"
                
                # 執行推播
                success = send_telegram_rmdr(msg)
                
                # 更新後續狀態
                if success:
                    print(f"[{now.strftime('%H:%M:%S')}] ✅ 成功發送: {r['content']}")
                    if r.get('is_recurring'):
                        next_time = calculate_next_run(r['remind_time'], r['recurrence_type'], r['recurrence_value'])
                        db_manager.update_reminder_time(r['id'], next_time)
                    else:
                        db_manager.update_status(r['id'], 'sent')

# ==========================================================
# 區塊 5：主迴圈啟動
# ==========================================================
if __name__ == "__main__":
    print("🚀 RMDR Worker 背景大腦已啟動... 正在監控資料庫")
    db_manager.init_db() # 確保資料庫存在
    
    # 無限迴圈，每 30 秒掃描一次
    while True:
        try:
            check_and_send_reminders()
        except Exception as e:
            print(f"⚠️ 排程掃描發生異常: {e}")
        time.sleep(30)
