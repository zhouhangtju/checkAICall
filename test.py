import pandas as pd
import json
from extractResultOutbound import parse_dialog_clean,parseAITag,annotate_default_prompt
from llmServer import llm_api
from app import ALL_TAGS
import re


PROMPT_INTENTION = '''
    已知外呼系统和用户的对话为{},
    用户的待选意图为{},
    请问用户的真实意图是啥，只需回答待选意图{}中的某种，不需要其他内容
'''

PROMPT_ANSWER = '''
    已知外呼系统和用户的对话为{},待选意图为{},外呼系统识别的意图为{},
    请问外呼系统识别的意图是否正确，只需回答正确还是不正确，不需要其他内容
'''
df = pd.read_excel("./data/装机单竣工回访_通话记录1022.xlsx")
# df = pd.read_excel("/Users/hzhou/dev-projects/checkAICall/data/通话记录.xlsx")
# df = pd.read_excel("./data/质差派单.xlsx")

df = df.replace("_x000D_", "", regex=True)



# text = df.loc[0,"通话文本"]
# print(text)
check_res = []
for i,row in df.iterrows():
    check_list = []

    if pd.isnull(row["机器人标签"]):
        continue

    annotated_dialog = annotate_default_prompt(row["通话文本"])
    dialog = parse_dialog_clean(annotated_dialog)
    ai_tag = parseAITag(row["机器人标签"])
    # print(dialog)
    # for key, value in ai_tag.items():
    data = {}
    for key, tag in ai_tag.items():
        for item in dialog:
            data = {}
            if item['Q'] == key:   # 可以改成模糊匹配 if key in item['Q']
                data[key] = {
                "text": item['dialogue'],
                "ai_tag": tag,
                "check_tag_intention": "",
                "check_tag_answer":""
            }
                response_intention = llm_api(PROMPT_INTENTION.format(json.dumps(item['dialogue'], ensure_ascii=False), json.dumps(ALL_TAGS["装机单竣工"][key], ensure_ascii=False),json.dumps(ALL_TAGS["装机单竣工"][key], ensure_ascii=False)))  
                response_answer = llm_api(PROMPT_ANSWER.format(json.dumps(item['dialogue'], ensure_ascii=False),json.dumps(ALL_TAGS["装机单竣工"][key], ensure_ascii=False),tag))
                # data[key]["check_tag_intention"] = response_intention.json()["choices"][0]["text"]
                data[key]["check_tag_intention"] = response_intention.json()["choices"][0]["message"]["content"]
                # data[key]["check_tag_answer"] = response_answer.json()["choices"][0]["text"]
                data[key]["check_tag_answer"] = response_answer.json()["choices"][0]["message"]["content"]

            
                if re.search(r"(?<!不)(?<!没)(正确|对|符合|是)",data[key]["check_tag_answer"]):
                    data[key]["check_tag_answer"] = "正确"
                elif re.search(r"不正确|不对|不符合|错误|不是",data[key]["check_tag_answer"]):
                    data[key]["check_tag_answer"] = "不正确"
                else:
                    data[key]["check_tag_answer"] = "不确定"
                check_res.append(data)
                check_list.append(f'''{key}: {data[key]["check_tag_intention"]}-{data[key]["check_tag_answer"]}''')

        # print(data)
    print(check_list)
    df.at[i, "aiCheckRes"] = "; ".join(check_list)
    # print(dialog)
    # print(ai_tag)
    # print(df.at[i, "aiCheckRes"])
    # print(check_res)
    # break

df.to_excel("./data/装机单竣工-check.xlsx")