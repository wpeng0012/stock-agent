from datetime import date
from pathlib import Path

import akshare as ak
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]


def main():
    code = "000001"
    start_date = "20260817"
    end_date = date.today().strftime("%Y%m%d")

    print("检查股票：", code)
    print("请求日期：", start_date, "至", end_date)
    print("正在获取行情……", flush=True)

    try:
        df = ak.stock_zh_a_hist_tx(
            symbol="sz000001",
            start_date=start_date,
            end_date=end_date,
            adjust="",
            timeout=20,
        )
    except Exception as exc:
        print("获取失败：", type(exc).__name__, str(exc))
        return

    if df is None or df.empty:
        print("接口没有返回数据")
        return

    required = [
        "date",
        "open",
        "close",
        "high",
        "low",
        "volume",
        "amount",
        "turnover",
    ]

    missing = [column for column in required if column not in df.columns]

    print("\n返回字段：", list(df.columns))
    print("缺少字段：", missing)
    print("返回条数：", len(df))

    if missing:
        return

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    print("最新日期：", df["date"].max())

    print("\n最近 5 条行情：")
    print(df[required].tail(5).to_string(index=False))

    print("\n各字段缺失数量：")
    print(df[required].isna().sum().to_string())

    # 与本地重叠日期的数据比较，检查口径是否一致
    local_file = BASE_DIR / "data" / "stock_daily_price.csv"

    if local_file.exists():
        local = pd.read_csv(local_file, dtype={"code": str})
        local["code"] = local["code"].str.zfill(6)
        local["date"] = pd.to_datetime(
            local["date"]
        ).dt.strftime("%Y-%m-%d")

        columns = ["date", "close", "volume", "amount", "turnover"]

        matched = local.loc[
            local["code"] == code, columns
        ].merge(
            df[columns],
            on="date",
            suffixes=("_local", "_remote"),
        )

        print("\n与本地历史数据的重叠对比：")

        if matched.empty:
            print("没有重叠日期，暂时无法比较口径")
        else:
            print(matched.tail(3).to_string(index=False))

    print("\n检查完成，本次没有修改本地行情文件。")


if __name__ == "__main__":
    main()