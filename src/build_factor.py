import os
import sys
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


# 解决 factors 导入
sys.path.append(BASE_DIR)


from factors.volume_factor import calculate_volume_factor
from factors.trend_factor import calculate_trend_factor
from factors.liquidity_factor import calculate_liquidity_factor


print("项目目录:", BASE_DIR)


# ==========================
# 读取行情数据
# ==========================

price_file = os.path.join(
    DATA_DIR,
    "stock_daily_price.csv"
)


df = pd.read_csv(
    price_file
)


print(
    "原始数据:",
    len(df)
)


# ==========================
# 股票基础信息
# ==========================

basic_file = os.path.join(
    DATA_DIR,
    "stock_basic.csv"
)


stock = pd.read_csv(
    basic_file
)


print(
    "股票信息:",
    len(stock)
)


# ==========================
# 合并股票名称
# ==========================

if "code" in stock.columns:

    df["code"] = (
        df["code"]
        .astype(str)
    )

    stock["code"] = (
        stock["code"]
        .astype(str)
    )


    df = df.merge(
        stock[
            [
                "code",
                "name"
            ]
        ],
        on="code",
        how="left"
    )


print(
    "股票名称合并完成"
)


# ==========================
# 因子计算
# ==========================

df = calculate_volume_factor(df)

df = calculate_trend_factor(df)

df = calculate_liquidity_factor(df)


print(
    "因子计算完成:",
    len(df)
)


# ==========================
# 保存
# ==========================

output_file = os.path.join(
    DATA_DIR,
    "stock_factor_daily.csv"
)


df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)


print(
    "保存完成:",
    output_file
)