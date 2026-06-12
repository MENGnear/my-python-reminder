import streamlit as st
import datetime
from modules import db_manager

# 1. 初始化資料庫 (確保資料庫檔案與資料表存在)
db_manager.init_db()

# 2. 設定 Streamlit 頁面外觀 (深色模式通常跟隨使用者瀏覽器或在 Settings 中設定)
st.set_page_config(page_title="提醒備忘系統", page_icon="⏰", layout="wide")

st.title("⏰ 我的提醒備忘錄")

# ----------------------------------------
# 左側邊欄：新增備忘錄區塊
# ----------------------------------------
with st.sidebar:
    st.header("➕ 新增提醒")
    
    # 接收使用者輸入
    content = st.text_input("備忘內容", placeholder="例如：下午三點與供應商開會")
    remind_date = st.date_input("提醒日期", datetime.date.today())
    remind_time = st.time_input("提醒時間", datetime.datetime.now().time())
    
    if st.button("加入備忘錄", use_container_width=True):
        if content:
            # 將日期與時間合併成字串格式
            full_datetime = datetime.datetime.combine(remind_date, remind_time)
            time_str = full_datetime.strftime("%Y-%m-%d %H:%M:%S")
            
            # 呼叫資料庫模組寫入資料
            db_manager.add_reminder(content, time_str)
            
            st.success("✅ 成功加入！")
            st.rerun()  # 重新整理頁面以顯示最新資料
        else:
            st.error("⚠️ 請輸入備忘內容！")

# ----------------------------------------
# 主畫面：顯示現有備忘錄 (卡片式視覺)
# ----------------------------------------
st.subheader("📌 待辦清單")

# 從資料庫讀取所有資料
reminders = db_manager.get_all_reminders()

# 過濾出狀態為 'pending' (尚未提醒) 的項目
pending_reminders = [r for r in reminders if r['status'] == 'pending']

if not pending_reminders:
    st.info("目前沒有待辦事項喔！🎉")
else:
    # 使用迴圈產生卡片式清單
    for r in pending_reminders:
        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 2, 1])
            
            with col1:
                st.write(f"**{r['content']}**")
            with col2:
                st.write(f"🕒 {r['remind_time']}")
            with col3:
                # 刪除按鈕：使用資料庫的 id 作為按鈕的 key 避免衝突
                if st.button("🗑️ 刪除", key=f"del_{r['id']}"):
                    db_manager.delete_reminder(r['id'])
                    st.rerun()  # 刪除後重新整理畫面
