import re

SCORE_CONTEXT_PATTERNS = [
    r"分数", r"得分", r"评分", r"打分", r"几分", r"多少分",
    r"(\d+(\.\d+)?)\s*分",           # 直接出现“10分/4.5分”
    r"满分", r"分值", r"分/10", r"分/5", r"分/100"
]

def is_score_context(text: str) -> bool:
    """判断文本是否在谈评分/分数语境。"""
    if not isinstance(text, str):
        return False
    t = text.strip()

    # 命中任一评分语境关键词/结构即可
    for p in SCORE_CONTEXT_PATTERNS:
        if re.search(p, t):
            return True
    return False


def extract_score(text: str):
    """
    在确认是评分语境后，提取分数（优先提取带'分'的数字，其次提取首个数字）。
    返回字符串分数，如 '10' / '4.5' / '10-9'（区间可选）。
    若无法提取，返回原文本。
    """
    t = text.strip()

    # 1) 优先提取 “数字+分”
    m = re.search(r"(\d+(?:\.\d+)?)\s*分", t)
    if m:
        return f"{m.group(1)}分"

    # 2) 可选：处理区间 “9-10分 / 9~10分”
    m_range = re.search(r"(\d+(?:\.\d+)?)\s*[-~—]\s*(\d+(?:\.\d+)?)\s*分", t)
    if m_range:
        return f"{m_range.group(1)}-{m_range.group(2)}分"

    # 3) 兜底：评分语境下，提取首个数字
    m2 = re.search(r"(\d+(?:\.\d+)?)", t)
    if m2:
        return f"{m2.group(1)}分"

    return text


def postprocess_intention_keep_score_only(s):
    """
    仅当输出处于评分/分数语境时，抽取分数；否则原样返回。
    """
    if not isinstance(s, str):
        return s
    s = s.strip()

    if is_score_context(s):
        return extract_score(s)

    return s


def strip_quotes(s):
    if not isinstance(s, str):
        return s
    return s.strip().strip('"').strip("'").strip("“").strip("”")