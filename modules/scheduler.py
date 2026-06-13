"""
提醒備忘系統 - 背景排程器模組
Version: v1.0.0
"""
import time
import datetime
import threading
from modules import db_manager
from modules import line_bot_api

def check_and_send_reminders():
    """檢查資料庫並發送提醒"""
    # 取得當前台灣時間
    TW_TZ = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(TW_TZ)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # 撈取所有備忘錄
    reminders = db_manager.get_all_reminders()
    
    for r in reminders:
        # 判斷邏輯：狀態是 pending 且 現在時間 >= 提醒時間
        if r['status'] == 'pending' and now_str >= r['remind_time']:
            # 組合推播訊息
            msg = f"⏰ 【備忘提醒】\n{r['content']}\n設定時間: {r['remind_time']}"
            
            # 觸發 LINE 發送
            success = line_bot_api.send_message(msg)
            
            # 如果發送成功，更新資料庫狀態為已發送 (sent)
            if success:
                db_manager.update_status(r['id'], 'sent')
                print(f"✅ 自動推播成功: {r['content']}")

def continuous_run():
    """背景持續執行的迴圈"""
    while True:
        check_and_send_reminders()
        time.sleep(30)  # 每 30 秒掃描一次資料庫

def start_background_task():
    """啟動背景執行緒 (Daemon Thread)"""
    thread = threading.Thread(target=continuous_run, daemon=True)
    thread.start()
