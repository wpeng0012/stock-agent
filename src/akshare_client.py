import tushare as ts
import os
from dotenv import load_dotenv


load_dotenv()

token = os.getenv("TUSHARE_TOKEN")

ts.set_token(token)

pro = ts.pro_api()


def test_connection():

    df = pro.stock_basic(
        exchange='',
        list_status='L',
        fields='ts_code,symbol,name,area,industry'
    )

    return df


if __name__ == "__main__":

    df = test_connection()

    print(df.head())

    print("数量:", len(df))