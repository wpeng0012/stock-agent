import requests


def get_stock_price(code):

    url = (
        "https://hq.sinajs.cn/list=sz"
        + code
    )

    headers = {
        "Referer": "https://finance.sina.com.cn"
    }

    r = requests.get(
        url,
        headers=headers
    )

    data = r.text

    return data


def parse_stock(data):

    content = data.split('"')[1]

    fields = content.split(",")

    result = {

        "name": fields[0],

        "open": fields[1],

        "pre_close": fields[2],

        "price": fields[3],

        "high": fields[4],

        "low": fields[5],

        "volume": fields[8],

        "amount": fields[9],

        "date": fields[30],

        "time": fields[31]

    }

    return result



if __name__ == "__main__":

    data = get_stock_price("000001")

    stock = parse_stock(data)

    print(stock)