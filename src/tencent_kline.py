import akshare as ak


df = ak.stock_zh_a_hist_tx(
    symbol="000001",
    start_date="20260101",
    end_date="20260821"
)


print(df.head())

print(len(df))