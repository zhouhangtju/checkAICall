# checkAICall

通话质检服务：解析外呼机器人与客户对话，根据场景标签集调用大模型判断意图是否匹配，并输出质检结果。

## 功能概览

- FastAPI 接口：`/api/v1/check_call`、`/api/v1/health`、`/api/v1/scene_types`
- 对话解析：将通话文本按 Q 节点拆分为 AI/客户问答对
- 意图校验：根据场景的候选标签集调用 LLM 判断意图，输出“正确/不正确”
- 评分语境处理：在评分场景下提取分数输出

## 目录结构

- `app.py`：FastAPI 服务入口与核心逻辑
- `extractResultOutbound.py`：对话解析与机器人标签解析
- `llmServer.py`：LLM 请求封装（含服务地址与鉴权）
- `utils.py`：评分语境处理与文本清理
- `request_check_call.py`：单次请求示例脚本
- `test/test-curl.py`：批量请求示例（读 Excel）
- `locust-test.py`：Locust 压测脚本
- `data/`：通话记录样例数据（Excel）

## 环境准备

```bash
pip install -r requirements.txt
```

## 启动服务

```bash
python app.py
```

默认监听：`http://0.0.0.0:8000`

## 接口说明

### POST `/api/v1/check_call`

请求体：

```json
{
  "robot_tag": "Q1:接通,Q3:满意,Q5:测速已确认",
  "call_text": "AI：0.1秒\nQ1:...",
  "scene_type": "装机单竣工"
}
```

响应示例：

```json
{
  "status_code": "200",
  "message": "质检完成",
  "results": [
    {
      "question_key": "Q1",
      "dialogue_json": [
        {"AI": "...", "客户": "..."}
      ],
      "dialogue_text": "...",
      "ai_tag": "接通",
      "check_tag_intention": "接通",
      "check_tag_answer": "正确"
    }
  ],
  "total_checks": 1
}
```

### GET `/api/v1/health`

健康检查。

### GET `/api/v1/scene_types`

返回支持的场景类型列表。

## 调用示例

### Python 单次调用

```bash
python request_check_call.py
```

### 批量调用（Excel）

```bash
python test/test-curl.py
```

### 压测

```bash
locust -f locust-test.py
```

## 重要说明

- `llmServer.py` 内包含模型服务地址和鉴权信息，运行前请根据实际环境修改。
- `scene_type` 必须是系统支持的场景类型，否则返回 400。
- `call_text` 会自动去除 `_x000D_`。

## 开发提示

- 如需新增场景标签，更新 `app.py` 中的 `ALL_TAGS`。
- 对话解析规则在 `extractResultOutbound.py` 中，可按实际文本格式调整。
