import os
import json


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)


input_file = os.path.join(
    OUTPUT_DIR,
    "agent_input.json"
)


with open(
    input_file,
    "r",
    encoding="utf-8"
) as f:
    data = json.load(f)



stocks = data["stocks"]


print(
    "股票数量:",
    len(stocks)
)



research_result = []


for stock in stocks[:10]:

    print(
        "正在搜索:",
        stock["name"]
    )


    # 这里保留你的搜索逻辑
    # 后续接 Tavily


    research_result.append(
        {
            "code":stock["code"],
            "name":stock["name"],
            "price":stock["price"],
            "score":stock["score"],
            "news":[]
        }
    )



output_file = os.path.join(
    OUTPUT_DIR,
    "stock_research.json"
)


with open(
    output_file,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        research_result,
        f,
        ensure_ascii=False,
        indent=2
    )


print(
    "研究结果生成:",
    output_file
)