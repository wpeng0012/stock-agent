from pathlib import Path
import sys

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.factor_service import build_factor_data


def main():
    dates = pd.bdate_range("2026-01-01", periods=80)
    records = []
    for code, multiplier in (("000001", 1.0), ("000002", 0.5)):
        for index, day in enumerate(dates):
            close = 10 + multiplier * index * 0.1
            records.append({
                "code": code,
                "date": day.strftime("%Y-%m-%d"),
                "open": close - 0.05,
                "close": close,
                "high": close + 0.2,
                "low": close - 0.2,
                "volume": 100000 + index * 1000,
                "amount": (100000 + index * 1000) * close,
                "turnover": 0.02 + index * 0.0001,
            })
    price = pd.DataFrame(records)
    basic = pd.DataFrame({"code": ["000001", "000002"], "name": ["甲", "乙"]})
    basic_file = BASE_DIR / "output" / "test_technical_stock_basic.csv"
    basic_file.parent.mkdir(parents=True, exist_ok=True)
    basic.to_csv(basic_file, index=False, encoding="utf-8-sig")
    try:
        factor = build_factor_data(price, basic_file)
    finally:
        basic_file.unlink(missing_ok=True)

    required = {
        "amount_ratio_5d", "turnover_ratio_30d", "ma_alignment",
        "ma5_ma10_cross", "ma20_slope_5d", "distance_ma20",
        "return_1d", "return_5d", "return_20d", "macd_dif", "macd_dea",
        "macd_hist", "macd_cross", "rsi6", "kdj_k", "kdj_d", "kdj_j",
        "kdj_cross", "atr14", "atr14_pct", "drawdown_20d", "drawdown_60d",
        "relative_strength_5d", "relative_strength_20d",
    }
    assert required.issubset(factor.columns), sorted(required - set(factor.columns))
    latest = factor.groupby("code").tail(1)
    numeric = list(required - {"ma_alignment", "ma5_ma10_cross", "macd_cross", "kdj_cross"})
    assert np.isfinite(latest[numeric].to_numpy(dtype=float)).all()
    assert set(latest["ma_alignment"]) == {"bullish"}
    assert latest["rsi6"].between(0, 100).all()
    print("通过：技术指标字段、最新值和取值范围正确")


if __name__ == "__main__":
    main()
