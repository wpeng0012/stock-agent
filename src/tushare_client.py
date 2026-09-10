import tushare as ts
import os
from dotenv import load_dotenv


load_dotenv()


token = os.getenv("TUSHARE_TOKEN")

ts.set_token(token)

pro = ts.pro_api()


def get_daily():

    df = pro.daily(
        trade_date="20260822"
    )

    return df


if __name__ == "__main__":

    df = get_daily()

    print(df.head())

    print("数量:", len(df))