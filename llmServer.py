import time
import jwt
import requests
import json


def generate_token(apikey: str, exp_seconds: int):
    try:
        id, secret = apikey.split(".")
    except Exception as e:
        raise Exception("invalid apikey", e)

    payload = {
        "api_key": id,
        "exp": int(round(time.time())) + exp_seconds,
        "timestamp": int(round(time.time())),
    }

    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "typ": "JWT", "sign_type": "SIGN"},
    )


apiKey = "67d91bfe360b95266c69c102./tmvYt75PO60rqYcmMBDTJoAuMs567/J"
token = generate_token(apiKey, 86400)
token = "sk-a2b25448-f74f-4c2f-a855-aed8e4251d01"


# MODEL_SERVICE_URL = "http://188.103.147.179:30181/largemodel/api/v2/completions"
MODEL_SERVICE_URL = "http://188.103.147.179:30175/gateway/api/bMWPmH"

# 模型服务认证令牌
AUTH_TOKEN = token

# headers = {
#     "Content-Type": "application/json",
#     "Authorization": f"Bearer {AUTH_TOKEN}"
# }

headers = {
    "Content-Type": "application/json",
    "Authorization-Gateway": "sk-a2b25448-f74f-4c2f-a855-aed8e4251d01"
}
print(AUTH_TOKEN)

def llm_api(payload):
    json_request = {
        "model":"Qwen2-72B-Instruct",
        "messages": [
            {"role": "user", "content":payload}
        ],
        "stream":False
    }

    response = requests.post(MODEL_SERVICE_URL, headers=headers, data=json.dumps(json_request))
    return response

# curl -X POST http://188.103.147.179:30181/largemodel/api/v2/completions \
# -H "Content-Type: application/json" \
# -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInNpZ25fdHlwZSI6IlNJR04iLCJ0eXAiOiJKV1QifQ.eyJhcGlfa2V5IjoiNjdkOTFiZmUzNjBiOTUyNjZjNjljMTAyIiwiZXhwIjoxNzU2OTUyODI2LCJ0aW1lc3RhbXAiOjE3NTY4NjY0MjZ9.AubGYH2mSRxQ_aO1bLoUisIcsuGt-6uegkpqy4MlkGk" \
# -d '{
# "model": "qwen-72b",
# "prompt": "北京今天天气如何？",
# "temperature":0.1,
# "top_p":0.1,
# "history":[],
# "appId":"67d918af74f68c28fdd333b0",
# "stream":false }'