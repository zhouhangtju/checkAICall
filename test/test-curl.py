import pandas as pd
import requests
df = pd.read_excel("./data/20260108通话记录.xlsx", sheet_name="质差派单")
for i,row in df.iterrows():
    payload = {
        "robot_tag": "" if pd.isna(row["机器人标签"]) else str(row["机器人标签"]),
        "call_text": "" if pd.isna(row["通话文本"]) else str(row["通话文本"]),
        "scene_type": "质差派单",
    }
    url = "http://localhost:8000/api/v1/check_call"
    response = requests.post(url, json=payload, timeout=30)


    print(f"Row {i} response:", response.json())
