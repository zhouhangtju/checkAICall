'''
将结果解析成下述格式
[
    {
        "Q":"Qx",
        "dialogue":[
            {
                "AI":"xx","客户":"xx"
            },
            {
                "AI":"xx","客户":"xx"
            }
        ]
    }
]
'''


import pandas as pd
import re
import json


import re

DEFAULT_PROMPT = {"不好意思，我没有听清，请您再详细说明一下?","不好意思，我没有听清，能否请您再详细说明一下?"}

def annotate_default_prompt(text: str, default_prompt: set = DEFAULT_PROMPT) -> str:
    """
    在解析前给默认兜底话术补充节点标识：{last_q}-default
    规则：
      - last_q 来自最近出现的 Q 节点（Qx: 或 AI：Qx: / AI：Qx-1: 等）
      - 只处理 AI 行
      - 如果 AI 行内容已经是 Qx...: 开头，则不重复标注
      - 如果 last_q 不存在，则原样返回
    """
    lines = text.splitlines()
    out = []
    last_q = None

    # 允许匹配 Q4、Q4-1、Q4-default 等“节点名”，但 last_q 只取 Q4 或 Q4-1 这种主节点（不带 -default）
    # q_line_pat = re.compile(r'^(Q\d+(?:-\d+)?):')                 # Q5:...
    # ai_q_pat = re.compile(r'^AI：\s*(Q\d+(?:-\d+)?)(?:-[^:]+)?:')  # AI：Q4:... 或 AI：Q4-1:... 或 AI：Q4-default:...
    # 修改正则：允许匹配 Q4、Q4-1、Q4-A 等形式
    # q_line_pat = re.compile(r'^(Q\d+(?:-[A-Z0-9]+)?):')                    
    # ai_q_pat = re.compile(r'^AI：\s*(Q\d+(?:-[A-Z0-9]+)?)(?:-[^:]+)?:')

    q_line_pat = re.compile(r'^(Q\d+(?:-(?:[A-Z]|\d+|满分|非满分))*):')
    ai_q_pat = re.compile(r'^AI：\s*(Q\d+(?:-(?:[A-Z]|\d+|满分|非满分))*)(?:-[^:]+)?:')

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        # 1) 若是 Qx: 行，更新 last_q
        m1 = q_line_pat.match(line)
        if m1:
            last_q = m1.group(1)
            out.append(raw)  # 保留原始行（含缩进/格式）
            continue

        # 2) 若是 AI：Qx...: 行，更新 last_q（取 Qx 或 Qx-1）
        m2 = ai_q_pat.match(line)
        if m2:
            last_q = m2.group(1)
            out.append(raw)
            continue

        # 3) 处理 AI：默认兜底话术，且该 AI 行没有自带 Q 前缀时补标
        if line.startswith("AI："):
            content = line[len("AI："):].strip()

            # 已经带 Q 节点前缀就不动（例如 AI：Q4-default:...）
            if re.match(r'^(Q\d+(?:-\d+)?):', content) or re.match(r'^(Q\d+(?:-\d+)?)-default:', content) or re.match(r'^Q\d+(?:-[A-Z0-9]+)*(?:-default)?:', content) or re.match(r'^(Q\d+(?:-(?:[A-Z]|\d+|满分|非满分))*):', content) or re.match(r'^(Q\d+(?:-(?:[A-Z]|\d+|满分|非满分))*)-default:', content):
                out.append(raw)
                continue

            # 命中默认话术才补
            if content in default_prompt and last_q:
                out.append(f"AI：{last_q}-default:{content}")
                continue

        out.append(raw)

    return "\n".join(out)


def parse_dialog_clean(text):
    lines = text.splitlines()
    result = []
    current_q = None    #标识最新的是Q几
    dialogue_pairs = [] #这里装的是外呼系统AI和客户的一个问答对
    buffer_ai = None   #放AI的话，buffer
    buffer_cust = []  #放客户的话，buffer
    Q_PATTERN = r'(Q\d+(?:-[A-Za-z0-9_]+)*)'
    Q_PATTERN = r'(Q\d+(?:-(?:\d+|default|满分|非满分|[A-Za-z0-9_]+))*)'

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 匹配 Qx 匹配Qx的时候才开始更新dialogue_pairs
        # q_match = re.match(r'^Q\d+:', line)
        q_match = re.match(rf'^{Q_PATTERN}:', line)
        if q_match:
            # 保存上一个 Q
            if current_q and buffer_ai is not None:
                # 把客户内容合并成一句
                dialogue_pairs.append({"AI": buffer_ai, "客户": " ".join(buffer_cust)})
            if current_q:
                result.append({"Q": current_q, "dialogue": dialogue_pairs})
            current_q = q_match.group().rstrip(':')
            dialogue_pairs = []
            buffer_ai = line[q_match.end():].strip()
            buffer_cust = []
            continue

        # 匹配 AI（忽略时间标记，例如 AI：0.1秒）
        
        ai_match = re.match(r'^AI：', line)
        if ai_match:

            content = line[ai_match.end():].strip()


            # ⭐ 关键修复：AI：Qx: 形式的 Q
            # q_in_ai = re.match(r'^(Q\d+(?:-\d+)?):', content)
            q_in_ai = re.match(rf'^{Q_PATTERN}:', content)
            if q_in_ai:
                # 保存上一轮
                if current_q and buffer_ai is not None:
                    dialogue_pairs.append({
                        "AI": buffer_ai,
                        "客户": " ".join(buffer_cust)
                    })
                if current_q:
                    result.append({
                        "Q": current_q,
                        "dialogue": dialogue_pairs
                    })

                current_q = q_in_ai.group(1)
                dialogue_pairs = []
                buffer_ai = content[q_in_ai.end():].strip()
                buffer_cust = []
                continue



            
            # 如果内容只是时间或数字，忽略
            if not re.match(r'^\d+(\.\d+)?秒$', content):
                # 保存上一个 AI 对话
                if buffer_ai is not None:
                    dialogue_pairs.append({"AI": buffer_ai, "客户": " ".join(buffer_cust)})
                buffer_ai = content
                buffer_cust = []
            continue

        # 匹配客户
        cust_match = re.match(r'^客户：', line)
        if cust_match:
            customer_text = line[cust_match.end():].strip()
            buffer_cust.append(customer_text)
            continue

    # 保存最后一个 Q
    if current_q and buffer_ai is not None:
        dialogue_pairs.append({"AI": buffer_ai, "客户": " ".join(buffer_cust)})
    if current_q:
        result.append({"Q": current_q, "dialogue": dialogue_pairs})

    return result

def parseAITag(text):
    '''
      解析AI Tag
    '''
    result = {}
    for tag in  text.split(","):
        try:
            result[f"{tag.split(':')[0]}"] = tag.split(":")[1]
        except:
            continue
    return result


if __name__ == "__main__":
    df = pd.read_excel("./data/装机单竣工回访_通话记录1022.xlsx")
    df = df.replace("_x000D_", "", regex=True)
    text = df.loc[11,"通话文本"]
    print(text)
#     dialog_str = """AI：0.1秒
# Q1:很高兴您能接听我的电话，我是浙江移动宽带服务专员，您最近安装了移动宽带，我们想对本次装维服务简单回访几个问题，您看方便吗?
# 客户：你说什么，你到屋里好就方便。
# AI：0.1秒
# Q3:您对本次装维服务整体上是否满意？
# 客户：你处理好了，美女。
# 客户：满意。
# AI：0.1秒
# Q5:已经记录，那师傅在装机完成时有没有为您进行宽带测速，并将结果展示给您确认？
# 客户：啊。
# AI：Q5-default:不好意思，我没有听清，请您再详细说明一下?
# 客户：我老生活总是第一性的，这次收拿移动工资的。
# AI：0.1秒
# Q6:最后一个问题，师傅是否有告知您后续收到满意度测评时请打10分满意？
# 客户：那面有。
# 客户：有。
# AI：0.1秒
# Q7:好的，感谢您参与本次调研，敬请您在后续的满意度调研中给予10分好评，祝您生活愉快再见！"""

#     dialog_str = '''AI：0.1秒
# Q1:很高兴您能接听我的电话，我是浙江移动宽带服务专员，您最近安装了移动宽带，我们想对本次装维服务简单回访几个问题，您看方便吗?
# 客户：你说。
# AI：0.1秒
# Q3:您对本次装维服务整体上是否满意？
# 客户：一般。
# AI：Q4:很抱歉带来不好的体验，方便告知您不满意的原因是？
# 客户：都不太满意。
# AI：Q4-default:不好意思，我没有听清，请您再详细说明一下?
# 客户：网络不太行。
# AI：Q4-1:非常抱歉给您带来不好的体验了，是否需要升级安排属地网格长上门处理呢？如您需要安排，请直接说“需要”。
# 客户：你安排吧。
# AI：0.1
# Q5:已经记录，那师傅在装机完成时有没有为您进行宽带测速，并将结果展示给您确认？
# 客户：有展示。
# AI：0.1秒
# Q6:最后一个问题，师傅是否有告知您后续收到满意度测评时请打10分满意？
# 客户：什么满意。
# AI：0.1秒
# Q7:好的，感谢您参与本次调研，敬请您在后续的满意度调研中给予10分好评，祝您生活愉快再见！
# '''

#     dialog_str = '''AI：0.1秒
# Q1:很高兴您能接听我的电话，我是浙江移动宽带服务专员，您最近安装了移动宽带，我们想对本次装维服务简单回访几个问题，您看方便吗?
# 客户：行啊。
# AI：0.1秒
# Q3:您对本次装维服务整体上是否满意？
# 客户：不满意啊。
# AI：Q4:很抱歉带来不好的体验，方便告知您不满意的原因是？
# 客户：师傅来帮我装宽带装的不太好啊，我对宽带不满意。
# AI：Q4-1:非常抱歉给您带来不好的体验了，是否需要升级安排属地网格长上门处理呢？如您需要安排，请直接说“需要”。
# 客户：哦，那你帮我安排吧，应该要吧。
# AI：Q5:已经记录，那师傅在装机完成时有没有为您进行宽带测速，并将结果展示给您确认？
# 客户：那，这个不是很记得了，我记得应该是有的吧。
# AI：0.1秒
# Q6:最后一个问题，师傅是否有告知您后续收到满意度测评时请打10分满意？
# 客户：这个他没跟我说啊，不过我会给他打十分满意的。
# AI：0.1秒
# Q7:好的，感谢您参与本次调研，敬请您在后续的满意度调研中给予10分好评，祝您生活愉快再见！
# '''
    dialog_str = '''AI：Q1:您好，我是浙江移动宽带服务专员，现在浙江移动推出免费网络体检活动，工作人员会根据您方便时间上门，如果您需要专业人员上门处理，可以直接跟我说需要
客户：你在吗？
AI：不好意思，我没有听清，能否请您再详细说明一下?
客户：免费吗？你说亏带什么免费吧。
AI：0.1秒
Q2:请问您什么时间方便呀，我帮您做个登记，具体上门时间以装维与您预约时间为准。
客户：你好像不是中国人啊。
AI：不好意思，我没有听清，能否请您再详细说明一下?
客户：啊，我讲的话你听。
客户：我问你，你打这个电话什么意思？
AI：不好意思，我没有听清，能否请您再详细说明一下?
客户：操你妈逼。
AI：打扰了，下次如有满意度调研，请帮忙都打十分！祝您生活愉快，再见！
0.1秒
'''
    dialog_str = '''AI：0.1秒
Q1:很高兴您能接听我的电话，我是浙江移动宽带服务专员，您最近安装了移动宽带，我们想对本次装维服务简单回访几个问题，您看方便吗?
客户：你是i吗？
AI：不好意思，我没有听清，请您再详细说明一下?
客户：你是ai吗？
AI：Q1-C:噢是这样的，我是基于人工智能技术的智能客服，虽然没有实体，但和真人一样全身心为您服务，邀请您回答几个简单的问题可以吗？
客户：你说吧。
AI：0.1秒
Q3:您对本次装维服务整体上是否满意？
客户：你说什么什么装位服务？
AI：不好意思，我没有听清，请您再详细说明一下?
客户：满意的不知道啊，让他满意的满意的。
AI：0.1秒
Q5:已经记录，那师傅在装机完成时有没有为您进行宽带测速，并将结果展示给您确认？
客户：嗯。
客户：应该有确认吧。
AI：0.1秒
Q6:最后一个问题，师傅是否有告知您后续收到满意度测评时请打10分满意？
客户：啊，十分满意十分满意。
AI：0.1秒
Q7:好的，感谢您参与本次调研，敬请您在后续的满意度调研中给予10分好评，祝您生活愉快再见！
'''
#     dialog_str = '''AI：0.1秒
# Q1:很高兴您能接听我的电话，我是浙江移动宽带服务专员，您最近安装了移动宽带，我们想对本次装维服务简单回访几个问题，您看方便吗?
# 客户：你是哪里呀？我没听清。
# AI：Q1-A:噢是这样的，我是浙江移动宽带服务专员，您刚安装完我们移动宽带，想简单的回访几个问题，耽误您几分钟，好吗？
# 客户：嗯。
# AI：0.1秒
# Q3:您对本次装维服务整体上是否满意？
# 客户：哦，你说吧。
# 客户：还可以。
# AI：0.1秒
# Q5:已经记录，那师傅在装机完成时有没有为您进行宽带测速，并将结果展示给您确认？
# 客户：嗯，有的有的。
# AI：0.1秒
# Q6:最后一个问题，师傅是否有告知您后续收到满意度测评时请打10分满意？
# 客户：啊没听懂。
# AI：Q6-A:装机完成后，师傅是否说过让你接到电话或者短信给他打10分？
# 客户：哦，这个跟我讲了。
# AI：不好意思，我没有听清，请您再详细说明一下?
# 客户：和我讲过了。
# AI：0.1秒
# Q7:好的，感谢您参与本次调研，敬请您在后续的满意度调研中给予10分好评，祝您生活愉快再见！
# '''
#     dialog_str = '''AI：Q1:很高兴您能接听我的电话，我是浙江移动宽带服务专员，您最近报修了宽带故障，我们想对本次装维服务简单回访几个问题，您看方便吗?
# 客户：지说.
# AI：不好意思，我没有听清，请您再详细说明一下?
# 客户：行啊，你说。
# AI：0.1秒
# 0.1秒
# Q3:近期您反馈的故障我们装维是否上门处理过？
# 客户：有来过吧。
# AI：0.1秒
# Q5:好的，师傅是否有告知您后续收到满意度评价时请打10分满意？
# 客户：有跟我讲过。
# AI：0.1秒
# Q6:好的，师傅处理后家里移动宽带使用感觉怎么样？1 到 10 分之间，10 分是满意，1 分是不满意，1-10分请给我一个具体的分数喔~
# 客户：两分吧。
# AI：0.1秒
# Q7:嗯登记了~那您觉得宽带安装或维修服务怎么样？10 分代表满意，1 分代表不满意，1-10分请给我一个具体的分数喔~
# 客户：三分。
# AI：0.1秒
# Q8:那您评价低分的原因是什么？
# 客户：你这个网络啊质量不好。
# AI：0.1秒
# Q9:好的，那您觉得我们移动宽带可以在哪些方面有所改进呢？
# 客户：网络速度帮我提快一点，还有那个资费可以降低一点。
# AI：Q10:非常抱歉，对您造成不便了，如您需要人员再次安排上门处理，请直接说“需要”。
# 客户：你帮我安排吧。
# AI：好的，感谢您参与本次调研，敬请您在后续的满意度调研中给予10分好评，祝您生活愉快再见！
# '''
    dialog_str = '''AI：Q1:很高兴您能接听我的电话，我是浙江移动宽带服务专员，您最近报修了宽带故障，我们想对本次装维服务简单回访几个问题，您看方便吗?
客户：지说.
AI：不好意思，我没有听清，请您再详细说明一下?
客户：行啊，你说。
AI：0.1秒
0.1秒
Q3:近期您反馈的故障我们装维是否上门处理过？
客户：有来过吧。
AI：0.1秒
Q5:好的，师傅是否有告知您后续收到满意度评价时请打10分满意？
客户：有跟我讲过。
AI：0.1秒
Q6:好的，师傅处理后家里移动宽带使用感觉怎么样？1 到 10 分之间，10 分是满意，1 分是不满意，1-10分请给我一个具体的分数喔~
客户：两分吧。
AI：0.1秒
Q7-非满分:嗯登记了~那您觉得宽带安装或维修服务怎么样？10 分代表满意，1 分代表不满意，1-10分请给我一个具体的分数喔~
客户：三分。
AI：不好意思，我没有听清，请您再详细说明一下?
客户：三分。
AI：0.1秒
Q8:那您评价低分的原因是什么？
客户：你这个网络啊质量不好。
AI：0.1秒
Q9:好的，那您觉得我们移动宽带可以在哪些方面有所改进呢？
客户：网络速度帮我提快一点，还有那个资费可以降低一点。
AI：Q10:非常抱歉，对您造成不便了，如您需要人员再次安排上门处理，请直接说“需要”。
客户：你帮我安排吧。
AI：好的，感谢您参与本次调研，敬请您在后续的满意度调研中给予10分好评，祝您生活愉快再见！'''
    dialog_str = annotate_default_prompt(dialog_str)

    print("-----annotate_default_prompt后的内容------" + dialog_str)
    parsed = parse_dialog_clean(dialog_str)
    print("-----parse_dialog_clean后的内容------")
    print(json.dumps(parsed, ensure_ascii=False, indent=2))
    ai_tag = parseAITag("Q1-default:质差需上门,用户厌恶，骂脏话")
    print(ai_tag)

    # print(json.dumps(parsed, ensure_ascii=False, indent=2))



