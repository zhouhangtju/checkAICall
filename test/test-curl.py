import pandas as pd
import requests
# df = pd.read_excel("./data/20260108通话记录.xlsx", sheet_name="装机单")
# df = pd.read_excel("./data/zjyd01_测试3-检查_通话记录_202601221153_zjyd01.xlsx")
# df = pd.read_excel("./data/zjyd01_测试.xlsx")
df = pd.read_excel("./data/zjyd01_测试任务_03.xlsx")


scene_type = "投诉单报结"
for i,row in df.iterrows():
    payload = {
        "robot_tag": "" if pd.isna(row["机器人标签"]) else str(row["机器人标签"]),
        "call_text": "" if pd.isna(row["通话文本"]) else str(row["通话文本"]),
        "scene_type": scene_type,
    }
    url = "http://localhost:8000/api/v1/check_call"
    response = requests.post(url, json=payload, timeout=30)




    # print(f"Row {i} response:", response.json())
    # print(f"Row {i} response:", response.json())
    for res in response.json()["results"]:
        print(f"{res['question_key']}:{res['check_tag_intention']}-{res['check_tag_answer']}")
    print("#############")