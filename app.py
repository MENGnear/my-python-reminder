# ==========================================================
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# 專案名稱 : 提醒備忘系統 - 網頁主程式 (Telegram 深色戰情室 UI 版)
# 檔案名稱 : app.py
# 程式版本 : V2.2.8 (UI 版面優化版)
# 進版說明 : 
#   1. 【修正】調整 st.columns 比例為 [3.8, 3.2, 1.4, 1.4, 1.4]，確保按鈕等寬。
#   2. 【修正】CSS 增加 white-space: nowrap，防止電腦版按鈕文字被擠壓斷行。
#   3. 【維持】保留 V2.2.7 所有防休眠、動態 Key (防崩潰)、雙重確認 (防卡住) 邏輯。
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# ==========================================================

import streamlit as st
import datetime
import json
import urllib.request
import os
import time
from modules import db_manager
from modules import scheduler
from streamlit_autorefresh import st_autorefresh

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

/* 【V2.2.8 修正】：加入 white-space: nowrap !important; 防止按鈕文字斷行 */
.stButton > button { 
    background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important; 
    color: white !important; 
    border: none !important; 
    border-radius: 8px !important; 
    font-weight: 600 !important; 
    transition: all 0.2s ease !important; 
    white-space: nowrap !important; 
}
.stButton > button:hover { box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important; transform: translateY(-1px) !important; }

h1.main-title { color: #f8fafc; font-weight: 800; text-align: left; padding-bottom: 10px; border-bottom: 2px solid #1e293b; margin-bottom: 20px; font-size: 1.8rem; }
.valign-text { margin-top: 6px; }
div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] { gap: 10px; }
</style>
''', unsafe_allow_html=True)

# ==========================================================
# 區塊 2：⚙️ 初始化、Session 狀態控制與 API
# ==========================================================
APP_VERSION = "V2.2.8"
TW_TZ = datetime.timezone(datetime.timedelta(hours=8))
now_in_tw = datetime.datetime.now(TW_TZ)

# 前端定時刷新心跳 (5分鐘刷新一次)，防止伺服器休眠與同步資料庫狀態
st_autorefresh(interval=5 * 60 * 1000, key="app_keepalive")

# 防止時間跳動的 session_state 初始化
if "init_date" not in st.session_state: st.session_state.init_date = now_in_tw.date()
if "init_time" not in st.session_state: st.session_state.init_time = now_in_tw.time()

# 動態 Key 計數器 (金蟬脫殼戰術)，取代直接清空字串避免崩潰
if "input_counter" not in st.session_state: st.session_state.input_counter = 0

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

# 幽靈小卡雙重確認機制 (Double-Check)
def verify_task_alive(task_id):
    """確認該筆任務在資料庫中是否仍為 pending 狀態，防止對幽靈元件操作"""
    all_reminders = db_manager.get_all_reminders()
    for t in all_reminders:
        if t['id'] == task_id:
            if t['status'] == 'pending':
                return True # 任務活著，允許操作
            else:
                break # 找到了但狀態不是 pending
    st.error("⚠️ 動作無效：此任務已在背景執行完畢或過期！畫面即將同步...")
    time.sleep(1.5)
    st.rerun()
    return False

# ==========================================================
# 區塊 3：📱 UI 渲染 - 側邊欄控制區
# ==========================================================
with st.sidebar:
    with st.container(border=True):
        st.markdown("### ➕ 新增備忘錄")
        
        task_type = st.radio("📌 任務類型", ["單次提醒", "週期提醒"], horizontal=True)
        
        # 套用動態 Key (input_counter)
        dynamic_key = f"form_input_{st.session_state.input_counter}"
        content = st.text_input("備忘內容", key=dynamic_key, placeholder="例如：下午三點開會或每月繳費")
        
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
                # 不洗白字串，直接將計數器 +1 讓系統產生新輸入框 (金蟬脫殼)
                st.session_state.input_counter += 1
                st.rerun()
            else:
                st.error("⚠️ 內容不能為空！")
                
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
        # 【V2.2.8 修正】：重新分配欄位比例，讓三個按鈕的寬度權重保持一致 (1.4)，避免電腦版變形
        col1, col2, col3, col4, col5 = st.columns([3.8, 3.2, 1.4, 1.4, 1.4])
        
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
        
        # 按鈕皆綁定 verify_task_alive 雙重確認機制，並使用 container_width 撐滿欄位
        with col3:
            if st.button("🗑️ 刪除", key=f"del_{r['id']}", use_container_width=True):
                if verify_task_alive(r['id']):
                    db_manager.delete_reminder(r['id'])
                    st.rerun()
        with col4:
            if st.button("✏️ 修改", key=f"btn_edit_{r['id']}", use_container_width=True):
                if verify_task_alive(r['id']):
                    st.session_state[f"edit_{r['id']}"] = not st.session_state.get(f"edit_{r['id']}", False)
                    st.rerun()
        with col5:
            if st.button("🚀 測試", key=f"test_{r['id']}", use_container_width=True):
                if verify_task_alive(r['id']):
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
                    if verify_task_alive(r['id']): # 儲存時也再次確認防呆
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
