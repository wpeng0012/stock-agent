import os
import pandas as pd


# ==========================
# 项目路径
# ==========================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)


OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)


print(
    "项目目录:",
    BASE_DIR
)


# ==========================
# 读取因子数据
# ==========================


factor_file = os.path.join(
    DATA_DIR,
    "stock_factor_daily.csv"
)


df = pd.read_csv(
    factor_file
)


print(
    "因子数据:",
    len(df)
)


# ==========================
# 最新交易日
# ==========================


latest_date = df["date"].max()


df = df[
    df["date"] == latest_date
].copy()


print(
    "日期:",
    latest_date
)



# ==========================
# 去ST
# ==========================


df = df[
    ~df["name"]
    .str.contains(
        "ST",
        na=False
    )
]


print(
    "去ST后:",
    len(df)
)



# ==========================
# 评分
# ==========================


df["score"] = 0



# 成交额

df.loc[
    df["amount_ratio_1d"] > 1.5,
    "score"
] += 40


df.loc[
    (
        df["amount_ratio_1d"] >=1.2
    )
    &
    (
        df["amount_ratio_1d"] <=1.5
    ),
    "score"
] +=30



df.loc[
    (
        df["amount_ratio_1d"] >=1
    )
    &
    (
        df["amount_ratio_1d"] <1.2
    ),
    "score"
] +=20



# 换手


df.loc[
    (
        df["turnover_ma5"] >=0.03
    )
    &
    (
        df["turnover_ma5"] <=0.10
    ),
    "score"
]+=30



df.loc[
    (
        df["turnover_ma5"] >0.10
    )
    &
    (
        df["turnover_ma5"] <=0.15
    ),
    "score"
]+=20



# 趋势


df.loc[
    df["close"] > df["MA20"],
    "score"
]+=30



df.loc[
    (
        df["close"] > df["MA10"]
    )
    &
    (
        df["close"] <= df["MA20"]
    ),
    "score"
]+=20



# ==========================
# 排序
# ==========================


result = df.sort_values(
    "score",
    ascending=False
)



result = result.head(50)



# ==========================
# 输出
# ==========================


output_file = os.path.join(
    OUTPUT_DIR,
    "candidate_stock.csv"
)


result.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)



print(
    "候选股票:",
    len(result)
)


print(
    result[
        [
            "code",
            "name",
            "close",
            "score"
        ]
    ].head(20)
)