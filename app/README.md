# a-stock-data

<p align="center">
  <strong>A 股全栈数据 API 服务</strong><br>
  7 层架构 · 32 个端点 · 13 个数据源 · 零第三方数据封装依赖
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green" alt="FastAPI">
  <img src="https://img.shields.io/badge/tests-277%20passed-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/license-Apache%202.0-orange" alt="License">
</p>

一个自包含的 A 股数据服务，把分散在 13 个数据源里的原始数据整合为统一 RESTful API。所有上游 API 直连，零第三方数据封装依赖（不依赖 akshare/tushare 等）。同时提供 AI Skill 模式（结构化 Markdown + 内嵌 Python），兼容 Claude Code / Codex / OpenClaw。

---

## 目录

- [项目架构](#项目架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API 接口文档](#api-接口文档)
- [统一响应格式](#统一响应格式)
- [环境变量配置](#环境变量配置)
- [核心模块说明](#核心模块说明)
- [数据源一览](#数据源一览)
- [开发指南](#开发指南)
- [测试体系](#测试体系)
- [设计与实现审计表](#设计与实现对比审计表)
- [Skill 模式](#skill-模式)
- [FAQ](#faq)
- [更新日志](#更新日志)
- [License](#license)

---

## 项目架构

### 业务架构（七层数据模型）

```
A 股全栈数据 · 七层架构 · V4.0
│
├── 行情层    mootdx + 腾讯财经 + 百度K线   K线(带MA5/10/20) + 五档盘口 + PE/PB/市值 + 指数/ETF
├── 研报层    东财 reportapi + 同花顺 + iwencai  研报列表 / PDF下载 / 一致预期 / NL搜索
├── 信号层    同花顺 + 百度股市通 + 东财     强势股 + 题材归因 + 北向资金 + 概念板块
│                                           + 资金流向(push2) + 龙虎榜 + 全市场龙虎榜 + 解禁 + 行业对比
├── 资金面    东财 datacenter + push2        融资融券 + 大宗交易 + 股东户数 + 分红送转 + 资金流(分钟+120日)
├── 新闻层    东财 + 财联社（直连HTTP）      个股新闻 / 财联社快讯 / 全球资讯
├── 基础数据  mootdx + 东财 + 新浪           季报37字段 / F10九大类 / 财报三表
└── 公告层    巨潮 cninfo + mootdx           沪深北全量公告
```

### 代码架构（分层设计）

```
app/
├── main.py              # FastAPI 应用入口，路由注册
├── api/routes/          # 路由层 — HTTP 端点定义，参数校验，调用 service
├── services/            # 服务层 — 业务编排，缓存逻辑，多源聚合
├── providers/           # 数据源层 — 直连上游 API/TCP，返回原始数据
├── schemas/             # 响应模型 — Pydantic 统一 envelope
├── domain/              # 领域逻辑 — 纯计算（估值公式、解析逻辑）
└── core/                # 基础设施 — HTTP客户端、缓存、错误处理、配置
```

**数据流方向：**

```
HTTP Request → Route → Service → Provider → 上游数据源
                ↓                    ↓
            Schema (envelope)    core/http (重试+超时)
                                 core/cache (TTL文件缓存)
```

---

## 快速开始

### 环境要求

- Python ≥ 3.11
- pip（推荐 pip ≥ 23.0）

### 安装

```bash
# 克隆项目
git clone https://github.com/simonlin1212/a-stock-data.git
cd a-stock-data

# 安装运行时依赖
pip install fastapi uvicorn requests pandas lxml pydantic-settings

# 安装开发依赖
pip install -U pytest responses httpx ruff

# 可选：mootdx TCP 行情（需国内网络环境）
pip install mootdx
```

### 启动服务

```bash
uvicorn app.main:app --reload
```

服务启动后访问：
- API 文档（Swagger UI）：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/api/v1/health

### 快速验证

```bash
# 获取贵州茅台实时行情
curl "http://localhost:8000/api/v1/quote?codes=600519"

# 获取百度K线
curl "http://localhost:8000/api/v1/kline/600519"

# 获取估值数据
curl "http://localhost:8000/api/v1/valuation/600519"
```

---

## 项目结构

```
a-stock-data/
├── app/                          # 应用主目录
│   ├── __init__.py
│   ├── main.py                   # FastAPI 入口，注册路由和异常处理
│   ├── api/
│   │   └── routes/               # 路由端点
│   │       ├── health.py         # 健康检查
│   │       ├── market.py         # 行情：报价/K线/mootdx行情
│   │       ├── fundamentals.py   # 基础：个股信息/财报/F10
│   │       ├── valuation.py      # 估值：forward PE/PEG/消化
│   │       ├── research.py       # 研报：东财报告/iwencai搜索
│   │       ├── capital.py        # 资金面：融资融券/大宗/股东/分红/资金流
│   │       ├── news.py           # 新闻：个股新闻/电报/全球资讯
│   │       ├── filings.py        # 公告：巨潮公告
│   │       └── signal.py         # 信号：龙虎榜/解禁/行业/概念/北向/热点
│   ├── services/                 # 业务服务层
│   │   ├── market_service.py     # 行情服务（Tencent/Baidu/mootdx）
│   │   ├── fundamentals_service.py  # 基础数据服务
│   │   ├── valuation_service.py  # 估值服务（多源聚合 + 降级）
│   │   ├── research_service.py   # 研报服务
│   │   ├── capital_service.py    # 资金面服务
│   │   ├── news_service.py       # 新闻服务
│   │   ├── filings_service.py    # 公告服务
│   │   └── signal_service.py     # 信号服务
│   ├── providers/                # 数据源 Provider
│   │   ├── tencent.py            # 腾讯财经（实时行情/PE/PB）
│   │   ├── baidu.py              # 百度股市通（K线/概念板块）
│   │   ├── eastmoney.py          # 东方财富（资金流/龙虎榜/融资融券等）
│   │   ├── ths.py                # 同花顺（热点股/北向资金/一致预期）
│   │   ├── sina.py               # 新浪财经（财报三表）
│   │   ├── cninfo.py             # 巨潮（公告）
│   │   ├── cls.py                # 财联社（快讯）
│   │   ├── iwencai.py            # iwencai（NL语义搜索）
│   │   └── mootdx_provider.py   # mootdx（TCP K线/盘口/逐笔/财务/F10）
│   ├── schemas/                  # Pydantic 数据模型
│   │   ├── common.py             # ApiResponse 统一响应 envelope
│   │   ├── market.py             # 行情相关 schema
│   │   ├── capital.py            # 资金面 schema
│   │   ├── fundamentals.py       # 基础数据 schema
│   │   ├── news.py               # 新闻 schema
│   │   ├── research.py           # 研报 schema
│   │   ├── filings.py            # 公告 schema
│   │   └── valuation.py          # 估值 schema
│   ├── domain/                   # 纯业务逻辑（无IO）
│   │   ├── valuation.py          # forward_pe / peg / pe_digestion 计算
│   │   └── parsing.py            # 上游数据解析逻辑
│   └── core/                     # 基础设施
│       ├── config.py             # Pydantic Settings 配置
│       ├── errors.py             # 统一异常体系
│       ├── http.py               # HTTP 客户端（重试/超时/UA）
│       ├── cache.py              # 文件 TTL 缓存
│       └── normalize.py          # 股票代码标准化
├── tests/                        # 测试目录
│   ├── conftest.py               # 共享 fixtures
│   ├── unit/                     # 单元测试（纯逻辑，无IO mock）
│   ├── contract/                 # 契约测试（mock上游，验证provider解析）
│   └── integration/              # 集成测试（TestClient 端到端）
├── SKILL.md                      # AI Skill 文件（13 个数据源完整代码）
├── pyproject.toml                # 项目配置/依赖声明
├── CHANGELOG.md                  # 版本变更日志
└── README.md                     # 本文件
```

---

## API 接口文档

所有接口前缀为 `/api/v1`。股票代码支持多种格式：`600519`、`SH600519`、`600519.SH`。

### 行情层

| 端点 | 方法 | 数据源 | 说明 |
|------|------|--------|------|
| `/quote?codes=600519,000858` | GET | 腾讯财经 | 批量实时行情（PE/PB/市值/涨跌停等17字段） |
| `/kline/{code}` | GET | 百度股市通 | 日K线 + MA5/MA10/MA20 均线 |
| `/mootdx-kline/{code}?category=daily&offset=100` | GET | mootdx TCP | 多周期K线（日/周/月/分钟级） |
| `/mootdx-quotes?codes=688017,300476` | GET | mootdx TCP | 五档盘口 + 46字段实时报价 |
| `/mootdx-transaction/{code}?date=20260528` | GET | mootdx TCP | 逐笔成交明细 |

### 研报层

| 端点 | 方法 | 数据源 | 说明 |
|------|------|--------|------|
| `/reports/{code}` | GET | 东财 reportapi | 研报列表 + 评级 + EPS 预测 + PDF URL |
| `/iwencai-search?query=人形机器人&channel=report&size=50` | GET | iwencai | NL自然语言跨主题搜索 |
| `/valuation/{code}` | GET | 腾讯+同花顺 | forward PE / PEG / PE消化年数（含一致预期EPS） |

### 信号层

| 端点 | 方法 | 数据源 | 说明 |
|------|------|--------|------|
| `/hot-stocks?date=2026-05-28` | GET | 同花顺 | 当日强势股 + 题材归因 reason tags |
| `/northbound` | GET | 同花顺 | 沪/深股通实时分钟级净流入 |
| `/northbound/history?days=30` | GET | 本地缓存 | 北向资金日级历史（自动积累） |
| `/concept-blocks/{code}` | GET | 百度股市通 | 概念/行业/地域板块归属 |
| `/billboard/{code}?trade_date=2026-05-28` | GET | 东财 | 龙虎榜席位 + 买卖TOP5 |
| `/billboard/daily?trade_date=2026-05-28` | GET | 东财 | 全市场龙虎榜净买排名 |
| `/lockup/{code}` | GET | 东财 | 限售解禁日历（历史+未来90天） |
| `/industry-ranking?top_n=20` | GET | 东财 push2 | 行业涨跌幅排名 |
| `/fund-flow/minute/{code}` | GET | 东财 push2 | 主力/大单/中单/小单分钟级净流入 |

### 资金面层

| 端点 | 方法 | 数据源 | 说明 |
|------|------|--------|------|
| `/margin/{code}` | GET | 东财 datacenter | 融资融券明细（余额/买入/偿还） |
| `/block-trade/{code}` | GET | 东财 datacenter | 大宗交易（价/量/溢价率/买卖方） |
| `/holder-num/{code}` | GET | 东财 datacenter | 股东户数变化 + 户均持股 |
| `/dividend/{code}` | GET | 东财 datacenter | 分红送转历史 |
| `/fund-flow/daily/{code}` | GET | 东财 push2his | 资金流120日（主力/大单/中单日级） |

### 新闻层

| 端点 | 方法 | 数据源 | 说明 |
|------|------|--------|------|
| `/news/{code}` | GET | 东财 search-api | 个股相关新闻 |
| `/telegraph` | GET | 财联社 cls.cn | 分钟级快讯电报 |
| `/global-news` | GET | 东财 np-weblist | 全球财经资讯 |

### 基础数据层

| 端点 | 方法 | 数据源 | 说明 |
|------|------|--------|------|
| `/stock-info/{code}` | GET | 东财 push2 | 行业/总股本/流通股/市值（10min缓存） |
| `/financial-report/{code}?report_type=lrb` | GET | 新浪财经 | 财报三表（fzb/lrb/llb） |
| `/finance-snapshot/{code}` | GET | mootdx TCP | 季报37字段快照 |
| `/f10/{code}?category=公司概况` | GET | mootdx TCP | F10 九大类文本 |
| `/f10-announcement/{code}` | GET | mootdx TCP | 最新提示公告 |

### 公告层

| 端点 | 方法 | 数据源 | 说明 |
|------|------|--------|------|
| `/announcements/{code}` | GET | 巨潮 cninfo | 沪深北全量公告 |

### 系统

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |

---

## 统一响应格式

所有接口返回统一 envelope（成功和失败结构完全一致，便于客户端统一解析）：

### 成功响应

```json
{
  "success": true,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": { ... },
  "source": ["tencent"],
  "cached": false,
  "warnings": [],
  "fetched_at": "2026-05-29T01:00:00+00:00",
  "error": null
}
```

### 错误响应

```json
{
  "success": false,
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "data": null,
  "source": [],
  "cached": false,
  "warnings": [],
  "fetched_at": "2026-05-29T01:00:00+00:00",
  "error": {
    "code": "UPSTREAM_HTTP_ERROR",
    "message": "HTTP 502 from https://...",
    "provider": "eastmoney"
  }
}
```

### 错误码体系

| 错误码 | HTTP Status | 含义 |
|--------|-------------|------|
| `VALIDATION_ERROR` | 400 | 请求参数校验失败（如无效股票代码） |
| `PROVIDER_AUTH_ERROR` | 403 | 数据源鉴权失败（如 iwencai Key 无效） |
| `UPSTREAM_HTTP_ERROR` | 502 | 上游数据源 HTTP 请求失败 |
| `UPSTREAM_SCHEMA_ERROR` | 502 | 上游返回数据结构不符合预期 |
| `DEPENDENCY_UNAVAILABLE` | 503 | 依赖不可用（如 mootdx TCP 连接失败） |

---

## 环境变量配置

通过环境变量或 `.env` 文件配置（基于 pydantic-settings）：

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `APP_ENV` | str | `development` | 运行环境 |
| `APP_HOST` | str | `0.0.0.0` | 监听地址 |
| `APP_PORT` | int | `8000` | 监听端口 |
| `LOG_LEVEL` | str | `INFO` | 日志级别 |
| `DEFAULT_HTTP_TIMEOUT` | int | `15` | HTTP 请求超时（秒） |
| `DEFAULT_RETRY_COUNT` | int | `2` | 上游请求自动重试次数 |
| `CACHE_DIR` | str | `.cache` | 文件缓存目录（空字符串 = 禁用缓存） |
| `ENABLE_MOOTDX` | bool | `false` | 是否启用 mootdx TCP 连接 |
| `IWENCAI_API_KEY` | str | `""` | iwencai 语义搜索 API Key |
| `IWENCAI_BASE_URL` | str | `https://openapi.iwencai.com` | iwencai 接口基础 URL |

---

## 核心模块说明

### `app/core/http.py` — HTTP 客户端

- 全局共享 `requests.Session`，连接池复用
- 自动重试（可配置次数，默认 2 次，指数退避）
- 统一 User-Agent 头
- 超时保护（默认 15s）
- 所有 HTTP 错误统一抛 `UpstreamHTTPError`

### `app/core/cache.py` — 文件 TTL 缓存

- 基于文件系统的 JSON 缓存
- TTL 过期自动清理
- 原子写入（先写 tmp 再 rename，防止读到半成品）
- 可通过 `CACHE_DIR=""` 完全禁用
- 命名空间隔离，避免 key 冲突

### `app/core/errors.py` — 统一异常体系

```
AppError (base)
├── ValidationError          400  参数校验
├── UpstreamHTTPError        502  上游HTTP失败
├── UpstreamSchemaError      502  上游结构异常
├── ProviderAuthError        403  鉴权失败
└── DependencyUnavailableError  503  TCP/依赖不可用
```

所有异常统一通过 `app_error_handler` 转换为标准 envelope 响应。

### `app/core/normalize.py` — 股票代码标准化

支持多种输入格式自动转换：
- `600519` → `600519`
- `SH600519` / `sh600519` → `600519`
- `600519.SH` → `600519`

自动判断市场前缀（sh/sz/bj），并提供各数据源的 symbol 格式转换：
- `to_tencent_symbol("600519")` → `"sh600519"`
- `to_eastmoney_secid("600519")` → `"1.600519"`
- `to_cninfo_org_id("600519")` → `"gssh0600519"`

### `app/domain/valuation.py` — 估值计算

纯函数，无 IO 依赖：
- `forward_pe(price, eps_forecast)` — 前瞻市盈率
- `calc_peg(pe, cagr)` — PEG 估值
- `pe_digestion(current_pe, cagr, target_pe=30)` — PE 消化年数

---

## 数据源一览

| 优先级 | 数据源 | 协议 | 需要 Key | 封 IP 风险 |
|--------|--------|------|----------|-----------|
| 1 | mootdx | TCP 7709 | ❌ | 极低 |
| 2 | 腾讯财经 | HTTP | ❌ | 低 |
| 3 | 东财 datacenter | HTTP | ❌ | 低 |
| 4 | 东财 push2/push2his | HTTP | ❌ | 低 |
| 5 | iwencai | OpenAPI | ✅ | 低 |
| 6 | 东财 reportapi/PDF | HTTP | ❌ | 低 |
| 7 | 同花顺热点 | HTTP | ❌ | 极低 |
| 8 | 同花顺北向 | HTTP | ❌ | 极低 |
| 9 | 百度股市通 | HTTP | ❌ | 极低 |
| 10 | 新浪财经 | HTTP | ❌ | 低 |
| 11 | 同花顺一致预期 | HTTP | ❌（需UA） | 低 |
| 12 | 财联社 | HTTP | ❌ | 低 |
| 13 | 巨潮 cninfo | HTTP | ❌ | 低 |

> **架构原则：** 除 mootdx（TCP 二进制协议）外，全部直连 HTTP API，零第三方数据封装依赖。

---

## 开发指南

### 代码规范

- Python 3.11+，type hints 全覆盖
- 行宽限制 120 字符
- 使用 `ruff` 进行代码检查
- 所有路由端点必须声明 `response_model=ApiResponse`

### 常用命令

```bash
# 启动开发服务（热重载）
uvicorn app.main:app --reload

# 代码检查
ruff check app/ tests/

# 运行全量测试
pytest tests/

# 运行指定测试
pytest tests/contract/test_mootdx_provider.py -v

# 查看测试覆盖
pytest tests/ --co -q  # 列出所有测试用例
```

### 新增端点标准流程

1. **Provider** (`app/providers/xxx.py`) — 封装上游 API 调用，返回原始 dict/list
2. **Service** (`app/services/xxx_service.py`) — 业务编排，代码标准化，缓存逻辑
3. **Route** (`app/api/routes/xxx.py`) — HTTP 端点，参数校验，调用 service，包装 envelope
4. **Contract Test** (`tests/contract/`) — mock 上游，验证 provider 解析逻辑
5. **Integration Test** (`tests/integration/`) — TestClient 端到端，mock provider
6. **README 审计表** — 更新端点状态

### Provider 开发规范

```python
# 标准 Provider 模板
from app.core.http import http_get
from app.core.errors import UpstreamHTTPError, UpstreamSchemaError

def fetch_xxx(code: str) -> list[dict]:
    """获取xxx数据。
    
    Raises:
        UpstreamHTTPError: 上游HTTP请求失败
        UpstreamSchemaError: 上游返回数据结构异常
    """
    url = f"https://api.example.com/data/{code}"
    resp = http_get(url, provider="example")
    
    try:
        data = resp.json()
    except ValueError:
        raise UpstreamSchemaError("Invalid JSON response", provider="example")
    
    # 解析并返回
    return [{"field": item["field"]} for item in data.get("items", [])]
```

---

## 测试体系

项目采用三层测试架构，共 277 个测试用例：

### 测试分层

| 层级 | 目录 | 职责 | Mock 范围 |
|------|------|------|-----------|
| Unit | `tests/unit/` | 纯逻辑测试（无IO） | 无需 mock |
| Contract | `tests/contract/` | Provider 解析契约验证 | mock `_get_client` 或 `responses` |
| Integration | `tests/integration/` | 端到端 HTTP 测试 | mock provider 函数 |

### 测试文件对照

| 测试文件 | 覆盖模块 |
|----------|----------|
| `unit/test_normalize.py` | 股票代码标准化 |
| `unit/test_cache.py` | TTL 缓存逻辑 |
| `unit/test_valuation_domain.py` | 估值纯计算 |
| `unit/test_http_retry.py` | HTTP 重试机制 |
| `unit/test_response_schema.py` | envelope 结构 |
| `contract/test_tencent_provider.py` | 腾讯行情解析 |
| `contract/test_eastmoney_provider.py` | 东财数据解析 |
| `contract/test_mootdx_provider.py` | mootdx 全部函数（K线/盘口/逐笔/财务/F10） |
| `contract/test_ths_signal_provider.py` | 同花顺信号解析 |
| `integration/test_quote_api.py` | 行情端点 |
| `integration/test_mootdx_endpoints.py` | mootdx 全部 6+3 端点 |
| `integration/test_valuation_api.py` | 估值端点 |
| `integration/test_eastmoney_apis.py` | 东财系列端点 |

### 运行测试

```bash
# 全量测试
pytest tests/ -q

# 指定层级
pytest tests/unit/ -v
pytest tests/contract/ -v
pytest tests/integration/ -v

# 指定文件
pytest tests/contract/test_mootdx_provider.py -v

# 查看详细输出
pytest tests/ -v --tb=short
```

---

## 设计与实现对比审计表

对照 SKILL.md 能力，当前 API 服务的实现状态。

**状态词定义：**
- ✅ 已实现并验证 — mock+contract+integration 测试通过，HTTP 数据源已验证
- ⚠️ 仅mock验证 — 代码完整、mock 测试通过，但未经真实上游验证
- ⚠️ 已接线待TCP — 代码+mock 通过，需 mootdx TCP 7709 可达环境
- ⚠️ 已接线待Key — 代码+mock 通过，需 IWENCAI_API_KEY 环境变量

| Layer | SKILL.md 功能 | API 状态 | 说明 |
|-------|--------------|----------|------|
| **1 行情** | mootdx K线/盘口/逐笔 | ⚠️ 已接线待TCP | `/mootdx-kline`、`/mootdx-quotes`、`/mootdx-transaction` |
| **1 行情** | 腾讯 PE/PB/市值/实时行情 | ✅ 已实现并验证 | `/quote` |
| **1 行情** | 百度K线(带MA) | ✅ 已实现并验证 | `/kline/{code}` |
| **2 研报** | 东财研报列表+PDF URL | ✅ 已实现并验证 | `/reports/{code}` |
| **2 研报** | 同花顺一致预期EPS | ⚠️ 仅mock验证 | 内嵌于 `/valuation` |
| **2 研报** | iwencai NL语义搜索 | ⚠️ 已接线待Key | `/iwencai-search` |
| **3 信号** | 同花顺热点强势股 | ⚠️ 仅mock验证 | `/hot-stocks` |
| **3 信号** | 同花顺北向资金(实时) | ⚠️ 仅mock验证 | `/northbound` |
| **3 信号** | 同花顺北向资金(历史) | ✅ 已实现并验证 | `/northbound/history` |
| **3 信号** | 百度概念板块 | ✅ 已实现并验证 | `/concept-blocks/{code}` |
| **3 信号** | 东财资金流(分钟) | ✅ 已实现并验证 | `/fund-flow/minute/{code}` |
| **3 信号** | 龙虎榜席位 | ✅ 已实现并验证 | `/billboard/{code}` |
| **3 信号** | 限售解禁日历 | ✅ 已实现并验证 | `/lockup/{code}` |
| **3 信号** | 行业板块排名 | ✅ 已实现并验证 | `/industry-ranking` |
| **3 信号** | 全市场龙虎榜 | ✅ 已实现并验证 | `/billboard/daily` |
| **4 资金面** | 融资融券明细 | ✅ 已实现并验证 | `/margin/{code}` |
| **4 资金面** | 大宗交易 | ✅ 已实现并验证 | `/block-trade/{code}` |
| **4 资金面** | 股东户数变化 | ✅ 已实现并验证 | `/holder-num/{code}` |
| **4 资金面** | 分红送转历史 | ✅ 已实现并验证 | `/dividend/{code}` |
| **4 资金面** | 资金流120日 | ✅ 已实现并验证 | `/fund-flow/daily/{code}` |
| **5 新闻** | 东财个股新闻 | ✅ 已实现并验证 | `/news/{code}` |
| **5 新闻** | 财联社快讯 | ✅ 已实现并验证 | `/telegraph` |
| **5 新闻** | 东财全球资讯 | ✅ 已实现并验证 | `/global-news` |
| **6 基础** | mootdx 财务快照 | ⚠️ 已接线待TCP | `/finance-snapshot/{code}` |
| **6 基础** | mootdx F10 | ⚠️ 已接线待TCP | `/f10/{code}` |
| **6 基础** | 东财个股基本面 | ✅ 已实现并验证 | `/stock-info/{code}` |
| **6 基础** | 新浪财报三表 | ✅ 已实现并验证 | `/financial-report/{code}` |
| **7 公告** | 巨潮公告 | ✅ 已实现并验证 | `/announcements/{code}` |
| **7 公告** | mootdx F10 公告 | ⚠️ 已接线待TCP | `/f10-announcement/{code}` |
| **估值** | forward PE / PEG / PE消化 | ✅ 已实现并验证 | `/valuation/{code}` |

**统计:**
- ✅ 已实现并验证: 22 项
- ⚠️ 仅mock验证: 3 项（THS热点+THS北向实时+THS一致预期）
- ⚠️ 已接线待TCP: 6 项（mootdx 全部端点）
- ⚠️ 已接线待Key: 1 项（iwencai）

---

## Skill 模式

除了 API 服务外，本项目还提供 AI Skill 文件模式，兼容 Claude Code / Codex / OpenClaw。

### 快速开始

```bash
# 1. 创建 skill 目录
mkdir -p ~/.claude/skills/a-stock-data

# 2. 下载 SKILL.md
curl -o ~/.claude/skills/a-stock-data/SKILL.md \
  https://raw.githubusercontent.com/simonlin1212/a-stock-data/main/SKILL.md

# 3. 安装依赖（V3.0 不再需要 akshare）
pip install mootdx requests pandas stockstats
```

启动 Claude Code，说一句「帮我看看 688017 的估值」，自动激活。

> **Codex / OpenClaw 用户：** 把 SKILL.md 的内容贴入你的系统 prompt 或项目上下文文件即可，内嵌的 Python 代码可直接执行。

---

## 使用示例

### API 模式（curl）

```bash
# 个股估值
curl "http://localhost:8000/api/v1/valuation/688017"

# 批量行情
curl "http://localhost:8000/api/v1/quote?codes=600519,000858,300750"

# 龙虎榜
curl "http://localhost:8000/api/v1/billboard/600519"

# 今日全市场龙虎榜
curl "http://localhost:8000/api/v1/billboard/daily"

# 融资融券
curl "http://localhost:8000/api/v1/margin/600519"

# 财联社快讯
curl "http://localhost:8000/api/v1/telegraph"

# 财报三表（利润表）
curl "http://localhost:8000/api/v1/financial-report/600519?report_type=lrb"
```

### AI Skill 模式（自然语言）

| 场景 | 说什么 |
|------|--------|
| 个股估值 | 「帮我估一下 688017，给我 PE / PEG / 消化时间」 |
| 题材归因 | 「今天哪些股票走强，主要是什么题材」 |
| 研报检索 | 「人形机器人产业链最近的研报，特别是丝杠和减速器」 |
| 北向资金 | 「今天北向资金流入流出怎么样」 |
| 资金流向 | 「000858 今天主力资金流入还是流出」 |
| 龙虎榜 | 「002475 最近上过龙虎榜吗，哪些营业部在买」 |
| 融资融券 | 「600519 最近的融资余额变化趋势」 |
| 批量对比 | 「帮我对比这 5 只半导体股的估值」 |

---

## FAQ

**Q: mootdx 和腾讯有什么区别？**
互补。mootdx = 交易层（价格 + 盘口 + K 线），腾讯 = 估值层（PE / PB / 市值 / 换手率 / 涨跌停价）。两者都不封 IP。

**Q: 在海外服务器跑，mootdx 超时？**
mootdx 走 TCP 直连通达信行情服务器，需国内 IP 才稳定。海外环境建议走代理或切换到 yfinance。

**Q: 腾讯 API 字段 43 是 PB 吗？**
不是。43 = 振幅%，46 = PB。网上大量教程写错了，这里是实测校准结果。

**Q: V3.0 为什么移除 akshare？**
akshare 本质是对东财/同花顺/新浪等公开 API 的封装，中间层增加了故障点（版本兼容 bug、pandas 3.0 ArrowInvalid 等）。V3.0 直连底层 HTTP API，零中间依赖，更稳定可控。

**Q: 行业板块为什么从同花顺换成东财？**
同花顺 `stock_board_industry_summary_ths` 接口 2026 年初加了反爬 401。东财 push2 行业板块（`m:90+t:2`）是完美替代，零鉴权且字段更丰富。

**Q: iwencai 返回 401？**
检查：(1) API Key 有效性 (2) 是否携带了 X-Claw-* Headers。SkillHub 2.0 后强制要求。

**Q: 同花顺热点 reason 字段为空？**
盘后数据还没更新，15:30 之后再调。个别 ST 股没有人工标注，`dropna` 过滤即可。

**Q: 百度股市通 ResultCode 不稳定？**
已知坑——有时返回 int `0`，有时返回 string `"0"`。代码里用 `str()` 统一比较即可。

**Q: 北向资金历史只有几天？**
本地自缓存机制。每次调用 `/northbound` 自动积累历史。`/northbound/history` 读取本地日级缓存，越跑越丰富。

**Q: 不用 Claude Code，能用吗？**
能。SKILL.md 本质是 Markdown + 内嵌 Python 代码。Codex、OpenClaw 或任何 AI 编程助手都能读取。你也可以直接把 Python 代码段复制出来在自己的脚本里跑。API 服务模式则提供标准 RESTful 接口，任何 HTTP 客户端都可调用。

**Q: 如何部署为生产服务？**
```bash
# 使用 gunicorn + uvicorn worker
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 更新日志

见 [CHANGELOG.md](./CHANGELOG.md)。

---

## Donate

如果这个工具帮到了你的投研工作流，欢迎请作者喝杯咖啡 ☕

<p align="center">
  <img src="./assets/wechat-sponsor.jpg" width="240" alt="微信赞赏码">
</p>
<p align="center">
  <a href="https://ifdian.net/a/simonlin">爱发电</a> ·
  <a href="https://buymeacoffee.com/simonlin1212">Buy Me a Coffee</a>
</p>

> 想要什么数据端点？欢迎开 [Issue](https://github.com/simonlin1212/a-stock-data/issues) 提需求，赞助者的 Issue 优先处理。

---

## Disclaimer

本项目仅提供数据获取工具，不构成任何投资建议。股市有风险，投资需谨慎。

---

## License

[Apache License 2.0](./LICENSE) — 自由使用，注明出处即可。

**作者：** Simon 林 · 抖音「Simon林」 · 公众号「硅基世纪」

