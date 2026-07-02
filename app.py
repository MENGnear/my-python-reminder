# ==========================================================
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# 專案名稱 : 提醒備忘系統 - 網頁主程式 (Telegram 深色戰情室 UI 版)
# 檔案名稱 : RMDR_app.py
# 程式版本 : v2.0.2 (RWD 手機適配與原生時間選擇器優化)
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# ==========================================================

import streamlit as st
import datetime
import json
import urllib.request
import os
from modules import db_manager
from modules import scheduler  # 引入排程器

# ==========================================================
# 1️⃣ 🚀 頁面設定 (加入 initial_sidebar_state="auto" 讓手機自動收折)
# ==========================================================
st.set_page_config(
    page_title="提醒備忘系統", 
    page_icon="⏰", 
    layout="wide",
    initial_sidebar_state="auto" 
)

# ==========================================================
# 2️⃣ 🎨 注入純淨 CSS 
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

/* 側邊欄與容器框線視覺 */
[data-testid="stSidebar"] { 
    background-color: #171a23 !important; 
    border-right: 1px solid #2d3748 !important; 
}
[data-testid="stVerticalBlockBorderWrapper"] { 
    background-color: #1e293b !important; 
    border: 1px solid #94a3b8 !important; 
    border-radius: 12px !important; 
    padding: 15px !important; 
    margin-bottom: 10px !important; 
}
[data-testid="collapsedControl"] svg, [data-testid="stSidebarCollapseButton"] svg { 
    color: #ffffff !important; fill: #ffffff !important; 
}

/* 輸入框與選單視覺 */
.stTextInput div[data-baseweb="input"], .stSelectbox div[data-baseweb="select"] > div { 
    background-color: #0f172a !important; 
    border: 1px solid #475569 !important; 
    border-radius: 8px !important;  
}
.stTextInput input { color: #ffffff !important; background-color: transparent !important; }
.stSelectbox div[data-baseweb="select"] span { color: #ffffff !important; }
[data-testid="stSidebar"] h3 { color: #ffffff !important; font-size: 1.1rem !important; font-weight: 700 !important; margin-bottom: 15px !important; margin-top: 0px !important; }
[data-testid="stWidgetLabel"] p, div[data-testid="stMarkdownContainer"] p { color: #cbd5e1 !important; font-weight: 600 !important; font-size: 0.95rem !important; }

/* 按鈕：漸層藍色與 Hover 效果 */
.stButton > button { 
    background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important; 
    color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; transition: all 0.2s ease !important; 
}
.stButton > button:hover { box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important; transform: translateY(-1px) !important; }

/* 主標題樣式 */
h1.main-title { color: #f8fafc; font-weight: 800; text-align: left; padding-bottom: 10px; border-bottom: 2px solid #1e293b; margin-bottom: 20px; font-size: 1.8rem; }
</style>
''', unsafe_allow_html=True)

# ==========================================================
# 3️⃣ ⚙️ 初始化與 Telegram API 設定
# ==========================================================
APP_VERSION = "v2.0.2"

# 設定台灣時區 (UTC+8)
TW_TZ = datetime.timezone(datetime.timedelta(hours=8))

# 建立專屬的 Telegram 發送函數 (區隔股票機械人)
def send_telegram_rmdr(message):
    token = None
    chat_id = None
    try:
        # 使用 RMDR 專屬的 Token，避免與股市警報混淆
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

# 1. 初始化資料庫
db_manager.init_db()

# 2. 啟動背景自動排程器
@st.cache_resource
def init_scheduler():
    scheduler.start_background_task()
    return True

init_scheduler()

# ==========================================================
# 4️⃣ 📱 UI 渲染 - 側邊欄
# ==========================================================
with st.sidebar:
    with st.container(border=True):
        st.markdown("### ➕ 新增備忘錄")
        st.markdown("<div style='color:#38bdf8; font-size:1.0rem; font-weight:700; margin-bottom:5px;'>✍️ 設定內容與時間</div>", unsafe_allow_html=True)
        
        now_in_tw = datetime.datetime.now(TW_TZ)
        
        content = st.text_input("備忘內容", placeholder="例如：下午三點開會")
        
        # 升級為原生 Date 與 Time Input (解決手機截斷問題)
        col1, col2 = st.columns(2)
        with col1:
            remind_date = st.date_input("提醒日期", now_in_tw.date())
        with col2:
            remind_time = st.time_input("設定時間", now_in_tw.time())
            
        # 組合字串並固定秒數為 00
        remind_time_str = f"{remind_date} {remind_time.strftime('%H:%M')}:00"
        
        if st.button("➕ 確認新增", use_container_width=True):
            if content:
                db_manager.add_reminder(content, remind_time_str)
                st.success(f"✅ 成功新增提醒：{remind_time_str}")
                st.rerun()
            else:
                st.error("⚠️ 內容不能為空！")
                
    # 測試推播功能區塊
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
# 5️⃣ 📈 UI 渲染 - 主畫面清單
# ==========================================================
st.markdown('<h1 class="main-title">⏰ 我的提醒備忘錄清單</h1>', unsafe_allow_html=True)

reminders = db_manager.get_all_reminders()

if not reminders:
    st.info("💡 目前沒有待辦提醒事項。請從左側新增！")
else:
    for r in reminders:
        with st.container(border=True):
            col1, col2, col3 = st.columns([5, 3, 2])
            with col1:
                st.markdown(f"<span style='color:#f1f5f9; font-size:1.1rem; font-weight:700;'>📝 {r['content']}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<span style='color:#38bdf8; font-size:1.0rem; font-weight:600;'>🕒 {r['remind_time']}</span>", unsafe_allow_html=True)
            with col3:
                if st.button("🗑️ 刪除", key=f"del_{r['id']}", use_container_width=True):
                    db_manager.delete_reminder(r['id'])
                    st.rerun()
            
            with st.expander("✏️ 修改這筆備忘錄"):
                orig_dt = datetime.datetime.strptime(r['remind_time'], "%Y-%m-%d %H:%M:%S")
                
                edit_content = st.text_input("修改內容", value=r['content'], key=f"ec_{r['id']}")
                
                # 同樣升級為原生 Date 與 Time Input
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
