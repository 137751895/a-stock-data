# a-stock-data API 服务化 MVP 任务拆解清单

本文件是直接开工的 MVP 执行清单。

默认前提：

- 已阅读 [API_SERVICE_DEVELOPMENT_GUIDE.md](API_SERVICE_DEVELOPMENT_GUIDE.md)
- 当前目标是先交付 MVP，而不是一次性完成全部 28 个端点

使用方式：

- 严格按 Phase 顺序推进
- 每完成一个切片立即验证
- 如果遇到架构分歧，再回看 [API_SERVICE_DEVELOPMENT_GUIDE.md](API_SERVICE_DEVELOPMENT_GUIDE.md)

## 1. MVP 目标

先把项目从 Skill 形态落成一个可运行、可测试、可扩展的 FastAPI 服务骨架，并优先提供 8 个高价值接口。

MVP 只做这些：

- 健康检查
- 实时报价
- 单票估值
- 研报列表
- 个股基本面
- 分钟级资金流
- 融资融券
- 公告列表
- 个股新闻

MVP 暂不强求：

- mootdx TCP 能力
- F10 文本大块处理
- 北向资金缓存体系升级
- 批量工作流
- 全量 28 端点一次性完成

## 2. MVP 完成标准

满足以下条件就算 MVP 完成：

- 已建立标准 Python 项目结构
- 服务可启动
- `/api/v1/health` 可用
- 上述 8 个接口可返回统一 JSON
- 已有单元测试、Provider 契约测试、API 集成测试
- 已覆盖 3 个高风险回归点：
  - 腾讯字段 43/46 映射
  - 巨潮 orgId 规则
  - 东财资金流使用 push2 而不是旧百度接口

## 2.1 集成 Karpathy 执行守则

这份清单同时集成 [andrej-karpathy-skills-main/skills/karpathy-guidelines/SKILL.md](andrej-karpathy-skills-main/skills/karpathy-guidelines/SKILL.md) 的四条原则，并把它们压成直接可执行的约束：

- 编码前思考：每个非琐碎切片开始前先写“假设 / 歧义 / 最小切片 / 验证方式”
- 简洁优先：没有第二个真实调用点前，不要引入通用抽象、基类、工厂、仓储层
- 精准修改：每一处改动都必须直接服务于当前卡片或当前失败测试
- 目标驱动执行：每张卡必须带明确验证命令，未验证不得进入下一张卡

这次任务属于非琐碎改造，必须完整启用这四条规则，不能按“简单任务”处理。

配套项目化示例见 [API_SERVICE_PROJECT_EXAMPLES.md](API_SERVICE_PROJECT_EXAMPLES.md)。

如果只是每次开工前快速自检，直接使用 [API_SERVICE_60S_PRESTART_CHECKLIST.md](API_SERVICE_60S_PRESTART_CHECKLIST.md)。

使用方式：

- 开始一个新卡片前，先看对应原则下的项目反例 / 正例
- 如果当前实现方案看起来像“提前抽象”“顺手重构”“全量后测”，先回到这页对照
- 如果当前卡片写不出明确验证命令，也先回到这页对照

## 2.2 最小依赖与首批命令

MVP 推荐依赖：

- 运行时：fastapi、uvicorn、requests、pandas、lxml、pydantic-settings
- 开发时：pytest、responses 或 requests-mock、httpx、ruff

首批命令：

```bash
pip install fastapi uvicorn requests pandas lxml pydantic-settings
pip install -U pytest responses httpx ruff
uvicorn app.main:app --reload
pytest
```

特别说明：

- `pandas` 和 `lxml` 不能省。估值接口依赖同花顺 HTML 表格解析。
- MVP 先不要装 `mootdx`、`stockstats`、Redis、Celery；这些属于后续阶段，不要提前扩张复杂度。

## 3. 开工顺序

严格按这个顺序做，不要跳步。

### Phase 0：定范围，不写业务代码

任务：

- 确认 MVP 只覆盖 8 个接口
- 确认技术栈：FastAPI + Pydantic + requests + pandas + lxml + pytest + responses 或 requests-mock
- 确认目录结构
- 确认统一响应格式
- 确认错误模型
- 创建 `pyproject.toml` 或等价依赖清单
- 写明服务启动命令和测试命令

交付物：

- 一份简短设计文档或 README 段落
- 初始目录骨架

完成判定：

- 不再讨论“要不要一次做完全部 28 个接口”
- 团队对 MVP 边界一致
- 依赖清单可安装
- 启动命令和测试命令已落盘

### Phase 1：先搭骨架

任务：

- 创建 `app/main.py`
- 创建 `app/api/routes/health.py`
- 创建 `app/core/config.py`
- 创建 `app/core/errors.py`
- 创建 `app/core/http.py`
- 创建 `app/core/normalize.py`
- 创建 `app/schemas/common.py`
- 创建 `tests/integration/test_health.py`

必须实现：

- 服务可启动
- 健康检查接口可调用
- 统一响应 envelope
- 统一异常输出

完成判定：

- 启动服务不报错
- `GET /api/v1/health` 返回 200
- `pytest tests/integration/test_health.py` 通过

### Phase 2：先做公共能力，再做业务接口

任务：

- 在 `normalize.py` 中实现：
  - 代码归一化
  - 市场前缀
  - 腾讯 symbol
  - 东财 secid
  - 巨潮 orgId
- 在 `core/http.py` 中实现：
  - 默认 Session
  - 默认超时
  - 通用请求封装
  - 基础错误包装
- 在 `schemas/common.py` 中实现：
  - success 响应结构
  - error 响应结构
  - warning 字段

测试：

- `tests/unit/test_normalize.py`
- `tests/unit/test_response_schema.py`

完成判定：

- 代码转换规则稳定
- 巨潮 orgId 规则单测通过

### Phase 3：先打通最简单的两个接口

先做这两个：

- quote
- stock-info

原因：

- 都是高频接口
- 业务语义清晰
- 能先验证路由、Provider、Service、Schema 四层协作

任务拆解：

- `providers/tencent.py`
- `providers/eastmoney.py`
- `services/market_service.py`
- `services/fundamentals_service.py`
- `schemas/market.py`
- `schemas/fundamentals.py`
- `routes/market.py`
- `routes/fundamentals.py`

测试：

- 腾讯字段解析单测
- tencent provider mocked 测试
- eastmoney stock info mocked 测试
- quote API 集成测试
- stock-info API 集成测试

完成判定：

- `GET /api/v1/quote?codes=600519,000858` 可用
- `GET /api/v1/stock-info/600519` 可用
- 腾讯字段 43 和 46 有回归测试

### Phase 4：做估值接口

目标接口：

- `GET /api/v1/valuation/{code}`

依赖：

- 腾讯行情
- 同花顺一致预期
- 估值计算函数

任务拆解：

- `providers/ths.py`
- `domain/valuation.py`
- `domain/parsing.py`
- `services/valuation_service.py`
- `schemas/valuation.py`
- `routes/valuation.py` 或并入 `routes/market.py`

必须处理：

- 同花顺一致预期是 DataFrame，不可直接透出到 API
- eps 缺失时接口不能直接崩
- 聚合结果允许部分字段为空，但要附带 warning

测试：

- `forward_pe`
- `calc_peg`
- `pe_digestion`
- HTML 表格解析逻辑
- valuation service 测试
- valuation API 集成测试

完成判定：

- `GET /api/v1/valuation/600519` 可用
- 部分失败时返回 warnings 而不是 500

### Phase 5：做东财系列表接口

这一阶段尽量复用同一套 Eastmoney Provider 能力。

目标接口：

- `GET /api/v1/reports/{code}`
- `GET /api/v1/fund-flow/minute/{code}`
- `GET /api/v1/margin/{code}`
- `GET /api/v1/news/{code}`

任务拆解：

- 在 `providers/eastmoney.py` 中沉淀：
  - reportapi 请求
  - push2 资金流请求
  - datacenter 通用 helper
  - 个股新闻请求
- 在 service 层补齐：
  - `research_service.py`
  - `capital_service.py`
  - `news_service.py`
- 在 schemas 中补齐对应响应模型
- 在 routes 中补齐对应接口

测试：

- eastmoney datacenter helper mocked 测试
- reportapi mocked 测试
- push2 fund flow mocked 测试
- stock news mocked 测试
- 4 个 API 集成测试

完成判定：

- 上述 4 个接口可用
- 资金流明确走东财 push2
- datacenter helper 被 margin 等接口复用，而不是重复实现

### Phase 6：做公告接口

目标接口：

- `GET /api/v1/announcements/{code}`

任务拆解：

- `providers/cninfo.py`
- `services/filings_service.py`
- `schemas/filings.py`
- `routes/filings.py`

必须处理：

- orgId 生成规则
- 日期转换
- URL 组装

测试：

- cninfo provider mocked 测试
- orgId 单测
- announcementTime 转换单测
- announcements API 集成测试

完成判定：

- `GET /api/v1/announcements/600519` 可用
- orgId 规则有独立测试保护

### Phase 7：统一收口

任务：

- 检查所有接口是否统一返回 envelope
- 检查错误码和异常信息是否统一
- 检查 warnings 字段是否一致
- 检查 README 中是否新增启动方式和接口说明
- 检查配置项是否整理完毕

补充文档：

- 运行方式
- 环境变量说明
- 测试命令
- 已实现接口清单
- 暂未实现接口清单

完成判定：

- 新人可以按 README 启动服务
- 新人可以按 README 运行测试

## 4. 目录落地清单

直接照这个清单创建即可：

```text
app/
  main.py
  api/
    routes/
      health.py
      market.py
      research.py
      capital.py
      news.py
      fundamentals.py
      filings.py
  core/
    config.py
    errors.py
    http.py
    normalize.py
  schemas/
    common.py
    market.py
    valuation.py
    research.py
    capital.py
    news.py
    fundamentals.py
    filings.py
  providers/
    tencent.py
    eastmoney.py
    ths.py
    cninfo.py
  services/
    market_service.py
    valuation_service.py
    research_service.py
    capital_service.py
    news_service.py
    fundamentals_service.py
    filings_service.py
  domain/
    valuation.py
    parsing.py
tests/
  unit/
  contract/
  integration/
```

## 5. 接口清单

MVP 只做下面这些：

- `GET /api/v1/health`
- `GET /api/v1/quote?codes=600519,000858`
- `GET /api/v1/stock-info/{code}`
- `GET /api/v1/valuation/{code}`
- `GET /api/v1/reports/{code}`
- `GET /api/v1/fund-flow/minute/{code}`
- `GET /api/v1/margin/{code}`
- `GET /api/v1/news/{code}`
- `GET /api/v1/announcements/{code}`

## 6. 每个切片的固定开发循环

每完成一个切片，必须执行以下循环：

1. 先写 4 行：假设、歧义、最小切片、验证方式
2. 只实现当前切片最小代码
3. 立刻补当前切片测试
4. 先跑当前切片最小测试
5. 失败就只修当前切片
6. 修复后重跑同一组测试
7. 通过后再进入下一切片

不要这样做：

- 一次堆 5 个接口再统一测
- 测试失败后先继续开发别的功能
- 用大而泛的 except 吞掉错误
- 为单个接口提前设计通用平台抽象

如果对“什么算提前抽象、什么算可验证切片”拿不准，先看 [API_SERVICE_PROJECT_EXAMPLES.md](API_SERVICE_PROJECT_EXAMPLES.md)。

如果只是准备开工前 60 秒快速过一遍，先看 [API_SERVICE_60S_PRESTART_CHECKLIST.md](API_SERVICE_60S_PRESTART_CHECKLIST.md)。

## 7. 推荐测试命令顺序

按开发顺序跑：

```bash
pytest tests/unit/test_normalize.py
pytest tests/integration/test_health.py
pytest tests/contract/test_tencent_provider.py
pytest tests/integration/test_quote_api.py
pytest tests/contract/test_eastmoney_stock_info_provider.py
pytest tests/integration/test_stock_info_api.py
pytest tests/unit/test_valuation_domain.py
pytest tests/contract/test_ths_provider.py
pytest tests/integration/test_valuation_api.py
pytest tests/contract/test_eastmoney_provider.py
pytest tests/contract/test_cninfo_provider.py
pytest tests/integration
pytest tests/unit tests/contract tests/integration
```

如果后续配置了 lint 和类型检查，再补：

```bash
ruff check .
mypy app
```

## 8. 最关键的 6 个回归点

这 6 个点不测，MVP 就不算稳：

- 腾讯字段 43 = 振幅
- 腾讯字段 46 = PB
- 资金流必须走东财 push2
- 巨潮 stock 参数必须是 `code,orgId`
- 同花顺一致预期解析失败时，估值接口不能直接崩
- 所有接口返回结构必须统一

## 9. 任务板视图

如果要放进项目管理工具，可以直接拆成这 9 张卡：

1. 建立 FastAPI 项目骨架
2. 完成公共配置、错误、响应、代码归一化模块
3. 实现 quote 和 stock-info
4. 实现 valuation
5. 实现 reports
6. 实现 fund-flow-minute 和 margin
7. 实现 news 和 announcements
8. 补齐契约测试与集成测试
9. 更新 README、补运行说明、做最终回归

## 10. 最终验收清单

上线前逐条核对：

- 服务可以启动
- 核心 8 个接口全部可访问
- 单元测试通过
- Provider 契约测试通过
- API 集成测试通过
- README 已补启动和测试方法
- 环境变量说明完整
- 已知高风险回归点有测试覆盖
- 未做能力已明确列出，没有伪装成已完成

## 11. 一句话执行建议

把这次工作当成“先打通一条稳定主链”，不是“先铺满所有功能点”。

先把骨架、公共层、quote、stock-info、valuation 打稳，再复制同样的方法扩到东财系列表接口，MVP 会快很多，也稳很多。