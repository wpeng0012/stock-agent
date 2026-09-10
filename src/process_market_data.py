import pandas as pd


df = pd.read_csv(
    "../data/stock_daily_price.csv"
)


# 字段重命名

df = df.rename(
    columns={
        "price":"close",
        "date":"trade_date"
    }
)


# 转数字

num_cols = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount"
]


for col in num_cols:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# 保存标准格式

df.to_csv(
    "../data/stock_daily_price_clean.csv",
    index=False,
    encoding="utf-8-sig"
)


print(df.head())

print("数量:",len(df))