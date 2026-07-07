# ==========================================================
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# 專案名稱 : 提醒備忘系統 - 網頁主程式 (Telegram 深色戰情室 UI 版)
# 檔案名稱 : app.py
# 程式版本 : v2.2.5 
# 進版說明 : 
#   1. 升級主畫面頁籤為具備狀態連動的戰情室橫向導覽按鈕。
#   2. 實作「測試 Telegram」按鈕的脈絡感知功能，自動判定當前頁面發送對應格式。
#   3. 完整保留過往所有 UI 排版優化與原地修改 A 方案心血。
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
# 1️⃣ 🚀 頁面設定 (支援手機自動收折)
# ==========================================================
st.set_page_config(
    page_title="提醒備忘系統", 
    page_icon="⏰", 
    layout="wide",
    initial_sidebar_state="auto" 
)

# ==========================================================
# 2️⃣ 🎨 注入純淨 CSS (優化自訂導覽頁籤與按鈕外觀，不干擾 config.toml)
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

/* 戰情室專專屬漸層按鈕 */
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

/* 方案 B 專屬：將 Radio 美化為橫向高質感頁籤按鈕 */
div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] {
    gap: 10px;
}
</style>
''', unsafe_allow_html=True)

# ==========================================================
# 3️⃣ ⚙️ 初始化與設定 (時區、Session State 與 Telegram API)
# ==========================================================
APP_VERSION = "v2.2.5"
TW_TZ = datetime.timezone(datetime.timedelta(hours=8))
now_in_tw = datetime.datetime.now(TW_TZ)

# 防止時間跳動的 session_state 初始化
if "init_date" not in st.session_state:
    st.session_state.init_date = now_in_tw.date()
if "init_time" not in st.session_state:
    st.session_state.init_time = now_in_tw.time()

# Telegram 訊息發送底層函式
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

# 載入資料庫
db_manager.init_db()

# 啟動自動排程器 (確保背景唯一執行緒)
@st.cache_resource
def init_scheduler():
    scheduler.start_background_task()
    return True

init_scheduler()

# ==========================================================
# 4️⃣ 📱 UI 渲染 - 側邊欄 (控制區表單與脈絡測試按鈕)
# ==========================================================
with st.sidebar:
    with st.container(border=True):
        st.markdown("### ➕ 新增備忘錄")
        
        task_type = st.radio("📌 任務類型", ["單次提醒", "週期提醒"], horizontal=True)
        content = st.text_input("備忘內容", placeholder="例如：下午三點開會或每月繳費")
        
        if task_type == "單次提醒":
            # 單次提醒垂直平鋪結構 (v2.2.3 優化)
            remind_date = st.date_input("提醒日期", value=st.session_state.init_date, key="new_d")
            remind_time = st.time_input("設定時間", value=st.session_state.init_time, key="new_t")
            
            remind_time_str = f"{remind_date} {remind_time.strftime('%H:%M')}:00"
            is_recurring, recurrence_type, recurrence_value = 0, "", ""
            
        else:
            # 週期提醒三列滿寬垂直結構 (v2.2.2 優化)
            recurrence_type = st.selectbox("週期", ["每天", "每月", "每年"], key="recur_type_sel")
            
            if recurrence_type == "每天":
                st.text_input("執行頻率", value="每日發送", disabled=True, key="recur_val_daily")
                recurrence_value = "daily"
            elif recurrence_type == "每月":
                recurrence_value = st.number_input("日期 (1-31)", min_value=1, max_value=31, value=1, key="recur_val_monthly")
            elif recurrence_type == "每年":
                recurrence_value = st.text_input("月/日 (MM-DD)", placeholder="例如: 05-01", key="recur_val_yearly")
            
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
            
            # 【方案 B 核心功能】檢查主畫面當前所在的頁面名稱
            current_tab = st.session_state.get("main_page_nav", "📅 單次待辦清單")
            
            # 依據主畫面所在的頁面，智慧切換發送圖示與防呆內容
            if current_tab == "🔁 週期任務管理":
                test_icon = "🔄"
                display_content = content if content else "[未輸入週期內容]"
            else:
                test_icon = "⏰"
                display_content = content if content else "[未輸入單次內容]"
            
            test_msg = f"{test_icon} {test_dt_str}\n📝 {display_content}\n⭐ 手動測試"
            success, msg = send_telegram_rmdr(test_msg)
            if success: st.success("✅ 發送成功！")
            else: st.error(msg)

    # 系統狀態資訊卡片
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
# 5️⃣ 📈 UI 渲染 - 主畫面清單 (橫向導覽頁籤、4欄並排與 A 原地修改)
# ==========================================================
st.markdown('<h1 class="main-title">⏰ 我的提醒備忘錄清單</h1>', unsafe_allow_html=True)

# 【方案 B 核心功能】升級為可被後端程式感知狀態的橫向導覽按鈕頁籤
current_page = st.radio(
    "main_nav",
    ["📅 單次待辦清單", "🔁 週期任務管理"],
    horizontal=True,
    label_visibility="collapsed",
    key="main_page_nav"  # 綁定 key，讓側邊欄測試按鈕隨時讀取
)

# 撈取資料庫數據並分類
reminders = db_manager.get_all_reminders()
single_tasks = [r for r in reminders if not r.get('is_recurring') and r.get('status') == 'pending']
recurring_tasks = [r for r in reminders if r.get('is_recurring')]

# 共用單筆任務渲染函式 (包含 4 欄並排與原地修改機制)
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
                
    # A 方案：原地展開修改區域 (完好保護時間與日期格式)
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

# 根據當前感知到的導覽按鈕狀態，切換顯示對應資料清單
if current_page == "📅 單次待辦清單":
    if not single_tasks: 
        st.info("💡 目前沒有待辦的單次提醒事項。")
    else: 
        for r in single_tasks: render_task(r)

elif current_page == "🔁 週期任務管理":
    if not recurring_tasks: 
        st.info("💡 目前記憶中沒有任何固定發生的週期任務。")
    else:
        for r in recurring_tasks: render_task(r)
