import pandas as pd

file_path = "/Users/hzhou/dev-projects/checkAICall/data/分场景标签明细.xlsx"

# 读取所有 sheet，返回一个 {sheet_name: DataFrame} 的字典
sheets = pd.read_excel(file_path, sheet_name=None)

allSheetsTags = {}  # 最终结果：{sheet_name: {tag_key: [tag_values]}}

for sheet_name, df in sheets.items():
    sheetTags = {}
    for tag in df["标签名称(必填)"].dropna():  # 防止有空行
        parts = tag.split(":")
        if len(parts) > 1:
            sheetTags.setdefault(parts[0], []).append(parts[1])
    allSheetsTags[sheet_name] = sheetTags

# 打印结构
print(allSheetsTags)