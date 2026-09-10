import akshare as ak
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from datetime import datetime


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
            "失败",
            e
        )

        return None



def collect_all():


    stocks = load_stock_list()


    print(
        "股票数量:",
        len(stocks)
    )


    result=[]

    failed=[]


    with ThreadPoolExecutor(
        max_workers=10
    ) as executor:


        tasks={}


        for code in stocks["code"]:


            future = executor.submit(
                get_history,
                code
            )


            tasks[future]=code



        for future in as_completed(tasks):


            code = tasks[future]


            try:

                data = future.result()


                if data is not None:

                    result.append(data)

                    print(
                        code,
                        "完成"
                    )

                else:

                    failed.append(code)


            except Exception:

                failed.append(code)



    return result,failed



if __name__ == "__main__":


    start=datetime.now()


    data_list,failed = collect_all()


    print(
        "成功股票:",
        len(data_list)
    )


    print(
        "失败股票:",
        len(failed)
    )



    if data_list:


        final=pd.concat(
            data_list,
            ignore_index=True
        )


        final.to_csv(
            "../data/stock_daily_price.csv",
            index=False,
            encoding="utf-8-sig"
        )


        print(
            "行情保存完成:",
            len(final)
        )



    if failed:


        pd.DataFrame(
            {
                "code":failed
            }
        ).to_csv(
            "../data/failed_stock.csv",
            index=False
        )



    print(
        "耗时:",
        datetime.now()-start
    )