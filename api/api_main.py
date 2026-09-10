from fastapi import FastAPI

from api.stock_api import router


app = FastAPI(
    title="A股短线投资Agent"
)

app.include_router(router)


@app.get("/")
def home():
    return {
        "message": "stock agent api running"
    }