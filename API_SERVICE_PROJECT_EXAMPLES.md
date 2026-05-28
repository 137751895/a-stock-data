# a-stock-data API 服务化项目专用示例

本文件提供当前项目的反例 / 正例样板。

用途：

- 看不清当前切片是不是过度设计时，先看这里
- 不确定什么叫“可验证的最小切片”时，先看这里
- 想判断自己的修改是不是已经超出了当前任务边界时，先看这里

如果只需要开工前快速自检，直接看 [API_SERVICE_60S_PRESTART_CHECKLIST.md](API_SERVICE_60S_PRESTART_CHECKLIST.md)。

---

## 1. 编码前思考

### 示例 1：把“服务化”直接理解成“一次性重写全部 28 端点”

**用户请求：** “把这个项目封装成 API 接口服务。”

**❌ 错误做法（静默假设）**

```text
我会直接：

1. 创建完整 app 目录
2. 抽出全部 38 个函数
3. 一次性实现 28 个路由
4. 加 Redis、异步任务、数据库、监控
5. 最后统一测试
```

**问题：**

- 默认假设用户要全量服务化，而不是先做 MVP
- 默认假设要一次解决缓存、异步、监控、多实例部署
- 默认假设现阶段就要处理 mootdx 和所有复杂数据源
- 没有说明最小可行切片

**✅ 正确做法（先暴露假设）**

```text
Assumptions:
- 当前目标是先把 Skill 能力服务化，而不是保留 Markdown 运行时执行
- 先做 HTTP 主链路，不先做 mootdx TCP 能力
- 先做 MVP，再扩展到 28 个端点

Ambiguities:
- 是要直接全量服务化，还是先交付可运行的核心 API？
- 是否要求首版就包含缓存 / 多实例 / 异步任务？

Simplest viable slice:
- 先建立 FastAPI 骨架
- 先打通 quote 和 stock-info
- 再做 valuation 这个聚合接口

Verify:
- health 测试通过
- quote API 测试通过
- stock-info API 测试通过
- valuation API 测试通过
```

**这里的关键：**

- 不是先把所有工作都列满
- 而是先把任务边界收窄到可以验证的一条主链

### 示例 2：遇到歧义时不区分“必须问”和“可先假设”

**用户请求：** “先做 API 服务骨架。”

**❌ 错误做法**

```text
我要先问 12 个问题，确认：
- 用 Flask 还是 FastAPI
- 要不要 Redis
- 要不要 Celery
- 要不要 Docker
- 要不要异步
- 要不要数据库
- 要不要网关
- ...
```

**问题：**

- 把不阻塞主路径的小分歧也抬成阻塞问题
- 让任务推进在最开始就停住

**✅ 正确做法**

```text
会影响主路径的分歧：
- 服务框架选型
- API 响应契约
- MVP 接口范围

不会阻塞主路径的分歧：
- 是否未来切 Redis
- 是否未来加 Docker
- 是否未来改异步 Provider

处理方式：
- 主路径分歧：在文档里明确或最小澄清
- 非阻塞分歧：先写显式假设，再继续
```

---

## 2. 简洁优先

### 示例 1：一开始就设计平台级抽象

**用户请求：** “先做 MVP API 服务。”

**❌ 错误做法（过度抽象）**

```python
class BaseProvider(ABC):
    @abstractmethod
    def build_request(self, *args, **kwargs):
        ...

    @abstractmethod
    def parse_response(self, response):
        ...


class ProviderFactory:
    def create(self, provider_name: str) -> BaseProvider:
        ...


class MarketDataRepository:
    def __init__(self, provider_factory: ProviderFactory):
        ...


class ServiceRegistry:
    def resolve(self, service_name: str):
        ...
```

**问题：**

- 当前并没有第二个真实调用点支撑这套抽象
- quote 和 stock-info 的 MVP 根本不需要平台层
- 抽象越多，测试面越大，排错越慢

**✅ 正确做法（只做当前需要的最小结构）**

```python
# providers/tencent.py
def fetch_quotes(codes: list[str]) -> dict[str, dict]:
    ...


# providers/eastmoney.py
def fetch_stock_info(code: str) -> dict:
    ...


# services/market_service.py
def get_quotes(codes: list[str]) -> dict[str, dict]:
    return fetch_quotes(codes)


# services/fundamentals_service.py
def get_stock_info(code: str) -> dict:
    return fetch_stock_info(code)
```

**什么时候再加复杂度：**

- 真的出现多个 Provider 共享同一协议拼装逻辑时
- 真的出现多种实现需要同一契约时
- 真的出现配置切换场景时

### 示例 2：为“未来扩展”提前实现缓存和异步体系

**❌ 错误做法**

```text
首版先做：
- Redis 缓存
- Celery 定时刷新
- 数据库存储
- 多实例共享状态
- 动态速率限制配置
```

**✅ 正确做法**

```text
MVP 先只做：
- 可运行 API
- 可测试的 Provider / Service / Route 主链
- 必要的 warnings 和错误结构

后续阶段再做：
- Redis
- 异步任务
- 多实例缓存
- 监控
```

**判断标准：**

如果当前新增的复杂度，不能直接帮助一个现有 MVP 接口上线或通过测试，就先不要加。

---

## 3. 精准修改

### 示例 1：做 quote 接口时顺手重构整个目录设计

**用户请求：** “先实现 quote 接口。”

**❌ 错误做法**

```diff
- 新增 quote 接口
- 顺手把所有 routes 重命名
- 顺手把 schemas 全部改成另一种命名风格
- 顺手重写 logging 模块
- 顺手调整 README 大纲
```

**问题：**

- 修改范围和用户请求不再一一对应
- 后续一旦失败，很难定位是 quote 本身还是顺手改动导致

**✅ 正确做法**

```diff
+ 新增 providers/tencent.py
+ 新增 services/market_service.py
+ 新增 schemas/market.py
+ 新增 routes/market.py 中 quote 路由
+ 新增 quote 对应单测 / 契约测试 / 集成测试
```

**只改当前需要的线：**

- quote 的 Provider
- quote 的 Service
- quote 的 Schema
- quote 的 Route
- quote 的测试

### 示例 2：修估值接口时顺手“升级”现有风格

**❌ 错误做法**

```diff
- 把已有同步 requests 全改成 async/httpx
- 把所有单引号改成双引号
- 给所有文件补 type alias 和额外 docstring
- 顺手改掉不影响 valuation 的路由命名
```

**✅ 正确做法**

```diff
  # 当前目标：让 valuation 跑通并可测试

+ 新增或补齐 ths provider
+ 新增 valuation 计算纯函数
+ 新增 DataFrame -> JSON 转换逻辑
+ 新增 valuation 路由测试
```

**判断标准：**

如果某一行改动不能直接追溯到“让 valuation 可运行 / 可测试 / 可验证”，就先不要动。

---

## 4. 目标驱动执行

### 示例 1：没有验证标准地实现完整估值

**用户请求：** “做单票估值接口。”

**❌ 错误做法**

```text
我会先把估值逻辑实现出来，然后再看看怎么测。
```

**问题：**

- 没有明确 bug / 需求是否被满足
- DataFrame 解析、空值处理、warning 机制都可能被遗漏

**✅ 正确做法（步骤 -> 验证）**

```text
Plan:
1. 写 domain 单元测试：forward_pe / calc_peg / pe_digestion
   Verify:
   - 单测先跑通

2. 写 ths 表格解析测试
   Verify:
   - 给固定 HTML 样例，能稳定提取 eps_cur / eps_next / analyst_count

3. 实现 valuation service
   Verify:
   - 当 eps 有值时，返回完整估值字段
   - 当 eps 缺失时，不报 500，而是返回 warnings

4. 接入 API 路由
   Verify:
   - GET /api/v1/valuation/600519 返回 200
   - JSON 结构符合 envelope
```

### 示例 2：全量实现后再统一跑测试

**❌ 错误做法**

```text
先把 quote、stock-info、valuation、reports、margin、news、announcements 都写完，
最后统一跑 pytest。
```

**✅ 正确做法（切片循环）**

```text
切片 1：health
- 实现
- 跑 health 集成测试

切片 2：normalize
- 实现
- 跑 normalize 单元测试

切片 3：quote
- 实现
- 跑 tencent provider 契约测试
- 跑 quote API 集成测试

切片 4：stock-info
- 实现
- 跑 eastmoney provider 契约测试
- 跑 stock-info API 集成测试
```

**关键点：**

- 每一步都能独立失败、独立修复、独立通过
- 不把 5 个失败混成 1 个大失败

---

## 5. 反模式速查表

| 原则 | 当前项目中的反模式 | 推荐替代 |
|---|---|---|
| 编码前思考 | 把“服务化”直接理解成全量重写 28 端点 | 先收窄到 MVP 主链，写清假设和验证 |
| 简洁优先 | 提前设计 BaseProvider / Factory / Repository | 先用最小 Provider + Service + Route 结构 |
| 精准修改 | 做一个接口时顺手重构所有模块 | 只改当前接口所需文件和测试 |
| 目标驱动执行 | 全部写完再统一跑 pytest | 每个切片实现后立即验证 |

## 6. 本页的正确使用方式

如果你后续用 Claude 或其他 Agent 落地实现，推荐在真正编码前先做这三步：

1. 先读 [API_SERVICE_MVP_TASK_BREAKDOWN.md](API_SERVICE_MVP_TASK_BREAKDOWN.md)，确定当前切片属于哪一阶段。
2. 再读本页对应原则下的项目示例，确认自己没有掉进当前最常见的反模式。
3. 再开始写该切片的“假设 / 歧义 / 最小切片 / 验证方式”。

本页的目标不是增加文档长度，而是减少错误开工、过度设计、顺手重构和后置验证。

如果只需要开工前短卡版本，使用 [API_SERVICE_60S_PRESTART_CHECKLIST.md](API_SERVICE_60S_PRESTART_CHECKLIST.md)。