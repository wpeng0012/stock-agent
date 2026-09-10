# 本地启动

本项目统一使用 `E:\stock-agent\.venv\Scripts\python.exe`（Python 3.13）。
系统默认的 `python`、`pip` 和 `uvicorn` 可能属于 Anaconda，请使用以下入口。

在项目目录的 PowerShell 中启动 API：

```powershell
.\start_api.cmd
```

浏览器打开 http://127.0.0.1:8000/docs 。`GET /stocks/run` 会重新计算因子、筛选股票并调用 DeepSeek 分析前 10 只候选股，更新 output 下的结果。

开发时需要自动重启，可使用 `.\start_api.cmd --reload`。
终端可以最小化，关闭终端会停止服务；按 Ctrl+C 主动停止。

单独运行完整流程：

```powershell
.\.venv\Scripts\python.exe main.py
```

安装依赖也使用同一解释器：

```powershell
.\.venv\Scripts\python.exe -m pip install 包名
```

PyCharm 项目解释器应选择 `E:\stock-agent\.venv\Scripts\python.exe`。
`main.py` 中的子脚本固定使用项目解释器和项目目录，不依赖终端是否激活虚拟环境。

行情采集不在当前 API 流程内；运行接口不会自动更新历史行情。
