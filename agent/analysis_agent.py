import os
import json
from openai import OpenAI


# =========================
# 项目路径
# =========================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)



# =========================
# 读取研究结果
# =========================


input_file = os.path.join(
    OUTPUT_DIR,
    "stock_research.json"
)



with open(
    input_file,
    "r",
    encoding="utf-8"
) as f:

    stocks = json.load(f)



print(
    "分析股票:",
    len(stocks)
)



# =========================
# DeepSeek配置
# =========================


from dotenv import load_dotenv


load_dotenv(
    os.path.join(
        BASE_DIR,
        ".env"
    )
)


api_key = os.getenv(
    "DEEPSEEK_API_KEY"
)


client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)



# =========================
# AI分析
# =========================


results = []



for stock in stocks:


    print(
        "DeepSeek分析:",
        stock["name"]
    )


    prompt = f"""

你是一名A股短线投资分析助手。

请分析下面股票：

股票：
{stock["name"]}

代码：
{stock["code"]}

当前价格：
{stock["price"]}

量化评分：
{stock["score"]}


请从短线角度分析：

1. 技术面机会
2. 资金情况
3. 潜在风险
4. 是否值得关注


要求：
不要推荐买入。
给出客观分析。

输出JSON：

{{
"opportunity":"",
"risk":"",
"suggestion":""
}}

"""


    response = client.chat.completions.create(

        model="deepseek-chat",

        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ],

        temperature=0.3

    )


    content = response.choices[0].message.content


    results.append(

        {

            "code":stock["code"],

            "name":stock["name"],

            "score":stock["score"],

            "analysis":content

        }

    )



# =========================
# 保存
# =========================


output_file=os.path.join(
    OUTPUT_DIR,
    "stock_analysis.json"
)



with open(
    output_file,
    "w",
    encoding="utf-8"
) as f:


    json.dump(

        results,

        f,

        ensure_ascii=False,

        indent=2

    )



print(
    "DeepSeek分析完成:"
)

print(
    output_file
)