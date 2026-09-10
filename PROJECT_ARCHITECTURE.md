# A股短线投研 Agent 项目架构参考

更新时间：2026-09-09

本文用于指导 `E:\stock-agent` 后续开发。当前目标是先完成可复现的量化筛选 MVP，再逐步增加 Agent 能力。量化计算与 Agent 调度必须保持边界清楚。

## 一、项目定位

项目由两部分组成：

1. Python 量化筛选系统：读取行情、计算因子、过滤股票、评分排序。
2. AI Agent 交互层：理解用户问题，选择合适的量化能力，并解释结果。

Python 负责确定性计算；LangGraph 负责流程编排；LangChain 负责模型、工具和 Agent 循环；DeepSeek 作为模型服务。第一版不使用新闻研究 Agent 和复核 Agent。

## 二、当前已有能力

当前项目已经有以下基础：

- `src/`：行情采集、清洗、合并和因子构建脚本。
- `factors/`：成交额变化、均线、换手率等因子计算函数。
- `strategy/stock_filter.py`：去除 ST、计算当前评分并取候选股票。
- `agent/stock_selector.py`：把候选 CSV 转成 Agent 输入。
- `agent/analysis_agent.py`：调用 DeepSeek 生成分析文字的旧实现。
- `api/`：FastAPI 接口。
- `main.py`：当前固定串行执行入口。

当前主要评分实现是成交额变化 40 分、换手率 30 分、均线趋势 30 分。项目数据和结果必须标明数据截至日期，不能把历史数据描述成实时数据。

当前尚未完成或不能当作已完成能力：

- 新闻和公告真实检索；当前研究脚本中的 `news` 仍是空占位。
- MACD、RSI、KDJ、K 线形态、财务分析、估值、CZSC。
- 完整的 Agent 规划、工具调用循环和多 Agent 协作。
- 复核 Agent、实时预警、自动交易或自主下单。

## 三、MVP 架构

第一版只实现一个总 Agent 加一个量化执行节点：

```text
用户
  ↓
FastAPI
  ↓
LangGraph 工作流
  ↓
总 Agent
  ├─ 理解用户问题
  ├─ 判断是全市场筛选还是指定个股查询
  ├─ 生成受限参数
  └─ 解释最终结果
  ↓
量化节点
  ├─ 读取行情和因子
  ├─ 执行股票过滤
  ├─ 执行评分排序
  └─ 返回候选股票及指标依据
```

总 Agent 不直接计算均线和评分。它只负责理解请求、选择工具和组织回答。量化节点负责实际计算，确保相同输入能够得到可重复结果。

## 四、推荐目录结构

在现有目录上逐步增加，不需要拆成多个项目：

```text
E:\stock-agent
├─ main.py                         # CLI 入口
├─ api/                            # FastAPI 接口
├─ agent/
│  ├─ orchestrator.py              # 总 Agent 与 LangGraph 入口
│  └─ quant_agent.py               # 量化角色入口；首版可调用确定性节点
├─ workflow/
│  ├─ state.py                     # LangGraph 状态
│  └─ graph.py                     # 节点、边和退出条件
├─ tools/
│  ├─ market_tools.py              # 数据状态、历史行情、因子查询
│  └─ screening_tools.py           # 筛选和评分工具
├─ runtime/
│  ├─ model.py                     # DeepSeek/LangChain 模型配置
│  └─ agent_factory.py             # Agent 和工具绑定
├─ schemas/                        # 任务、候选、结果的数据结构
├─ factors/                        # 因子计算
├─ strategy/                       # 选股规则
├─ src/                            # 数据采集和预处理
├─ services/                       # 应用服务层
├─ data/                            # 行情和基础数据
└─ output/                          # 结果文件
```

## 五、模块之间如何联系

模块之间通过结构化 Python 对象或字典传递，不通过互相拼接长文本：

```text
TaskRequest
  → 量化工具
  → CandidateResult
  → 总 Agent
  → FinalAnswer
```

建议至少保留这些字段：

- `code`：股票代码，按字符串处理并保留前导零。
- `name`、`market`：股票身份。
- `data_as_of`：行情数据截至日期。
- `factors`：具体因子值。
- `score_breakdown`：各项得分。
- `quality_flags`：缺失值、窗口不足、数据过期等问题。
- `evidence_ids`：结果引用的证据标识。
- `status`：`completed`、`partial`、`no_data` 或 `failed`。

不要让后续 Agent 只收到股票名称、价格和总分；这样无法验证结论依据。

## 六、MVP 开发顺序

### 1. 先稳定量化函数

把现有脚本改成可调用函数，例如：

```python
def screen_stocks(as_of=None, top_n=10, strategy="v1"):
    ...
    return result
```

函数负责接收参数并返回结果，不在导入模块时自动读文件、写文件或调用模型。保留命令行入口，方便人工运行。

### 2. 统一数据输出

候选结果保留日期、因子值、分项得分和数据质量信息。明确哪些指标已经实现，哪些只是规划。

### 3. 封装量化工具

先提供以下工具：

- `get_data_status`
- `get_price_history`
- `get_factor_snapshot`
- `screen_candidates`
- `get_score_breakdown`

工具由 Python 执行，模型只能传入受校验的参数。

### 4. 用 LangGraph 建最小流程

先实现：

```text
接收问题
→ 总 Agent 识别任务
→ 参数校验
→ 调用量化工具
→ 总 Agent 解释结果
→ 返回答案
```

第一版不做复杂循环、不做并发、不做多 Agent 互相调用。

### 5. 再增加技术指标

按优先级逐步增加 5 日涨幅、MACD、RSI、KDJ 和形态指标。每加入一个指标，都先在 Python 中实现、验证和记录，再暴露给 Agent。

## 七、未来扩展架构

当量化 MVP 稳定后，再扩展为：

```text
总 Agent（LangGraph）
  ├─ 量化 Agent：筛选、技术指标、量价证据
  ├─ 研究 Agent：新闻、公告、行业事件
  ├─ 复核 Agent：检查结论是否有数据和来源支持
  └─ 基本面 Agent：财务、估值、公司业务
```

分 Agent 仍然放在同一个项目中，优先通过函数调用和结构化状态联系。只有出现独立部署、资源隔离、团队分工或扩展压力时，才考虑拆成服务。

总 Agent 负责派发和汇总；分 Agent 默认不直接互相调用。复核 Agent 发现技术证据不足时，向总 Agent 返回补查请求，由总 Agent 再安排量化 Agent。

## 八、Agent 与流程的边界

适合固定流程的工作：

- 数据读取；
- 指标计算；
- ST 过滤；
- 评分和排序；
- 数据质量检查。

适合 Agent 的工作：

- 理解用户的自然语言问题；
- 判断需要调用哪类工具；
- 根据工具结果决定是否需要有限补查；
- 把结构化结果解释给用户。

不要让模型代替 Python 对全市场股票逐只计算指标，也不要让模型在没有数据的情况下补写支撑位、突破前高或主力资金等结论。

## 九、暂时不做的内容

- 每个 Agent 一个独立项目。
- 每只股票一个 Agent。
- 每个技术指标一个 Agent。
- 让 DeepSeek Harness 成为项目运行的必需依赖。
- 自动下单、自动调仓和直接控制交易账户。
- 把评分结果描述为收益保证或买入建议。

DeepSeek Harness 可以作为后续开发和调试工具，但当前项目直接使用 LangChain、LangGraph 和 DeepSeek API 更简单，也更容易沿用已有 FastAPI/Python 代码。

## 十、完成标准

MVP 完成的判断标准：

1. 用户用自然语言提出筛选需求，总 Agent 能转换为受限参数。
2. LangGraph 能调用量化节点并返回结果。
3. 候选股票包含指标、分项得分和数据日期。
4. 同一份输入数据重复运行，结果可解释且基本一致。
5. 数据过期、字段缺失和没有候选时，系统不会伪造成功结果。
6. API 不会因为旧的固定输出文件而返回上一轮结果。

完成这些以后，再增加新闻研究和复核 Agent，风险会小很多。
