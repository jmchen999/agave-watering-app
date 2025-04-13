import streamlit as st
from datetime import datetime, timedelta
import json
import os
import gspread
import traceback
from google.oauth2.service_account import Credentials

# === Google Sheets 設定 ===
SPREADSHEET_ID = "1wEIyYVWcfgj71z2UMk5_pSXAB8B07Zl0GF9kOUbWFQI"
SHEET_NAME = "工作表1"

CONFIG_FILE = "last_config.json"
RECORD_FILE = "records.txt"

def send_to_google_sheets(data):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds_dict = st.secrets["google"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sh.worksheet(SHEET_NAME)
        worksheet.append_row([
            data["plant_type"],
            data["start_date"],
            data["interval"],
            data["repeat"],
            data["schedule"],
            data["note"]
        ])
        st.success("✅ 已成功寫入 Google Sheets！")
    except Exception as e:
        st.error("❌ Google Sheets 寫入錯誤：\n" + str(e))
        st.code(traceback.format_exc(), language="python")

def save_last_config(plant_type, date_str, interval, repeat):
    config = {
        "plant_type": plant_type,
        "date": date_str,
        "interval": interval,
        "repeat": repeat
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_last_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_record(log_text):
    with open(RECORD_FILE, "a", encoding="utf-8") as file:
        file.write(log_text)

# === Streamlit 畫面開始 ===
st.set_page_config(page_title="龍舌蘭澆水預估工具", layout="centered")
st.title("🌵 龍舌蘭澆水預估工具")

config = load_last_config()

# === 澆水日處理 ===
default_date = datetime.strptime(config.get("date"), "%Y-%m-%d") if config.get("date") else datetime.today()

rain_override = st.checkbox("我想指定『下雨提早澆水』的日期")
if rain_override:
    rain_date = st.date_input("請選擇下雨日（即提早澆水日）", value=default_date)
    start_date = rain_date
    note = "因下雨提前澆水（選擇日期）"
else:
    start_date = default_date
    note = ""

with st.form("watering_form"):
    plant_type = st.selectbox("植株類型", ["大植株", "小植株"], index=0 if config.get("plant_type") == "大植株" else 1)
    interval = st.selectbox("澆水週期（天）", [3, 5, 7, 10, 14, 21, 28], index=[3, 5, 7, 10, 14, 21, 28].index(config.get("interval", 7)))
    repeat = st.selectbox("預估次數", [3, 5, 10, 15], index=[3, 5, 10, 15].index(config.get("repeat", 5)))
    submit = st.form_submit_button("開始預估")

if submit:
    try:
        save_last_config(plant_type, start_date.strftime("%Y-%m-%d"), interval, repeat)

        header = f"【{plant_type}】澆水預估\n最近一次澆水日：{start_date.strftime('%Y-%m-%d')}\n週期：{interval} 天，預估次數：{repeat}"
        st.success(header)

        schedule_text = ""
        log = header + "\n"
        for i in range(repeat):
            next_date = start_date + timedelta(days=interval * (i + 1))
            line = f"第 {i+1} 次：{next_date.strftime('%Y-%m-%d')}"
            st.write(line)
            schedule_text += line + "\n"
            log += line + "\n"

        if note:
            st.info(f"【備註】{note}")
            log += f"【備註】{note}\n"

        log += "-" * 30 + "\n"
        save_record(log)

        # ✅ 寫入 Google Sheets，並顯示成功訊息
        send_to_google_sheets({
            "plant_type": plant_type,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "interval": interval,
            "repeat": repeat,
            "schedule": schedule_text.strip(),
            "note": note
        })

    except Exception as e:
        st.error("❌ 發生錯誤：\n" + str(e))
        st.code(traceback.format_exc(), language="python")
