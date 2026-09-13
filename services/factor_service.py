from pathlib import Path
from typing import Optional

import pandas as pd

from factors.liquidity_factor import calculate_liquidity_factor
from factors.trend_factor import calculate_trend_factor
from factors.volume_factor import calculate_volume_factor


BASE_DIR = Path(__file__).resolve().parents[1]
STOCK_BASIC_FILE = BASE_DIR / "data" / "stock_basic.csv"

PRICE_COLUMNS = [
    "code",
    "date",
    "open",
    "close",
    "high",
    "low",
    "volume",
    "amount",
    "turnover",
]

FACTOR_COLUMNS = [
    "code",
    "date",
    "name",
    "open",
    "close",
    "high",
    "low",
    "volume",
    "amount",
    "turnover",
    "prev_amount",
    "amount_ratio_1d",
    "MA5",
    "MA10",
    "MA20",
    "turnover_ma5",
]


def normalize_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """统一行情数据格式并检查基础字段。"""
    missing = sorted(set(PRICE_COLUMNS) - set(df.columns))

    if missing:
        raise ValueError(
            "行情数据缺少字段：" + ", ".join(missing)
        )

    result = df[PRICE_COLUMNS].copy()

    result["code"] = (
        result["code"]
        .astype(str)
        .str.zfill(6)
    )

    result["date"] = pd.to_datetime(
        result["date"],
        errors="raise",
    ).dt.strftime("%Y-%m-%d")

    numeric_columns = [
        "open",
        "close",
        "high",
        "low",
        "volume",
        "amount",
        "turnover",
    ]

    for column in numeric_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    if result[numeric_columns].isna().any().any():
        raise ValueError("行情数据存在无法转换的数值")

    if result.duplicated(["code", "date"]).any():
        raise ValueError("行情数据存在重复的股票和日期")

    return result.sort_values(
        ["code", "date"]
    ).reset_index(drop=True)


def load_stock_names(
    stock_basic_file: Path = STOCK_BASIC_FILE,
) -> pd.DataFrame:
    """读取股票代码和名称。"""
    stock = pd.read_csv(
        stock_basic_file,
        dtype={"code": str},
    )

    required = {"code", "name"}
    missing = sorted(required - set(stock.columns))

    if missing:
        raise ValueError(
            "股票基础信息缺少字段：" + ", ".join(missing)
        )

    stock = stock[["code", "name"]].copy()
    stock["code"] = stock["code"].str.zfill(6)

    stock = stock.drop_duplicates(
        subset=["code"],
        keep="last",
    )

    return stock


def build_factor_data(
    price_df: pd.DataFrame,
    stock_basic_file: Optional[Path] = None,
) -> pd.DataFrame:
    """根据完整行情历史计算当前V1因子。"""
    price = normalize_price_data(price_df)

    factor = calculate_volume_factor(price)
    factor = calculate_trend_factor(factor)
    factor = calculate_liquidity_factor(factor)

    basic_file = stock_basic_file or STOCK_BASIC_FILE
    stock = load_stock_names(basic_file)

    factor = factor.merge(
        stock,
        on="code",
        how="left",
        validate="many_to_one",
    )

    if factor["name"].isna().any():
        missing_codes = sorted(
            factor.loc[
                factor["name"].isna(),
                "code",
            ].unique()
        )

        raise ValueError(
            "以下股票缺少名称："
            + ", ".join(missing_codes[:20])
        )

    factor = factor[FACTOR_COLUMNS]

    return factor.sort_values(
        ["code", "date"]
    ).reset_index(drop=True)