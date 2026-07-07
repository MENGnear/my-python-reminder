# ==========================================================
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# 專案名稱 : 提醒備忘系統 - 網頁主程式 (Telegram 深色戰情室 UI 版)
# 檔案名稱 : app.py
# 程式版本 : V2.2.6 (雲端特化版)
# 進版說明 : 
#   1. 引入 streamlit_autorefresh 作為前端心跳，防止 SCC 休眠。
#   2. 實作「新增成功自動清空表單」，解決殘留字串錯覺。
#   3. 將測試按鈕移至主畫面各筆任務旁，實現 100% 精準測試發送。
#   4. 完整保留單次兩列、週期三列與 A 方案原地修改機制。
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# ==========================================================

import streamlit as st
import datetime
import json
import urllib.request
import os
from modules import db_manager
from modules import scheduler
from streamlit_autorefresh import st_autorefresh  # 【V2.2.6 新增】防休眠套件

# ==========================================================
# 區塊 1：🚀 頁面設定與自訂純淨 CSS
# ==========================================================
st.set_page_config(page_title="提醒備忘系統", page_icon="⏰", layout="wide", initial_sidebar_state="auto")

st.markdown(r'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [data-testid="stAppViewContainer"] { font-family: 'Inter', sans-serif !important; }
header[data-testid="stHeader"] { background-color: transparent !important; }
.main .block-container { padding-top: 1.5rem !important; margin-top: -30px !important; }
[data-testid="stVerticalBlockBorderWrapper"] { background-color: #1e293b !important; border: 1px solid #475569 !important; border-radius: 12px !important; padding: 15px !important; margin-bottom: 10px !important; }
.stButton > button { background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; transition: all 0.2s ease !important; }
.stButton > button:hover { box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important; transform: translateY(-1px) !important; }
h1.main-title { color: #f8fafc; font-weight: 800; text-align: left; padding-bottom: 10px; border-bottom: 2px solid #1e293b; margin-bottom: 20px; font-size: 1.8rem; }
.valign-text { margin-top: 6px; }
div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] { gap: 10px; }
</style>
''', unsafe_allow_html=True)

# ==========================================================
# 區塊 2：⚙️ 初始化、Session 狀態控制與 API
# ==========================================================
APP_VERSION = "V2.2.6"
TW_TZ = datetime.timezone(datetime.timedelta(hours=8))
now_in_tw = datetime.datetime.now(TW_TZ)

# 【V2.2.6 核心功能】前端定時刷新心跳 (5分鐘刷新一次)，假裝有人在看網頁，防止伺服器休眠
st_autorefresh(interval=5 * 60 * 1000, key="app_keepalive")

# 防止時間跳動的 session_state 初始化
if "init_date" not in st.session_state: st.session_state.init_date = now_in_tw.date()
if "init_time" not in st.session_state: st.session_state.init_time = now_in_tw.time()

# 【V2.2.6 變更】：綁定輸入框清空的專屬狀態
if "form_input_content" not in st.session_state: st.session_state.form_input_content = ""

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
# 區塊 3：📱 UI 渲染 - 側邊欄控制區
# ==========================================================
with st.sidebar:
    with st.container(border=True):
        st.markdown("### ➕ 新增備忘錄")
        
        task_type = st.radio("📌 任務類型", ["單次提醒", "週期提醒"], horizontal=True)
        # 綁定 session_state 以便後續新增成功時自動清空
        content = st.text_input("備忘內容", key="form_input_content", placeholder="例如：下午三點開會或每月繳費")
        
        if task_type == "單次提醒":
            remind_date = st.date_input("提醒日期", value=st.session_state.init_date, key="new_d")
            remind_time = st.time_input("設定時間", value=st.session_state.init_time, key="new_t")
            remind_time_str = f"{remind_date} {remind_time.strftime('%H:%M')}:00"
            is_recurring, recurrence_type, recurrence_value = 0, "", ""
            
        else:
            recurrence_type = st.selectbox("週期", ["每天", "每月", "每年"], key="recur_type_sel")
            if recurrence_type == "每天":
                st.text_input("執行頻率", value="每日發送", disabled=True)
                recurrence_value = "daily"
            elif recurrence_type == "每月":
                recurrence_value = st.number_input("日期 (1-31)", min_value=1, max_value=31, value=1)
            elif recurrence_type == "每年":
                recurrence_value = st.text_input("月/日 (MM-DD)", placeholder="例如: 05-01")
            
            remind_time = st.time_input("設定時間", value=st.session_state.init_time, key="new_rt")
            remind_time_str = f"{now_in_tw.date()} {remind_time.strftime('%H:%M')}:00" 
            is_recurring = 1
            recurrence_value = str(recurrence_value)

        if st.button("➕ 確認新增", use_container_width=True):
            if content:
                db_manager.add_reminder(content, remind_time_str, is_recurring, recurrence_type, recurrence_value)
                st.toast("✅ 成功新增！", icon="✅")
                # 【V2.2.6 核心功能】新增成功後，立刻清空輸入框，避免視覺殘留
                st.session_state.form_input_content = ""
                st.rerun()
            else:
                st.error("⚠️ 內容不能為空！")
                
    # 系統狀態卡片
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    tpe_now = now_utc.astimezone(TW_TZ)
    st.markdown(
        f"""
        <div style="background-color:#1e293b; padding:12px; border-radius:8px; border:1px solid #475569; text-align:center; margin-top:15px; margin-bottom:15px;">
            <div style="color:#94a3b8; font-size:0.8rem; font-weight:600; margin-bottom:4px;">系統當前版本</div>
            <div style="color:#38bdf8; font-size:1.1rem; font-weight:700; margin-bottom:10px;">{APP_VERSION}</div>
            <div style="color:#94a3b8; font-size:0.8rem; font-weight:600; margin-bottom:8px;">🕒 系統當前時間</div>
            <div style="color:#f1f5f9; font-size:0.88rem; font-weight:600; margin-bottom:2px;">Tw {tpe_now.strftime("%H:%M:%S %m/%d/%Y")}</div>
        </div>
        """, unsafe_allow_html=True
    )

# ==========================================================
# 區塊 4：📈 UI 渲染 - 主畫面清單與獨立發送測試
# ==========================================================
st.markdown('<h1 class="main-title">⏰ 我的提醒備忘錄清單</h1>', unsafe_allow_html=True)

current_page = st.radio("main_nav", ["📅 單次待辦清單", "🔁 週期任務管理"], horizontal=True, label_visibility="collapsed", key="main_page_nav")

reminders = db_manager.get_all_reminders()
single_tasks = [r for r in reminders if not r.get('is_recurring') and r.get('status') == 'pending']
recurring_tasks = [r for r in reminders if r.get('is_recurring')]

def render_task(r):
    with st.container(border=True):
        # 【V2.2.6 變更】：版面改為 5 欄，最右側加入該筆資料專屬的測試按鈕
        col1, col2, col3, col4, col5 = st.columns([4, 3.5, 1.3, 1.2, 1.2])
        
        display_time = r['remind_time'][:16]
        icon = "🔄" if r.get('is_recurring') else "⏰"
        text_icon = "🔁" if r.get('is_recurring') else "📝"
        
        with col1:
            st.markdown(f"<div class='valign-text'><span style='font-size:1.1rem; font-weight:700;'>{text_icon} {r['content']}</span></div>", unsafe_allow_html=True)
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
        with col5:
            # 【V2.2.6 核心功能】：單筆精準手動發送測試，完全同步資料庫格式
            if st.button("🚀 測試", key=f"test_{r['id']}", use_container_width=True):
                test_msg = f"{icon} {display_time}\n📝 {r['content']}\n⭐ 手動測試"
                success, msg_resp = send_telegram_rmdr(test_msg)
                if success: st.toast("✅ 發送成功！請檢查手機", icon="✅")
                else: st.error(f"發送失敗: {msg_resp}")
                
    # A 方案：原地展開修改區域
    if st.session_state.get(f"edit_{r['id']}", False):
        with st.container(border=True):
            orig_dt = datetime.datetime.strptime(r['remind_time'], "%Y-%m-%d %H:%M:%S")
            edit_content = st.text_input("📝 修改內容", value=r['content'], key=f"ec_{r['id']}")
            
            ecol1, ecol2 = st.columns(2)
            with ecol1: edit_date = st.date_input("修改日期", value=orig_dt.date(), key=f"ed_{r['id']}")
            with ecol2: edit_time = st.time_input("修改時間", value=orig_dt.time(), key=f"et_{r['id']}")
                
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

if current_page == "📅 單次待辦清單":
    if not single_tasks: st.info("💡 目前沒有待辦的單次提醒事項。")
    else: 
        for r in single_tasks: render_task(r)

elif current_page == "🔁 週期任務管理":
    if not recurring_tasks: st.info("💡 目前記憶中沒有任何固定發生的週期任務。")
    else:
        for r in recurring_tasks: render_task(r)
