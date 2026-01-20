import json
import textwrap
import requests


def main() -> None:
    url = "http://localhost:8000/api/v1/check_call"
    payload = {
        "robot_tag": "Q1:接通,Q3:满意,Q5:测速已确认",
        "call_text": textwrap.dedent(
            """\
            AI：0.1秒
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
            """
        ).strip(),
        "scene_type": "装机单竣工",
    }

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()

    try:
        data = response.json()
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except ValueError:
        print(response.text)


if __name__ == "__main__":
    main()
