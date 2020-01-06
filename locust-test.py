from locust import HttpUser, task, tag, between
import pandas as pd
import random

df = pd.read_excel("./data/装机单竣工回访_通话记录1022.xlsx")
df_temp = df[~pd.isnull(df["机器人标签"])]


# df_temp.index = range(0, len(df_temp))
df_temp = df_temp.reset_index(drop=True)


class ChatUser(HttpUser):

    wait_time = between(1, 3)


    @task
    @tag('check_call')
    def test_check_call(self):
        header = {"Content-Type": "application/json"}
        rowNumber = random.randint(0,60)
        json_request = {
            "robot_tag": df_temp.loc[rowNumber]["机器人标签"],
            "call_text": df_temp.loc[rowNumber]["通话文本"],
            }
        response = self.client.post("/api/v1/check_call", json=json_request, headers=header)
        print(response.json())


print("#####")