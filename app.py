# ==========================================================
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# 專案名稱 : 提醒備忘系統 - 網頁主程式 (Telegram 深色戰情室 UI 版)
# 檔案名稱 : app.py
# 程式版本 : v2.1.0 (新增單次與週期任務分頁管理、優化 UI)
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
# 2️⃣ 🎨 注入純淨 CSS (維持戰情室風格並優化頁籤)
# ==========================================================
st.markdown(r'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [data-testid="stAppViewContainer"] { 
    font-family: 'Inter', sans-serif !important; 
    background-color: #0e1117 !important; 
    color: #f1f5f9 !important; 
}
header[data-testid="stHeader"] { background-color: transparent !important; }
.main .block-container { padding-top: 1.5rem !important; margin-top: -30px !important; }
[data-testid="stSidebar"] { background-color: #171a23 !important; border-right: 1px solid #2d3748 !important; }
[data-testid="stVerticalBlockBorderWrapper"] { background-color: #1e293b !important; border: 1px solid #94a3b8 !important; border-radius: 12px !important; padding: 15px !important; margin-bottom: 10px !important; }
[data-testid="collapsedControl"] svg, [data-testid="stSidebarCollapseButton"] svg { color: #ffffff !important; fill: #ffffff !important; }
.stTextInput div[data-baseweb="input"], .stSelectbox div[data-baseweb="select"] > div { background-color: #0f172a !important; border: 1px solid #475569 !important; border-radius: 8px !important;  }
.stTextInput input { color: #ffffff !important; background-color: transparent !important; }
.stSelectbox div[data-baseweb="select"] span { color: #ffffff !important; }
[data-testid="stSidebar"] h3 { color: #ffffff !important; font-size: 1.1rem !important; font-weight: 700 !important; margin-bottom: 15px !important; margin-top: 0px !important; }
[data-testid="stWidgetLabel"] p, div[data-testid="stMarkdownContainer"] p { color: #cbd5e1 !important; font-weight: 600 !important; font-size: 0.95rem !important; }
.stButton > button { background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; transition: all 0.2s ease !important; }
.stButton > button:hover { box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important; transform: translateY(-1px) !important; }
h1.main-title { color: #f8fafc; font-weight: 800; text-align: left; padding-bottom: 10px; border-bottom: 2px solid #1e293b; margin-bottom: 20px; font-size: 1.8rem; }
/* 頁籤樣式優化 */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { background-color: #1e293b; border-radius: 8px 8px 0 0; padding: 10px 20px; border: 1px solid #475569; border-bottom: none; }
.stTabs [aria-selected="true"] { background-color: #3b82f6; border-color: #3b82f6; }
</style>
''', unsafe_allow_html=True)

# ==========================================================
# 3️⃣ ⚙️ 初始化與設定
# ==========================================================
APP_VERSION = "v2.1.0"
TW_TZ = datetime.timezone(datetime.timedelta(hours=8))

# 建立專屬的 Telegram 發送函數
def send_telegram_rmdr(message):
    token = None
    chat_id = None
    try:
        token = st.secrets.get("TELEGRAM_RMDR_TOKEN", os.environ.get('TELEGRAM_RMDR_TOKEN'))
        chat_id = st.secrets.get("TELEGRAM_RMDR_CHAT_ID", os.environ.get('TELEGRAM_RMDR_CHAT_ID'))
    except: pass
    
    if not token or not chat_id: 
        return False, "找不到 Telegram RMDR 設定"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": str(chat_id), "text": message, "parse_mode": "HTML"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try: 
        urllib.request.urlopen(req)
        return True, "發送成功"
    except Exception as e: 
        return False, f"Telegram 發送失敗: {e}"

# 初始化資料庫
db_manager.init_db()

# 啟動背景自動排程器
@st.cache_resource
def init_scheduler():
    scheduler.start_background_task()
    return True

init_scheduler()

# ==========================================================
# 4️⃣ 📱 UI 渲染 - 側邊欄 (動態表單)
# ==========================================================
with st.sidebar:
    with st.container(border=True):
        st.markdown("### ➕ 新增備忘錄")
        
        task_type = st.radio("📌 任務類型", ["單次提醒", "週期提醒"], horizontal=True)
        content = st.text_input("備忘內容", placeholder="例如：下午三點開會或每月繳費")
        
        now_in_tw = datetime.datetime.now(TW_TZ)
        
        if task_type == "單次提醒":
            col1, col2 = st.columns(2)
            with col1:
                remind_date = st.date_input("提醒日期", now_in_tw.date())
            with col2:
                remind_time = st.time_input("設定時間", now_in_tw.time())
            
            # 單次任務參數
            remind_time_str = f"{remind_date} {remind_time.strftime('%H:%M')}:00"
            is_recurring = 0
            recurrence_type = ""
            recurrence_value = ""
            
        else:
            col_type, col_val = st.columns(2)
            with col_type:
                recurrence_type = st.selectbox("週期", ["每天", "每月", "每年"])
            with col_val:
                if recurrence_type == "每天":
                    st.info("每日固定觸發")
                    recurrence_value = "daily"
                elif recurrence_type == "每月":
                    recurrence_value = st.number_input("日期 (1-31)", min_value=1, max_value=31, value=1)
                elif recurrence_type == "每年":
                    recurrence_value = st.text_input("月/日 (MM-DD)", placeholder="例如: 05-01")
            
            remind_time = st.time_input("設定時間", now_in_tw.time())
            
            # 週期任務我們先設定一個初始計算用的 dummy_time
            remind_time_str = f"{now_in_tw.date()} {remind_time.strftime('%H:%M')}:00" 
            is_recurring = 1
            recurrence_type = recurrence_type
            recurrence_value = str(recurrence_value)

        if st.button("➕ 確認新增", use_container_width=True):
            if content:
                db_manager.add_reminder(content, remind_time_str, is_recurring, recurrence_type, recurrence_value)
                st.success("✅ 成功新增任務！")
                st.rerun()
            else:
                st.error("⚠️ 內容不能為空！")
                
    with st.container(border=True):
        st.markdown("### 🛠️ 測試 Telegram 通訊")
        if st.button("發送測試訊息", use_container_width=True):
            success, msg = send_telegram_rmdr("🔔 <b>備忘錄系統測試</b>\n這是一則測試訊息，如果看到這行字，代表新的 Telegram 機械人設定成功！")
            if success:
                st.success("✅ 發送成功！請檢查手機")
            else:
                st.error(msg)

    # 系統狀態備註卡片
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
# 5️⃣ 📈 UI 渲染 - 主畫面清單 (雙頁籤)
# ==========================================================
st.markdown('<h1 class="main-title">⏰ 我的提醒備忘錄清單</h1>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📅 單次待辦清單", "🔁 週期任務管理"])

reminders = db_manager.get_all_reminders()

# 整理分類資料 (過濾掉已發送的單次任務)
single_tasks = [r for r in reminders if not r.get('is_recurring') and r.get('status') == 'pending']
recurring_tasks = [r for r in reminders if r.get('is_recurring')]

def render_task(r):
    with st.container(border=True):
        col1, col2, col3 = st.columns([5, 3, 2])
        with col1:
            icon = "🔁" if r.get('is_recurring') else "📝"
            st.markdown(f"<span style='color:#f1f5f9; font-size:1.1rem; font-weight:700;'>{icon} {r['content']}</span>", unsafe_allow_html=True)
        with col2:
            if r.get('is_recurring'):
                info = f"{r['recurrence_type']} ({r['recurrence_value']}) {r['remind_time'][-8:]}"
                st.markdown(f"<span style='color:#10b981; font-size:0.95rem; font-weight:600;'>設定規則: {info}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:#38bdf8; font-size:1.0rem; font-weight:600;'>🕒 {r['remind_time']}</span>", unsafe_allow_html=True)
        with col3:
            if st.button("🗑️ 刪除", key=f"del_{r['id']}", use_container_width=True):
                db_manager.delete_reminder(r['id'])
                st.rerun()
            
            # 單次任務保留編輯功能
            if not r.get('is_recurring'):
                with st.expander("✏️ 修改這筆備忘錄"):
                    orig_dt = datetime.datetime.strptime(r['remind_time'], "%Y-%m-%d %H:%M:%S")
                    
                    edit_content = st.text_input("修改內容", value=r['content'], key=f"ec_{r['id']}")
                    
                    ecol1, ecol2 = st.columns(2)
                    with ecol1:
                        edit_date = st.date_input("修改日期", value=orig_dt.date(), key=f"ed_{r['id']}")
                    with ecol2:
                        edit_time = st.time_input("修改時間", value=orig_dt.time(), key=f"et_{r['id']}")
                        
                    new_time_str = f"{edit_date} {edit_time.strftime('%H:%M')}:00"
                    
                    if st.button("💾 儲存修改", key=f"save_{r['id']}", use_container_width=True):
                        db_manager.update_reminder(r['id'], edit_content, new_time_str)
                        st.success("✅ 修改成功！")
                        st.rerun()

with tab1:
    if not single_tasks: st.info("💡 目前沒有待辦的單次提醒事項。")
    else: 
        for r in single_tasks: render_task(r)

with tab2:
    if not recurring_tasks: st.info("💡 目前沒有週期性任務。")
    else:
        for r in recurring_tasks: render_task(r)
