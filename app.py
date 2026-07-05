# ==========================================================
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# 專案名稱 : 提醒備忘系統 - 網頁主程式 (Telegram 深色戰情室 UI 版)
# 檔案名稱 : app.py
# 程式版本 : v2.2.2 (回歸 config.toml 配色、重組週期三列佈局)
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# ==========================================================

import streamlit as st
import datetime
import json
import urllib.request
import os
from modules import db_manager
from modules import scheduler

# ==========================================================
# 1️⃣ 🚀 頁面設定
# ==========================================================
st.set_page_config(
    page_title="提醒備忘系統", 
    page_icon="⏰", 
    layout="wide",
    initial_sidebar_state="auto" 
)

# ==========================================================
# 2️⃣ 🎨 注入純淨 CSS (僅保留裝飾與邊框，不干擾 config.toml 字體顏色)
# ==========================================================
st.markdown(r'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* 全域字型設定 */
html, body, [data-testid="stAppViewContainer"] { 
    font-family: 'Inter', sans-serif !important; 
}

header[data-testid="stHeader"] { background-color: transparent !important; }
.main .block-container { padding-top: 1.5rem !important; margin-top: -30px !important; }

/* 區塊容器細節美化 */
[data-testid="stVerticalBlockBorderWrapper"] { 
    background-color: #1e293b !important; 
    border: 1px solid #475569 !important; 
    border-radius: 12px !important; 
    padding: 15px !important; 
    margin-bottom: 10px !important; 
}

/* 戰情室專屬漸層按鈕 */
.stButton > button { 
    background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important; 
    color: white !important; 
    border: none !important; 
    border-radius: 8px !important; 
    font-weight: 600 !important; 
    transition: all 0.2s ease !important; 
}
.stButton > button:hover { 
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important; 
    transform: translateY(-1px) !important; 
}

/* 主標題樣式 */
h1.main-title { 
    color: #f8fafc; 
    font-weight: 800; 
    text-align: left; 
    padding-bottom: 10px; 
    border-bottom: 2px solid #1e293b; 
    margin-bottom: 20px; 
    font-size: 1.8rem; 
}

/* 垂直置中輔助 */
.valign-text { margin-top: 6px; }
</style>
''', unsafe_allow_html=True)

# ==========================================================
# 3️⃣ ⚙️ 初始化與設定
# ==========================================================
APP_VERSION = "v2.2.2"
TW_TZ = datetime.timezone(datetime.timedelta(hours=8))
now_in_tw = datetime.datetime.now(TW_TZ)

# 防止時間跳動的 session_state 初始化
if "init_date" not in st.session_state:
    st.session_state.init_date = now_in_tw.date()
if "init_time" not in st.session_state:
    st.session_state.init_time = now_in_tw.time()

def send_telegram_rmdr(message):
    token = st.secrets.get("TELEGRAM_RMDR_TOKEN", os.environ.get('TELEGRAM_RMDR_TOKEN'))
    chat_id = st.secrets.get("TELEGRAM_RMDR_CHAT_ID", os.environ.get('TELEGRAM_RMDR_CHAT_ID'))
    if not token or not chat_id: return False, "找不到設定"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": str(chat_id), "text": message, "parse_mode": "HTML"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try: 
        urllib.request.urlopen(req)
        return True, "發送成功"
    except Exception as e: return False, f"失敗: {e}"

db_manager.init_db()

@st.cache_resource
def init_scheduler():
    scheduler.start_background_task()
    return True

init_scheduler()

# ==========================================================
# 4️⃣ 📱 UI 渲染 - 側邊欄 (全新佈局)
# ==========================================================
with st.sidebar:
    with st.container(border=True):
        st.markdown("### ➕ 新增備忘錄")
        
        task_type = st.radio("📌 任務類型", ["單次提醒", "週期提醒"], horizontal=True)
        content = st.text_input("備忘內容", placeholder="例如：下午三點開會或每月繳費")
        
        if task_type == "單次提醒":
            col1, col2 = st.columns(2)
            with col1:
                remind_date = st.date_input("提醒日期", value=st.session_state.init_date, key="new_d")
            with col2:
                remind_time = st.time_input("設定時間", value=st.session_state.init_time, key="new_t")
            
            remind_time_str = f"{remind_date} {remind_time.strftime('%H:%M')}:00"
            is_recurring, recurrence_type, recurrence_value = 0, "", ""
            
        else:
            # 🔁 週期提醒：嚴格整合為等寬垂直向下生長的三列結構
            
            # a. 週期 (第一列)
            recurrence_type = st.selectbox("週期", ["每天", "每月", "每年"], key="recur_type_sel")
            
            # b. 週期對應參數 (第二列)
            if recurrence_type == "每天":
                st.text_input("執行頻率", value="每日發送", disabled=True, key="recur_val_daily")
                recurrence_value = "daily"
            elif recurrence_type == "每月":
                recurrence_value = st.number_input("日期 (1-31)", min_value=1, max_value=31, value=1, key="recur_val_monthly")
            elif recurrence_type == "每年":
                recurrence_value = st.text_input("月/日 (MM-DD)", placeholder="例如: 05-01", key="recur_val_yearly")
            
            # c. 設定時間 (第三列)
            remind_time = st.time_input("設定時間", value=st.session_state.init_time, key="new_rt")
            
            remind_time_str = f"{now_in_tw.date()} {remind_time.strftime('%H:%M')}:00" 
            is_recurring = 1
            recurrence_value = str(recurrence_value)

        if st.button("➕ 確認新增", use_container_width=True):
            if content:
                db_manager.add_reminder(content, remind_time_str, is_recurring, recurrence_type, recurrence_value)
                st.success("✅ 成功新增！")
                st.rerun()
            else:
                st.error("⚠️ 內容不能為空！")
                
    with st.container(border=True):
        st.markdown("### 🛠️ 測試 Telegram")
        if st.button("發送測試訊息", use_container_width=True):
            test_dt_str = now_in_tw.strftime("%Y-%m-%d %H:%M")
            display_content = content if content else "[未輸入內容]"
            test_icon = "🔁" if task_type == "週期提醒" else "📌"
            
            test_msg = f"{test_icon}{test_dt_str}\n📁{display_content}\n⭐手動測試"
            success, msg = send_telegram_rmdr(test_msg)
            if success: st.success("✅ 發送成功！")
            else: st.error(msg)

    # 系統狀態卡片
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    tpe_now = now_utc.astimezone(TW_TZ)
    tpe_time_str = tpe_now.strftime("%H:%M:%S %m/%d/%Y")

    st.markdown(
        f"""
        <div style="background-color:#1e293b; padding:12px; border-radius:8px; border:1px solid #475569; text-align:center; margin-top:15px; margin-bottom:15px;">
            <div style="color:#94a3b8; font-size:0.8rem; font-weight:600; margin-bottom:4px;">系統當前版本</div>
            <div style="color:#38bdf8; font-size:1.1rem; font-weight:700; margin-bottom:10px;">{APP_VERSION}</div>
            <div style="color:#94a3b8; font-size:0.8rem; font-weight:600; margin-bottom:8px;">🕒 系統當前時間</div>
            <div style="color:#f1f5f9; font-size:0.88rem; font-weight:600; margin-bottom:2px;">Tw {tpe_time_str}</div>
        </div>
        """, unsafe_allow_html=True
    )

# ==========================================================
# 5️⃣ 📈 UI 渲染 - 主畫面清單 (4欄並排 + 原地修改)
# ==========================================================
st.markdown('<h1 class="main-title">⏰ 我的提醒備忘錄清單</h1>', unsafe_allow_html=True)
tab1, tab2 = st.tabs(["📅 單次待辦清單", "🔁 週期任務管理"])

reminders = db_manager.get_all_reminders()
single_tasks = [r for r in reminders if not r.get('is_recurring') and r.get('status') == 'pending']
recurring_tasks = [r for r in reminders if r.get('is_recurring')]

def render_task(r):
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([5, 4, 1.5, 1.5])
        
        display_time = r['remind_time'][:16]
        icon = "🔁" if r.get('is_recurring') else "📝"
        
        with col1:
            st.markdown(f"<div class='valign-text'><span style='font-size:1.1rem; font-weight:700;'>{icon} {r['content']}</span></div>", unsafe_allow_html=True)
        with col2:
            if r.get('is_recurring'):
                st.markdown(f"<div class='valign-text'><span style='color:#10b981; font-size:0.95rem; font-weight:600;'>🕒 {display_time} ({r['recurrence_type']})</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='valign-text'><span style='color:#38bdf8; font-size:1.0rem; font-weight:600;'>🕒 {display_time}</span></div>", unsafe_allow_html=True)
        with col3:
            if st.button("🗑️ 刪除", key=f"del_{r['id']}", use_container_width=True):
                db_manager.delete_reminder(r['id'])
                st.rerun()
        with col4:
            if st.button("✏️ 修改", key=f"btn_edit_{r['id']}", use_container_width=True):
                st.session_state[f"edit_{r['id']}"] = not st.session_state.get(f"edit_{r['id']}", False)
                st.rerun()
                
    # A 方案：原地展開修改區域
    if st.session_state.get(f"edit_{r['id']}", False):
        with st.container(border=True):
            orig_dt = datetime.datetime.strptime(r['remind_time'], "%Y-%m-%d %H:%M:%S")
            edit_content = st.text_input("📝 修改內容", value=r['content'], key=f"ec_{r['id']}")
            
            ecol1, ecol2 = st.columns(2)
            with ecol1:
                edit_date = st.date_input("修改日期", value=orig_dt.date(), key=f"ed_{r['id']}")
            with ecol2:
                edit_time = st.time_input("修改時間", value=orig_dt.time(), key=f"et_{r['id']}")
                
            new_time_str = f"{edit_date} {edit_time.strftime('%H:%M')}:00"
            
            scol1, scol2 = st.columns(2)
            with scol1:
                if st.button("💾 儲存修改", key=f"save_{r['id']}", use_container_width=True):
                    db_manager.update_reminder(r['id'], edit_content, new_time_str)
                    st.session_state[f"edit_{r['id']}"] = False
                    st.rerun()
            with scol2:
                if st.button("❌ 取消", key=f"cancel_{r['id']}", use_container_width=True):
                    st.session_state[f"edit_{r['id']}"] = False
                    st.rerun()

with tab1:
    if not single_tasks: st.info("💡 目前沒有待辦的單次提醒事項。")
    else: 
        for r in single_tasks: render_task(r)

with tab2:
    if not recurring_tasks: st.info("💡 目前記憶中沒有任何固定發生的週期任務。")
    else:
        for r in recurring_tasks: render_task(r)
