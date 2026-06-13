"""
提醒備忘系統 - 網頁主程式
Version: v1.0.0
"""
import streamlit as st
import datetime
from modules import db_manager

# 1. 初始化資料庫
db_manager.init_db()

# 2. 設定 Streamlit 頁面外觀
st.set_page_config(page_title="提醒備忘系統", page_icon="⏰", layout="wide")

# 設定台灣時區 (UTC+8)，修正雲端伺服器時間差
TW_TZ = datetime.timezone(datetime.timedelta(hours=8))

st.title("⏰ 我的提醒備忘錄")

# ----------------------------------------
# 左側邊欄：新增備忘錄區塊
# ----------------------------------------
with st.sidebar:
    st.header("➕ 新增提醒")
    
    # 取得當下的台灣時間作為預設值
    now_in_tw = datetime.datetime.now(TW_TZ)
    
    content = st.text_input("備忘內容", placeholder="例如：下午三點與供應商開會")
    remind_date = st.date_input("提醒日期", now_in_tw.date())
    remind_time = st.time_input("提醒時間", now_in_tw.time())
    
    if st.button("加入備忘錄", use_container_width=True):
        if content:
            full_datetime = datetime.datetime.combine(remind_date, remind_time)
            time_str = full_datetime.strftime("%Y-%m-%d %H:%M:%S")
            db_manager.add_reminder(content, time_str)
            st.success("✅ 成功加入！")
            st.rerun()
        else:
            st.error("⚠️ 請輸入備忘內容！")

# ----------------------------------------
# 主畫面：顯示現有備忘錄
# ----------------------------------------
st.subheader("📌 待辦清單")

reminders = db_manager.get_all_reminders()
pending_reminders = [r for r in reminders if r['status'] == 'pending']

if not pending_reminders:
    st.info("目前沒有待辦事項喔！🎉")
else:
    for r in pending_reminders:
        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 2, 1])
            
            with col1:
                st.write(f"**{r['content']}**")
            with col2:
                st.write(f"🕒 {r['remind_time']}")
            with col3:
                if st.button("🗑️ 刪除", key=f"del_{r['id']}"):
                    db_manager.delete_reminder(r['id'])
                    st.rerun()
            
            with st.expander("✏️ 修改這筆備忘錄"):
                orig_dt = datetime.datetime.strptime(r['remind_time'], "%Y-%m-%d %H:%M:%S")
                
                edit_content = st.text_input("修改內容", value=r['content'], key=f"ec_{r['id']}")
                
                ecol1, ecol2 = st.columns(2)
                with ecol1:
                    edit_date = st.date_input("修改日期", value=orig_dt.date(), key=f"ed_{r['id']}")
                with ecol2:
                    edit_time = st.time_input("修改時間", value=orig_dt.time(), key=f"et_{r['id']}")
                    
                if st.button("💾 儲存修改", key=f"save_{r['id']}", use_container_width=True):
                    new_time_str = datetime.datetime.combine(edit_date, edit_time).strftime("%Y-%m-%d %H:%M:%S")
                    db_manager.edit_reminder(r['id'], edit_content, new_time_str)
                    st.rerun()
