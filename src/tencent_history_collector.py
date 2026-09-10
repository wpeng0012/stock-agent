import akshare as ak
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed


def load_stock_list():

    df = pd.read_csv(
        "../data/stock_basic.csv",
        dtype={
            "code": str
        }
    )

    return df



def get_history(code):

    try:

        df = ak.stock_zh_a_hist_tx(
            symbol=code,
            start_date="20260101",
            end_date="20260821"
        )

        if df.empty:
            return None


        df["code"] = code

        return df


    except Exception as e:

        print(
            code,
            "失败:",
            e
        )

        return None



def collect_all():

    stocks = load_stock_list()


    # 测试阶段
    stocks = stocks.head(100)


    result=[]


    with ThreadPoolExecutor(
        max_workers=10
    ) as executor:


        tasks = []


        for code in stocks["code"]:

            tasks.append(
                executor.submit(
                    get_history,
                    code
                )
            )


        for future in as_completed(tasks):

            data = future.result()


            if data is not None:

                result.append(data)


    return result



if __name__ == "__main__":


    data_list = collect_all()


    final = pd.concat(
        data_list,
        ignore_index=True
    )


    final.to_csv(
        "../data/stock_daily_price.csv",
        index=False,
        encoding="utf-8-sig"
    )


    print(
        "完成:",
        len(final)
    )