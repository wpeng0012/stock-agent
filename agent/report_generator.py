import json
from datetime import datetime



with open(
    "../output/stock_report.json",
    "r",
    encoding="utf-8"
) as f:

    reports = json.load(f)



today = datetime.now().strftime(
    "%Y-%m-%d"
)



content = f"""
# A股短线投资观察日报

日期：{today}


"""


for item in reports:


    content += f"""

---

## {item["name"]}

代码：
{item["code"]}


量化评分：
{item["score"]}


AI分析：

{item["report"]}


"""



with open(
    f"../output/{today}_stock_report.md",
    "w",
    encoding="utf-8"
) as f:

    f.write(content)



print(
    "日报生成完成"
)