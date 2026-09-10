import os
import json
import pandas as pd


# =========================
# 项目路径
# =========================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)


print(
    "项目目录:",
    BASE_DIR
)


# =========================
# 读取候选股票
# =========================


file = os.path.join(
    OUTPUT_DIR,
    "candidate_stock.csv"
)


df = pd.read_csv(
    file
)


print(
    "候选股票数量:",
    len(df)
)


# =========================
# 转Agent输入
# =========================


stocks = []


for _, row in df.iterrows():

    stocks.append(
        {
            "code": str(row["code"]),
            "name": row["name"],
            "price": float(row["close"]),
            "score": int(row["score"])
        }
    )


result = {
    "stocks": stocks
}



# =========================
# 保存
# =========================


output_file = os.path.join(
    OUTPUT_DIR,
    "agent_input.json"
)


with open(
    output_file,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        result,
        f,
        ensure_ascii=False,
        indent=2
    )


print(
    "Agent输入生成完成:",
    output_file
)


print(
    stocks[:10]
)