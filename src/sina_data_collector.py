import pandas as pd
import time

from sina_market import get_stock_price, parse_stock


def load_stock_list():

    df = pd.read_csv(
        "../data/stock_basic.csv",
        dtype={
            "code": str
        }
    )

    return df



def collect_market_data():

    stocks = load_stock_list()

    result = []


    # 先测试100只
    stocks = stocks.head(100)


    for index, row in stocks.iterrows():

        code = row["code"]


        try:

            data = get_stock_price(code)

            stock = parse_stock(data)

            stock["code"] = code

            result.append(stock)


            print(
                code,
                stock["name"],
                stock["price"]
            )


            time.sleep(0.1)


        except Exception as e:

            print(
                code,
                "失败",
                e
            )


    return pd.DataFrame(result)



if __name__ == "__main__":

    df = collect_market_data()


    print(df.head())


    df.to_csv(
        "../data/stock_daily_price.csv",
        index=False,
        encoding="utf-8-sig"
    )


    print(
        "保存完成:",
        len(df)
    )