"""
提醒備忘系統 - 網頁主程式
Version: v1.0.3
"""
import streamlit as st
import datetime
from modules import db_manager
from modules import line_bot_api  # 引入我們剛剛寫好的 LINE 模組

# 1. 初始化資料庫
db_manager.init_db()

# 2. 設定 Streamlit 頁面外觀
st.set_page_config(page_title="提醒備忘系統", page_icon="⏰", layout="wide")

# 設定台灣時區 (UTC+8)
TW_TZ = datetime.timezone(datetime.timedelta(hours=8))

st.title("⏰ 我的提醒備忘錄")

# ----------------------------------------
# 左側邊欄：新增備忘錄與系統時間
# ----------------------------------------
with st.sidebar:
    st.header("➕ 新增提醒")
    
    # 取得當下的台灣時間
    now_in_tw = datetime.datetime.now(TW_TZ)
    
    content = st.text_input("備忘內容", placeholder="例如：下午三點與供應商開會")
    remind_date = st.date_input("提醒日期", now_in_tw.date())
    
    st.markdown("提醒時間")
    t_col1, t_col2, t_col3 = st.columns(3)
    with t_col1:
        h_val = st.selectbox("小時", [f"{i:02d}" for i in range(24)], index=now_in_tw.hour)
    with t_col2:
        m1_val = st.selectbox("分(十位)", [str(i) for i in range(6)], index=now_in_tw.minute // 10)
    with t_col3:
        m2_val = st.selectbox("分(個位)", [str(i) for i in range(10)], index=now_in_tw.minute % 10)
    
    if st.button("加入備忘錄", use_container_width=True):
        if content:
            time_str = f"{remind_date.strftime('%Y-%m-%d')} {h_val}:{m1_val}{m2_val}:00"
            db_manager.add_reminder(content, time_str)
            st.success("✅ 成功加入！")
            st.rerun()
        else:
            st.error("⚠️ 請輸入備忘內容！")
            
    st.divider() 
    
    # ----------------------------------------
    # LINE Bot 測試按鈕區塊
    # ----------------------------------------
    st.markdown("### 🔧 系統連線測試")
    if st.button("發送 LINE 測試訊息", type="primary", use_container_width=True):
        success = line_bot_api.send_message("💡 測試訊息：你的專屬備忘錄機器人已成功連線！")
        if success:
            st.success("✅ 訊息已發送！請檢查手機 LINE。")
        else:
            st.error("❌ 發送失敗，請檢查 line_bot_api.py 裡面的密碼是否填錯。")

    st.divider()  
    st.markdown("### 🕒 目前台灣時間")
    st.metric(label="", value=now_in_tw.strftime("%Y-%m-%d"), delta=now_in_tw.strftime("%H:%M:%S"), delta_color="off")
    st.caption("提示：重新整理網頁或操作按鈕即可更新時間")

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
                edit_date = st.date_input("修改日期", value=orig_dt.date(), key=f"ed_{r['id']}")
                
                st.markdown("修改時間")
                ecol1, ecol2, ecol3 = st.columns(3)
                with ecol1:
                    e_h_val = st.selectbox("小時", [f"{i:02d}" for i in range(24)], index=orig_dt.hour, key=f"eh_{r['id']}")
                with ecol2:
                    e_m1_val = st.selectbox("分(十位)", [str(i) for i in range(6)], index=orig_dt.minute // 10, key=f"em1_{r['id']}")
                with ecol3:
                    e_m2_val = st.selectbox("分(個位)", [str(i) for i in range(10)], index=orig_dt.minute % 10, key=f"em2_{r['id']}")
                    
                if st.button("💾 儲存修改", key=f"save_{r['id']}", use_container_width=True):
                    new_time_str = f"{edit_date.strftime('%Y-%m-%d')} {e_h_val}:{e_m1_val}{e_m2_val}:00"
                    db_manager.edit_reminder(r['id'], edit_content, new_time_str)
                    st.rerun()
