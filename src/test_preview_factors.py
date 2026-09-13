from pathlib import Path
import sys

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.factor_service import build_factor_data
from tools.scoring_tools import calculate_scores


PREVIEW_PRICE_FILE = BASE_DIR / "output" / "market_update_preview.csv"
PREVIEW_FACTOR_FILE = BASE_DIR / "output" / "factor_update_preview.csv"

REQUIRED_SCORE_FIELDS = [
    "close",
    "amount_ratio_1d",
    "turnover_ma5",
    "MA10",
    "MA20",
]


def main():
    if not PREVIEW_PRICE_FILE.exists():
        raise FileNotFoundError(
            f"找不到行情预览文件：{PREVIEW_PRICE_FILE}"
        )

    price = pd.read_csv(
        PREVIEW_PRICE_FILE,
        dtype={"code": str},
    )

    print("行情预览记录数：", len(price))
    print("股票数量：", price["code"].nunique())

    factor = build_factor_data(price)

    latest_date = factor["date"].max()
    latest = factor.loc[factor["date"] == latest_date].copy()

    print("最新因子日期：", latest_date)
    print("最新日期股票数：", len(latest))

    valid = latest.dropna(subset=REQUIRED_SCORE_FIELDS).copy()

    if len(valid) != len(latest):
        invalid_codes = latest.loc[
            ~latest.index.isin(valid.index),
            "code",
        ].tolist()
        raise ValueError(
            "最新日期存在因子不完整股票："
            + ", ".join(invalid_codes)
        )

    scored = calculate_scores(valid)

    display_columns = [
        "code",
        "name",
        "date",
        "close",
        "amount_ratio_1d",
        "turnover_ma5",
        "MA10",
        "MA20",
        "score_amount",
        "score_turnover",
        "score_trend",
        "score",
    ]

    print("\n最新评分：")
    print(
        scored[display_columns]
        .sort_values(
            ["score", "code"],
            ascending=[False, True],
        )
        .to_string(index=False)
    )

    calculated_total = scored[
        ["score_amount", "score_turnover", "score_trend"]
    ].sum(axis=1)
    if not calculated_total.equals(scored["score"]):
        raise AssertionError("总分与分项得分之和不一致")

    latest_rows = factor.groupby("code").tail(1)
    if latest_rows[
        ["MA5", "MA10", "MA20", "turnover_ma5"]
    ].isna().any().any():
        raise AssertionError("最新数据的滚动因子存在缺失")

    repeated = build_factor_data(price)
    pd.testing.assert_frame_equal(
        factor.reset_index(drop=True),
        repeated.reset_index(drop=True),
    )

    PREVIEW_FACTOR_FILE.parent.mkdir(parents=True, exist_ok=True)
    factor.to_csv(
        PREVIEW_FACTOR_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n检查结果：")
    print("通过：分项得分与总分一致")
    print("通过：最新滚动因子完整")
    print("通过：相同输入重复计算结果一致")
    print("因子预览文件：", PREVIEW_FACTOR_FILE)
    print("正式因子文件没有修改")


if __name__ == "__main__":
    main()
