from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import re
from extractResultOutbound import parse_dialog_clean, parseAITag
from llmServer import llm_api
from utils import postprocess_intention_keep_score_only,strip_quotes

app = FastAPI(title="通话质检服务", version="1.0.0")


# 常量定义
ALL_TAGS = {'装机单竣工': {'Q1-B': ['接通', '接通未评价'],
           'Q1-A-default': ['接通', '接通未评价'],
           'Q1-C': ['接通', '接通未评价'],
           'Q1-B-default': ['接通', '接通未评价'],
           'Q1': ['接通', '接通未评价'],
           'Q1-C-default': ['接通未评价', '接通'],
           'Q1-A': ['接通', '接通未评价'],
           'Q1-default': ['接通', '接通未评价'],
           'Q3-A': ['不满意', '满意'],
           'Q3-A-default': ['满意', '不满意'],
           'Q3-default': ['接通未评价', '不满意', '满意'],
           'Q3': ['接通未评价', '不满意', '满意'],
           'Q4-default': ['上网质量问题', '非家庭网络类问题', '服务不及时', '装维服务不规范', '客户评价标准与移动不一致', '接通未评价'],
           'Q4': ['服务不及时', '接通未评价', '客户评价标准与移动不一致', '非家庭网络类问题', '装维服务不规范', '上网质量问题'],
           'Q4-1': ['接通未评价', '质差需上门', '质差无需上门'],
           'Q5-A': ['测速已确认', '测速未确认'],
           'Q5-A-default': ['接通未评价', '测速已确认', '测速未确认'],
           'Q5-default': ['接通未评价', '测速未确认', '测速已确认'],
           'Q5': ['接通未评价', '测速未确认', '测速已确认'],
           'Q6-A': ['已邀评', '未邀评'],
           'Q6-default': ['接通未评价', '邀评', '未邀评'],
           'Q6-A-default': ['未邀评', '接通未评价', '邀评'],
           'Q6': ['未邀评', '邀评']},
 '质差修复已上门（质差回访）': {'Q1-B': ['接通未评价', '接通'],
                   'Q1-A-default': ['接通', '接通未评价'],
                   'Q1-B-default': ['接通', '接通未评价'],
                   'Q1-C': ['接通', '接通未评价'],
                   'Q1-C-default': ['接通', '接通未评价'],
                   'Q1-A': ['接通未评价', '接通'],
                   'Q1-default': ['接通', '接通未评价'],
                   'Q1': ['接通', '接通未评价'],
                   'Q3-A-default': ['接通未评价', '未修复', '已修复'],
                   'Q3-A': ['质差无需上门', '已修复', '未修复'],
                   'Q3-default': ['未修复', '已修复', '接通未评价', '接通未评价', '质差无需上门'],
                   'Q3': ['质差无需上门', '未修复', '已修复', '接通未评价'],
                   'Q4-C-default': ['10分', '9分', '9'],
                   'Q4-C': ['10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
                   'Q4-A-default': ['9分', '8分', '10分', '5分', '2分', '6分', '1分', '7分', '4分', '3分', '1'],
                   'Q4-default': ['9分', '5分', '1分', '10分', '4分', '8分', '2分', '7分', '6分', '3分'],
                   'Q4-B': ['10分', '5分', '410分', '3分', '6分', '9分', '1分', '2分', '8分', '7分', '4分'],
                   'Q4-A': ['6分', '10分', '3分', '9分', '4分', '2分', '1分'],
                   'Q4': ['接通未评价', '1分', '6分', '3分', '4分', '5分', '10分', '9分', '8分', '7分', '2分'],
                   'Q5-满分': ['接通未评价'],
                   'Q5-非满分': ['接通未评价', '10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
                   'Q5-B-default': ['接通未评价', '10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
                   'Q5-B': ['接通未评价', '10分', '4分', '9分', '8分', '7分', '6分', '5分', '3分', '2分', '1分'],
                   'Q5-A-default': ['接通未评价', '10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
                   'Q5-A': ['接通未评价', '10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
                   'Q5-C-满分-default': ['接通未评价', '10分', '9分'],
                   'Q5-C-满分': ['接通未评价', '10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
                   'Q5-满分-default': ['10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分', '接通未评价'],
                   'Q4-B-default': ['5'],
                   'Q5-非满分-default': ['10分', '9分', '6分', '5分', '4分', '3分', '2分', '1分', '接通未评价'],
                   'Q5': ['3分', '1分', '5分', '7分', '9分', '10分', '6分', '2分', '4分', '8分'],
                   'Q6': ['接通未评价', '非家庭网络类问题', '装维服务不及时', '装维服务不规范', '上网质量问题', '质差未处理报结', '接通未评价客户'],
                   'Q6-A': ['满意', '接通未评价'],
                   'Q7': ['接通未评价', '质差需上门'],
                   'Q7-B-default': ['接通未评价', '质差无需上门', '质差需上门'],
                   'Q7-B': ['接通未评价', '质差无需上门', '质差需上门'],
                   'Q7-A': ['接通未评价', '质差无需上门', '质差需上门'],
                   'Q7-default': ['质差无需上门', '质差需上门']},
 '投诉单报结': {'Q1': ['接通', '接通未评价'],
           'Q1-A': ['接通', '接通未评价'],
           'Q1-A-default': ['接通', '接通未评价'],
           'Q1-B': ['接通', '接通未评价'],
           'Q1-B-default': ['接通未评价'],
           'Q1-C': ['接通', '接通未评价'],
           'Q1-C-default': ['接通未评价', '接通'],
           'Q1-default': ['接通', '接通未评价'],
           'Q3': ['已上门', '未上门', '接通未评价'],
           'Q3-A-default': ['已上门', '未上门', '接通未评价'],
           'Q3-A': ['接通未评价', '未上门', '已上门'],
           'Q3-default': ['未上门', '接通未评价', '上门'],
           'Q4-default': ['接通未评价', '意向上门', '未意向上门'],
           'Q4-A-default': ['意向上门', '未意向上门', '接通未评价'],
           'Q4-A': ['接通未评价', '未意向上门', '意向上门'],
           'Q4': ['接通未评价客户', '意向上门', '未意向上门'],
           'Q5-A-default': ['邀评', '未邀评', '接通未评价'],
           'Q5-A': ['接通未评价', '未邀评', '邀评'],
           'Q5-default': ['邀评', '未邀评', '接通未评价客户'],
           'Q5': ['邀评', '接通未评价', '未邀评'],
           'Q6': ['4分', '6分', '接通未评价', '10分', '9分', '1分', '5分', '8分', '3分', '7分', '2分'],
           'Q6-A': ['5分', '1分', '6分', '3分', '4分', '2分', '9分', '8分', '7分', '10分'],
           'Q6-A-default': ['10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
           'Q6-B': ['3分', '2分', '7分', '8分', '9分', '1分', '6分', '4分', '10分'],
           'Q6-B-default': ['1分', '2分', '3分', '4分', '5分', '6分', '7分', '8分', '9分', '10分'],
           'Q6-C': ['5分', '3分', '6分', '10分', '1分', '7分', '2分', '9分', '8分', '4分'],
           'Q6-C-default': ['10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
           'A6-D': ['5分'],
           'Q6-D': ['7分', '1分', '4分', '8分', '9分', '6分', '10分', '3分', '2分'],
           'Q6-D-default': ['10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
           'Q6-default': ['10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分', '接通未评价'],
           'Q7-A': ['7分', '10分', '9分', '4分', '2分', '8分', '6分', '5分', '1分', '3分'],
           'Q7-A-default': ['10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
           'Q7-B': ['5分', '1分', '6分', '10分', '9分', '8分', '4分', '3分', '2分', '7分'],
           'Q7-B-default': ['10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
           'Q7-C-非满分': ['10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
           'Q7-C-非满分-default': ['10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
           'Q7-C-满分': ['7分', '2分', '8分', '9分', '6分', '10分', '4分', '5分', '1分', '3分'],
           'Q7-C-满分-default': ['10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
           'Q7-非满分': ['10分', '8分', '接通未评价', '9分', '6分', '5分', '7分'],
           'Q7-非满分-default': ['接通未评价', '10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分'],
           'Q7-满分': ['5分', '1分', '4分', '3分', '6分', '7分', '接通未评价', '10分', '2分', '9分', '8分'],
           'Q7-满分-default': ['10分', '9分', '8分', '7分', '6分', '5分', '4分', '3分', '2分', '1分', '接通未评价'],
           'Q8': ['非家庭网络类问题', '装维服务不及时', '装维服务不规范', '上网质量问题', '接通未评价', '用户不是不满意'],
           'Q8-1': ['投诉产生新问题', '投诉未解决'],
           'Q9-非满分': ['缩短故障响应/处理时间', '提升装维技术水平', '提升装维服务态度', '其他建议', '没有建议', '优化网络稳定性', '多项方面需改进'],
           'Q9-满分': ['没有建议', '其他建议', '多项方面需改进', '优化网络稳定性', '提升装维服务态度', '提升装维技术水平', '缩短故障响应/处理时间', '接通未评价'],
           'Q10': ['需上门', '投诉需处理', '接通未评价', '投诉需上门', '投诉无需上门', '修不好', '上门没空'],
           'Q10-A': ['投诉无需上门', '投诉需处理', '投诉需上门', '接通未评价'],
           'Q10-B': ['投诉无需上门', '投诉需处理', '投诉需上门'],
           'Q10-B-default': ['投诉无需上门', '投诉需处理', '投诉需上门', '接通未评价']},
 '质差派单': {'Q1': ['接通未评价', '质差无需上门', '质差需上门'],
          'Q1-default': ['接通未评价', '质差无需上门', '质差需上门'],
          'Q1-A': ['接通未评价', '质差无需上门', '质差需上门'],
          'Q1-A-default': ['接通未评价', '质差无需上门', '质差需上门'],
          'Q1-B': ['接通未评价', '质差无需上门', '质差需上门'],
          'Q1-B-default': ['接通未评价', '质差无需上门', '质差需上门'],
          'Q2': ['质差无需上门', '抓取时间关键字', '接通未评价'],
          'Q2-default': ['质差无需上门', '抓取时间关键字', '接通未评价']},
 '存量维系': {'Q1': ['接通未评价', '接通未评价', '接通', '接通未评价', '接通未评价', '接通未评价', '接通未评价'],
          'Q1-default': ['接通', '接通未评价', '接通未评价', '接通未评价', '接通未评价', '接通未评价'],
          'Q1-B': ['接通', '接通未评价', '接通未评价', '接通', '接通', '接通'],
          'Q1-F': ['接通', '接通未评价'],
          'Q1-A': ['接通', '接通未评价', '接通未评价'],
          'Q3-D-default': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q3-C-default': ['10', '9'],
          'Q3-C': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q3-B-default': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q3-B': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q3-A-default': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q3-A': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q3-default': ['接通未评价', '接通未评价', '10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q3': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q4-C-default': ['10', '9', '5'],
          'Q4-C': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q4-B-default': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q4-B': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q4-A-default': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q4-A': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q4': ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q4-default': ['接通后未评价', '10', '9', '8', '7', '6', '5', '4', '3', '2', '1'],
          'Q5': ['接通未评价', '非家庭网络类问题', '装维服务不规范', '接通', '装维服务不及时', '上网质量问题'],
          'Q5-A': ['不是不满意'],
          'Q7-B-default': ['存量无需上门', '存量需上门'],
          'Q7-B': ['质差无需上门', '存量需上门', '修不好'],
          'Q7-A': ['质差无需上门', '上门没空', '存量需上门'],
          'Q7': ['存量无需上门', '存量需上门'],
          'Q8': ['存量无需联系', '存量需联系']}}

PROMPT_INTENTION = '''
    已知外呼系统和用户的对话为{},
    用户的待选意图为{},（注意稽核Q1时，如果用户意图愿意接受问卷算接通，如果出现拒绝意图或者啥也没说算接通未评价）
    请问用户的真实意图是啥，只需回答待选意图{}中的某种,不需要其他多余内容
'''

PROMPT_ANSWER = '''
    已知外呼系统和用户的对话为{},待选意图为{},外呼系统识别的意图为{},
    请问外呼系统识别的意图是否正确，只需回答正确还是不正确，不需要其他内容
'''


class CallCheckRequest(BaseModel):
    """通话质检请求模型"""
    robot_tag: str  # 机器人标签
    call_text: str  # 通话文本
    scene_type: str = "装机单竣工"  # 场景类型，默认为装机单竣工
    
    class Config:
        json_schema_extra = {
            "example": {
                "robot_tag": "Q1:接通|Q3:满意",
                "call_text": "客服：您好，请问...\n客户：我很满意",
                "scene_type": "装机单竣工"
            }
        }


class CheckResult(BaseModel):
    """单个问题的检查结果"""
    question_key: str
    dialogue_json: List[dict]
    dialogue_text: str
    ai_tag: str
    check_tag_intention: str
    check_tag_answer: str


class CallCheckResponse(BaseModel):
    """通话质检响应模型"""
    status_code: str
    message: str
    results: List[CheckResult]
    total_checks: int


def process_check_answer(answer: str) -> str:
    """处理检查答案，标准化输出"""
    if re.search(r"(?<!不)(?<!没)(正确|对|符合|是)", answer):
        return "正确"
    elif re.search(r"不正确|不对|不符合|错误|不是", answer):
        return "不正确"
    else:
        return "不确定"




@app.post("/api/v1/check_call", response_model=CallCheckResponse)
async def check_call(request: CallCheckRequest):
    """
    通话质检接口
    
    - **robot_tag**: 机器人标签字符串
    - **call_text**: 通话文本内容
    - **scene_type**: 场景类型（默认：装机单竣工）
    """
    try:
        # 清理通话文本
        clean_text = request.call_text.replace("_x000D_", "")
        
        # 解析对话和AI标签
        dialog = parse_dialog_clean(clean_text)
        ai_tag = parseAITag(request.robot_tag)
        
        # 检查场景类型是否存在
        if request.scene_type not in ALL_TAGS:
            raise HTTPException(
                status_code=400, 
                detail=f"场景类型 '{request.scene_type}' 不存在"
            )
        
        check_results = []
        
        # 遍历AI标签进行检查
        for key, tag in ai_tag.items():
            # 检查key是否在当前场景的ALL_TAGS中
            if key not in ALL_TAGS[request.scene_type]:
                continue
                
            for item in dialog:
                # 匹配问题
                if item['Q'] in key:  # 可以改成模糊匹配: if key in item['Q']
                    # 获取待选意图
                    available_tags = ALL_TAGS[request.scene_type][key]
                    pre_dialog_str = ""
                    if "default" in item['Q']:
                        prev_node = item['Q'].split("-default")[0]
                        for dialog_item in dialog:
                            if dialog_item['Q'] == prev_node:
                                pre_dialog_str = json.dumps(dialog_item['dialogue'], ensure_ascii=False)
                                break

                    q1_complement_str = ""
                    if item["Q"]=="Q1" and len(dialog)>1 and "Q1-" in dialog[1]["Q"]:
                        q1_complement_str = json.dumps(dialog[1]['dialogue'], ensure_ascii=False)
                    
                    # 调用LLM检查意图
                    response_intention = llm_api(
                        PROMPT_INTENTION.format(
                            pre_dialog_str + json.dumps(item['dialogue'], ensure_ascii=False)+q1_complement_str,
                            json.dumps(available_tags, ensure_ascii=False),
                            json.dumps(available_tags, ensure_ascii=False)
                        )
                    )
                    
                    # 调用LLM检查答案
                    # response_answer = llm_api(
                    #     PROMPT_ANSWER.format(
                    #         json.dumps(item['dialogue'], ensure_ascii=False),
                    #         json.dumps(available_tags, ensure_ascii=False),
                    #         tag
                    #     )
                    # )
                    
                    # 提取结果
                    intention_result = response_intention.json()["choices"][0]["message"]["content"]
                    # answer_result = response_answer.json()["choices"][0]["message"]["content"]
                    
                    # 标准化答案
                    # processed_answer = process_check_answer(answer_result)
                    intention_result = strip_quotes(intention_result)
                    intention_result = postprocess_intention_keep_score_only(intention_result)

                    
                    if intention_result == tag:
                        processed_answer = "正确"
                    else:
                        processed_answer = "不正确"
                    # 添加检查结果
                    check_results.append(CheckResult(
                        question_key=key,
                        dialogue_json=item['dialogue'],
                        dialogue_text = pre_dialog_str + json.dumps(item['dialogue'], ensure_ascii=False)+q1_complement_str,
                        ai_tag=tag,
                        check_tag_intention=intention_result,
                        check_tag_answer=processed_answer
                    ))
        
        return CallCheckResponse(
            status_code="200",
            message="质检完成",
            results=check_results,
            total_checks=len(check_results)
        )
        
    except Exception as e:
        return CallCheckResponse(
            status_code="500",
            message=str(e),
            results=[],
            total_checks=0
        )


@app.get("/api/v1/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "通话质检服务"}


@app.get("/api/v1/scene_types")
async def get_scene_types():
    """获取所有可用的场景类型"""
    return {
        "scene_types": list(ALL_TAGS.keys()),
        "total": len(ALL_TAGS)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



'''
curl -X POST "http://localhost:8000/api/v1/check_call" \
  -H "Content-Type: application/json" \
  -d '{
    "robot_tag": "Q1:接通,Q3:满意,Q5:测速已确认",
    "call_text": "AI：0.1秒
Q1:很高兴您能接听我的电话，我是浙江移动宽带服务专员，您最近安装了移动宽带，我们想对本次装维服务简单回访几个问题，您看方便吗?_x000D_
客户：你说什么，你到屋里好就方便。_x000D_
AI：0.1秒
Q3:您对本次装维服务整体上是否满意？_x000D_
客户：你处理好了，美女。_x000D_
客户：满意。_x000D_
AI：0.1秒
Q5:已经记录，那师傅在装机完成时有没有为您进行宽带测速，并将结果展示给您确认？_x000D_
客户：啊。_x000D_
AI：不好意思，我没有听清，请您再详细说明一下?_x000D_
客户：我老生活总是第一性的，这次收拿移动工资的。_x000D_
AI：0.1秒
Q6:最后一个问题，师傅是否有告知您后续收到满意度测评时请打10分满意？_x000D_
客户：那面有。_x000D_
客户：有。_x000D_
AI：0.1秒
Q7:好的，感谢您参与本次调研，敬请您在后续的满意度调研中给予10分好评，祝您生活愉快再见！_x000D_
",
    "scene_type": "装机单竣工"
  }'
'''