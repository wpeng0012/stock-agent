import pandas as pd


# 因子数据

factor_df = pd.read_csv(
    "../data/stock_factor_daily.csv",
    dtype={
        "code": str
    }
)


# 股票基础信息

stock_df = pd.read_csv(
    "../data/stock_basic.csv",
    dtype={
        "code": str
    }
)



print("因子数据:")
print(factor_df.head())


print("股票信息:")
print(stock_df.head())



# 合并

df = factor_df.merge(
    stock_df[
        [
            "code",
            "name"
        ]
    ],
    on="code",
    how="left"
)



df.to_csv(
    "../data/stock_factor_daily_v2.csv",
    index=False,
    encoding="utf-8-sig"
)


print(
    "合并完成:",
    len(df)
)


print(
    df.head()
)