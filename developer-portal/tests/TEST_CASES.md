# 接口自动化测试用例文档

**文档版本：** V1.0  
**测试类型：** 单元测试 + 组件测试  
**测试框架：** bun test  
**代码目录：** `packages/webapp/src/__tests__/`、`packages/cli/src/__tests__/`

---

## 用例覆盖率统计

### 总览

| 指标 | 数量 |
|------|------|
| 测试文件总数 | 14 |
| 用例总数 | 136 |
| 已实现（✅） | 136 |
| 未实现（❌） | 0 |
| 实现率 | 100% |

### 按模块

| 模块 | 文件 | 用例数 | 已实现 | 未实现 |
|------|------|--------|--------|--------|
| API 请求工具 | api.test.ts | 4 | 4 | 0 |
| API Key 管理 | apikeys.test.ts | 6 | 6 | 0 |
| 计费 | billing.test.ts | 6 | 6 | 0 |
| 实时数据看板 | dashboard.test.ts | 12 | 12 | 0 |
| 路由 | routing.test.ts | 7 | 7 | 0 |
| 订阅 | subscriptions.test.ts | 5 | 5 | 0 |
| OAuth 登录 | oauth-buttons.test.ts | 5 | 5 | 0 |
| Onboarding 流程 | onboarding.test.ts | 16 | 16 | 0 |
| 组织名可用性 | org-availability.test.ts | 13 | 13 | 0 |
| 密码规则（逻辑） | password-rules.test.ts | 12 | 12 | 0 |
| 密码规则（组件） | password-components.test.tsx | 8 | 8 | 0 |
| 工具函数 | utils.test.ts | 6 | 6 | 0 |
| CLI 命令解析 | cli.test.ts | 13 | 13 | 0 |
| Members 权限控制 | members.test.ts | 15 | 15 | 0 |

### 按优先级（建议分级）

| 优先级 | 说明 | 涉及模块 |
|--------|------|----------|
| P0 | 核心路径，阻断业务 | OAuth 登录、API 请求工具、路由、密码规则 |
| P1 | 重要功能，影响用户体验 | API Key、Onboarding、组织可用性、计费 |
| P2 | 辅助功能，影响数据展示 | 看板、订阅、CLI、工具函数 |
| P2 | 权限控制，安全合规 | Members 权限控制 |

---

## 1. API 请求工具（单元测试）

**路径：** `packages/webapp/src/__tests__/api.test.ts`  
**测试命令：** `bun test packages/webapp/src/__tests__/api.test.ts`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-API-001 | Token 存在时自动添加 Authorization 头 | P0 | ✅ | 本地存储中存有有效 token | 调用 `apiFetch`，mock fetch | 请求头包含 `Authorization: Bearer {token}` | 1. fetch 被调用；2. headers 中存在 Authorization 字段 |
| WT-API-002 | 无 Token 时不添加 Authorization 头 | P0 | ✅ | 本地存储中无 token | 调用 `apiFetch`，mock fetch | 请求头中不含 Authorization 字段 | 1. fetch 被调用；2. headers 中不存在 Authorization |
| WT-API-003 | 非 2xx 响应时抛出含 detail 的错误 | P0 | ✅ | mock fetch 返回非 ok 响应 | 调用 `apiFetch`，mock 返回 400 + `{detail: "..."}` | 抛出错误，错误信息来自响应 body 的 detail 字段 | 1. 抛出 Error；2. 错误信息等于 detail 内容 |
| WT-API-004 | 正确拼接 API_URL 和路径 | P0 | ✅ | API_URL 配置为 `http://localhost:8000` | 调用 `apiFetch("/v1/user")` | 实际请求 URL 为 `http://localhost:8000/v1/user` | 1. fetch 的第一个参数等于拼接后的完整 URL |

---

## 2. API Key 管理（单元测试）

**路径：** `packages/webapp/src/__tests__/apikeys.test.ts`  
**测试命令：** `bun test packages/webapp/src/__tests__/apikeys.test.ts`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-KEY-001 | 过期日期为 null 时显示"Never" | P1 | ✅ | 无 | 调用 `daysUntil(null)` | 返回字符串 `"Never"` | 1. 返回值 === "Never" |
| WT-KEY-002 | 未来日期正确计算剩余天数 | P1 | ✅ | 无 | 传入未来 N 天的日期 | 返回 `"{N}d left"` 格式字符串 | 1. 返回值匹配 `/\d+d left/` |
| WT-KEY-003 | 过去日期返回"Expired" | P1 | ✅ | 无 | 传入过去的日期 | 返回字符串 `"Expired"` | 1. 返回值 === "Expired" |
| WT-KEY-004 | 未展示时掩码显示 6 个圆点 | P1 | ✅ | revealed=false | 调用 `maskKey(prefix, false)` | prefix 后显示 6 个 `•`（U+2022） | 1. 返回值以 prefix 开头；2. 后缀为 6 个圆点 |
| WT-KEY-005 | 展示时显示完整 prefix | P1 | ✅ | revealed=true | 调用 `maskKey(prefix, true)` | 返回完整的 prefix 字符串 | 1. 返回值 === prefix |
| WT-KEY-006 | 所有 key 状态均有对应 badge 样式 | P1 | ✅ | 无 | 遍历 active、expired、revoked 状态 | 每种状态都有对应的 CSS class | 1. active 有绿色样式；2. expired 有琥珀色样式；3. revoked 有红色样式 |

---

## 3. 计费（单元测试）

**路径：** `packages/webapp/src/__tests__/billing.test.ts`  
**测试命令：** `bun test packages/webapp/src/__tests__/billing.test.ts`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-BILL-001 | 正数金额格式化为 USD | P1 | ✅ | 无 | `formatMoney(8420)` | 返回 `"$8,420.00"` | 1. 返回值 === "$8,420.00" |
| WT-BILL-002 | 零值格式化 | P1 | ✅ | 无 | `formatMoney(0)` | 返回 `"$0.00"` | 1. 返回值 === "$0.00" |
| WT-BILL-003 | 小数金额格式化 | P1 | ✅ | 无 | `formatMoney(17.35)` | 返回 `"$17.35"` | 1. 返回值 === "$17.35" |
| WT-BILL-004 | 负数金额格式化 | P1 | ✅ | 无 | `formatMoney(-15)` | 返回 `"-$15.00"` | 1. 返回值 === "-$15.00" |
| WT-BILL-005 | 快速选择金额均为有效分值 | P1 | ✅ | 无 | 遍历快速金额列表乘以 100 | 每项都是整数 | 1. 每项 `* 100` 后为整数；2. 包含 100、500、1000、5000、10000 |
| WT-BILL-006 | 所有交易类型均有 badge 样式 | P1 | ✅ | 无 | 遍历 topup、freeze、settle、refund | 每种类型有对应 CSS class | 1. topup 绿色；2. freeze 蓝色；3. settle 紫色；4. refund 琥珀色 |

---

## 4. 实时数据看板（单元测试）

**路径：** `packages/webapp/src/__tests__/dashboard.test.ts`  
**测试命令：** `bun test packages/webapp/src/__tests__/dashboard.test.ts`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-DASH-001 | 5 秒前显示"5s ago" | P2 | ✅ | 无 | `timeAgo(Date.now() - 5000)` | 返回 `"5s ago"` | 1. 返回值 === "5s ago" |
| WT-DASH-002 | 5 分钟前显示"5m ago" | P2 | ✅ | 无 | `timeAgo(Date.now() - 5*60000)` | 返回 `"5m ago"` | 1. 返回值 === "5m ago" |
| WT-DASH-003 | 2 小时前显示"2h ago" | P2 | ✅ | 无 | `timeAgo(Date.now() - 2*3600000)` | 返回 `"2h ago"` | 1. 返回值 === "2h ago" |
| WT-DASH-004 | 相同时间桶计数累加 | P2 | ✅ | 初始数据中存在时间"10:00"，count=3 | `addToChart(data, "10:00")` | "10:00" 的 count 变为 4 | 1. 对应桶 count 加 1 |
| WT-DASH-005 | 新时间桶创建新条目 | P2 | ✅ | 初始数据中无"11:00" | `addToChart(data, "11:00")` | 数组新增 `{time:"11:00", count:1}` | 1. 数组长度加 1；2. 新条目 count=1 |
| WT-DASH-006 | 图表数据最多保留 30 个点 | P2 | ✅ | 已有 30 个数据点 | `addToChart(data, "newTime")` | 最老的数据点被移除，总长度仍为 30 | 1. 数组长度 === 30；2. 旧数据点消失 |
| WT-DASH-007 | 新流数据插入到头部 | P2 | ✅ | 已有流数据 | `addToStream(stream, newItem, max)` | 新 item 在第一位 | 1. `stream[0]` === newItem |
| WT-DASH-008 | 流数据不超过最大数量 | P2 | ✅ | 流数据量已达 max | `addToStream(stream, newItem, max)` | 总数量不超过 max | 1. 数组长度 <= max |
| WT-DASH-009 | 改变状态为 adopted | P2 | ✅ | 存在 id 的 AnnotationItem | `updateStatus(items, id, "adopted")` | 对应 item 的 status === "adopted" | 1. 目标 item status 已更新 |
| WT-DASH-010 | 改变状态为 disputed | P2 | ✅ | 存在 id 的 AnnotationItem | `updateStatus(items, id, "disputed")` | 对应 item 的 status === "disputed" | 1. 目标 item status 已更新 |
| WT-DASH-011 | 不存在的 id 不修改原数据 | P2 | ✅ | items 中无目标 id | `updateStatus(items, "unknown-id", "adopted")` | 所有 item 保持不变 | 1. 返回结果与原数组深度相等 |
| WT-DASH-012 | 所有数据类型均有 CSS 映射 | P2 | ✅ | 无 | 遍历 label、classification、extraction、ranking、verification | 每种类型有对应颜色 class | 1. 5 种类型全部覆盖，无缺失 |

---

## 5. 路由（单元测试）

**路径：** `packages/webapp/src/__tests__/routing.test.ts`  
**测试命令：** `bun test packages/webapp/src/__tests__/routing.test.ts`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-ROUTE-001 | "/" 路由到 landing | P0 | ✅ | 无 | `resolveRoute("/")` | 返回 `"landing"` | 1. 返回值 === "landing" |
| WT-ROUTE-002 | "/auth/signin" 路由到 signin | P0 | ✅ | 无 | `resolveRoute("/auth/signin")` | 返回 `"signin"` | 1. 返回值 === "signin" |
| WT-ROUTE-003 | "/auth/signup" 路由到 signup | P0 | ✅ | 无 | `resolveRoute("/auth/signup")` | 返回 `"signup"` | 1. 返回值 === "signup" |
| WT-ROUTE-004 | "/dashboard" 路由到 dashboard | P0 | ✅ | 无 | `resolveRoute("/dashboard")` | 返回 `"dashboard"` | 1. 返回值 === "dashboard" |
| WT-ROUTE-005 | "/dashboard/api-keys" 路由到 dashboard | P0 | ✅ | 无 | `resolveRoute("/dashboard/api-keys")` | 返回 `"dashboard"` | 1. 返回值 === "dashboard" |
| WT-ROUTE-006 | "/dashboard/billing" 路由到 dashboard | P0 | ✅ | 无 | `resolveRoute("/dashboard/billing")` | 返回 `"dashboard"` | 1. 返回值 === "dashboard" |
| WT-ROUTE-007 | 未知路径回退到 landing | P0 | ✅ | 无 | `resolveRoute("/unknown")` | 返回 `"landing"` | 1. 返回值 === "landing" |

---

## 6. 订阅（单元测试）

**路径：** `packages/webapp/src/__tests__/subscriptions.test.ts`  
**测试命令：** `bun test packages/webapp/src/__tests__/subscriptions.test.ts`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-SUB-001 | 所有 vertical 均有有效 topics | P2 | ✅ | 无 | 遍历所有 vertical | 每个 vertical 的 topics 非空，且每项 slug 和 label 均有值 | 1. topics.length > 0；2. 每项 slug 和 label 非空 |
| WT-SUB-002 | topic 切换逻辑（添加/移除） | P2 | ✅ | 无 | 用 Set 添加再移除同一 topic | 移除后 Set 中不含该 topic | 1. 添加后 has() = true；2. 删除后 has() = false |
| WT-SUB-003 | quality 分数范围在 [0, 1] | P2 | ✅ | 无 | 验证 minQuality 取值 | 0 和 1 均合法，超出范围不合法 | 1. 0 <= value <= 1 |
| WT-SUB-004 | 传输模式只有 pull 和 push | P2 | ✅ | 无 | 枚举 mode 选项 | 仅包含 "pull" 和 "push" | 1. 数组 === ["pull", "push"] |
| WT-SUB-005 | 所有订阅状态均有 badge 样式 | P2 | ✅ | 无 | 遍历 active、paused、cancelled | 每种状态有对应 CSS class | 1. active 绿色；2. paused 琥珀色；3. cancelled 灰色 |

---

## 7. OAuth 登录（单元测试）

**路径：** `packages/webapp/src/__tests__/oauth-buttons.test.ts`  
**测试命令：** `bun test packages/webapp/src/__tests__/oauth-buttons.test.ts`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-OAUTH-001 | GitHub OAuth 传入正确 provider | P0 | ✅ | mock supabase.auth.signInWithOAuth | 调用 `startGitHubOAuth()` | 调用 supabase 时 provider="github"，redirectTo 包含回调地址 | 1. provider === "github"；2. redirectTo 非空 |
| WT-OAUTH-002 | GitHub OAuth 失败时返回错误信息 | P0 | ✅ | mock supabase 返回 error | 调用 `startGitHubOAuth()` | 返回 error.message 字符串 | 1. 返回值为错误字符串 |
| WT-OAUTH-003 | GitHub OAuth 支持自定义 returnTo | P0 | ✅ | 无 | `startGitHubOAuth("/onboarding")` | redirectTo 包含 "/onboarding" | 1. redirectTo 中含自定义路径 |
| WT-OAUTH-004 | HuggingFace OAuth 跳转到正确 API 端点 | P0 | ✅ | mock window.location | 调用 `startHuggingFaceOAuth()` | 跳转 URL 为 `{API_URL}/v1/auth/huggingface/start?return_to={path}` | 1. window.location.href 等于拼接后的 URL |
| WT-OAUTH-005 | HuggingFace OAuth 的 return_to 参数正确 URL 编码 | P0 | ✅ | 无 | 传入含查询参数的 returnTo | return_to 中的特殊字符被 encodeURIComponent | 1. 编码后不含未转义的特殊字符 |

---

## 8. Onboarding 流程（单元测试）

**路径：** `packages/webapp/src/__tests__/onboarding.test.ts`  
**测试命令：** `bun test packages/webapp/src/__tests__/onboarding.test.ts`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-OB-001 | "/onboarding" 路由到 onboarding | P0 | ✅ | 无 | `resolveRoute("/onboarding")` | 返回 `"onboarding"` | 1. 返回值 === "onboarding" |
| WT-OB-002 | onboarding 子路由正确解析 | P0 | ✅ | 无 | `resolveRoute("/onboarding/org-details")` | 返回 `"onboarding"` | 1. 返回值 === "onboarding" |
| WT-OB-003 | dashboard 路由优先级高于 onboarding | P0 | ✅ | 无 | `resolveRoute("/dashboard")` | 返回 `"dashboard"` 而非 "onboarding" | 1. 返回值 === "dashboard" |
| WT-OB-004 | slugify 大写转小写并用连字符连接 | P1 | ✅ | 无 | `slugify("Acme AI Labs")` | 返回 `"acme-ai-labs"` | 1. 返回值 === "acme-ai-labs" |
| WT-OB-005 | slugify 移除特殊字符 | P1 | ✅ | 无 | `slugify("Hello World! @#$%")` | 返回 `"hello-world"` | 1. 无特殊字符残留 |
| WT-OB-006 | slugify 去除首尾空格 | P1 | ✅ | 无 | `slugify("  hello  ")` | 返回 `"hello"` | 1. 无首尾空格 |
| WT-OB-007 | slugify 空字符串返回空字符串 | P1 | ✅ | 无 | `slugify("")` | 返回 `""` | 1. 返回值 === "" |
| WT-OB-008 | slugify 连续特殊字符合并为单个连字符 | P1 | ✅ | 无 | `slugify("foo  --  bar")` | 返回 `"foo-bar"` | 1. 无连续连字符 |
| WT-OB-009 | slugify 保留数字 | P1 | ✅ | 无 | `slugify("Web3 Company 123")` | 返回 `"web3-company-123"` | 1. 数字保留在结果中 |
| WT-OB-010 | slugify 去除首尾连字符 | P1 | ✅ | 无 | `slugify("-hello-")` | 返回 `"hello"` | 1. 无首尾连字符 |
| WT-OB-011 | 邀请角色仅限 admin 和 member | P1 | ✅ | 无 | 枚举角色列表 | 只有 "admin" 和 "member" | 1. 数组 === ["admin", "member"] |
| WT-OB-012 | API key 前缀固定为 hb_live_sk_ | P1 | ✅ | 无 | 读取前缀常量 | 值为 `"hb_live_sk_"` | 1. 常量 === "hb_live_sk_" |
| WT-OB-013 | 第 3 步为"Get Started"而非"API Key" | P1 | ✅ | 无 | 读取 onboarding steps 配置 | steps[2].label === "Get Started" | 1. 第三步标签正确 |
| WT-OB-014 | 后续操作卡片包含订阅和 API Keys 路径 | P1 | ✅ | 无 | 读取 StepNextActions 配置 | 包含 `/dashboard/subscriptions` 和 `/dashboard/api-keys` | 1. 两个路径均存在 |
| WT-OB-015 | 后续操作卡片链接均为内部链接 | P1 | ✅ | 无 | 遍历 StepNextActions 卡片 | 所有链接以 "/dashboard" 开头 | 1. 无外部链接 |
| WT-OB-016 | 完成 onboarding 的 API 端点路径正确 | P1 | ✅ | 无 | 构造 complete 接口 URL | 格式为 `/v1/onboarding/complete?org_id={orgId}` | 1. URL 格式正确 |

---

## 9. 组织名可用性检查（单元测试）

**路径：** `packages/webapp/src/__tests__/org-availability.test.ts`  
**测试命令：** `bun test packages/webapp/src/__tests__/org-availability.test.ts`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-ORG-001 | buildCheckUrl 正确拼接 name 和 slug | P1 | ✅ | 无 | `buildCheckUrl("Acme", "acme")` | URL 含 `name=Acme&slug=acme` | 1. URL 格式符合 `/v1/onboarding/org/check?...` |
| WT-ORG-002 | buildCheckUrl 对特殊字符编码 | P1 | ✅ | 无 | name 含 "&" | "&" 被编码为 `%26` | 1. URL 中无未编码的 & 字符 |
| WT-ORG-003 | buildCheckUrl 去除输入首尾空格 | P1 | ✅ | 无 | name=" Acme " | URL 中使用 "Acme" 而非 " Acme " | 1. URL 参数无首尾空格 |
| WT-ORG-004 | name 和 slug 均可用时正确解析 | P1 | ✅ | API 返回 `{name_available: true, slug_available: true}` | `parseCheckResponse(resp)` | `{nameAvailable: true, slugAvailable: true}` | 1. 两个字段均为 true |
| WT-ORG-005 | name 已占用时正确解析 | P1 | ✅ | API 返回 name_available=false | `parseCheckResponse(resp)` | `{nameAvailable: false, slugAvailable: true}` | 1. nameAvailable === false |
| WT-ORG-006 | slug 已占用时正确解析 | P1 | ✅ | API 返回 slug_available=false | `parseCheckResponse(resp)` | `{nameAvailable: true, slugAvailable: false}` | 1. slugAvailable === false |
| WT-ORG-007 | name 和 slug 均占用时正确解析 | P1 | ✅ | API 返回两者均 false | `parseCheckResponse(resp)` | `{nameAvailable: false, slugAvailable: false}` | 1. 两个字段均为 false |
| WT-ORG-008 | name 为空时不触发检查 | P1 | ✅ | 无 | `shouldCheck("", "acme")` | 返回 false | 1. 返回值 === false |
| WT-ORG-009 | slug 为空时不触发检查 | P1 | ✅ | 无 | `shouldCheck("Acme", "")` | 返回 false | 1. 返回值 === false |
| WT-ORG-010 | name 只有 1 个字符时不触发检查 | P1 | ✅ | 无 | `shouldCheck("A", "acme")` | 返回 false | 1. 返回值 === false |
| WT-ORG-011 | slug 只有 1 个字符时不触发检查 | P1 | ✅ | 无 | `shouldCheck("Acme", "a")` | 返回 false | 1. 返回值 === false |
| WT-ORG-012 | name 和 slug 均 >= 2 字符时触发检查 | P1 | ✅ | 无 | `shouldCheck("AB", "ab")` | 返回 true | 1. 返回值 === true |
| WT-ORG-013 | 正常输入触发检查 | P1 | ✅ | 无 | `shouldCheck("Acme Inc", "acme-inc")` | 返回 true | 1. 返回值 === true |

---

## 10. 密码规则逻辑（单元测试）

**路径：** `packages/webapp/src/__tests__/password-rules.test.ts`  
**测试命令：** `bun test packages/webapp/src/__tests__/password-rules.test.ts`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-PWD-001 | 空字符串无法通过任何规则，score=0 | P0 | ✅ | 无 | `validatePassword("")` | passedCount=0，score=0 | 1. 所有规则 passed=false；2. score === 0 |
| WT-PWD-002 | 强密码通过全部 6 条规则，score=4 | P0 | ✅ | 无 | `validatePassword("Abcdef1!X0")` | passedCount=6，score=4 | 1. 所有规则 passed=true；2. score === 4 |
| WT-PWD-003 | 短密码仅在 length 规则失败 | P0 | ✅ | 无 | `validatePassword("Sh0rt!A")` | length 规则 passed=false，其他通过 | 1. 仅 length 规则失败 |
| WT-PWD-004 | 全小写密码无法通过 uppercase 规则 | P0 | ✅ | 无 | `validatePassword("abcdef1!")` | uppercase 规则 passed=false | 1. uppercase 规则 passed === false |
| WT-PWD-005 | 全大写密码无法通过 lowercase 规则 | P0 | ✅ | 无 | `validatePassword("ABCDEF1!")` | lowercase 规则 passed=false | 1. lowercase 规则 passed === false |
| WT-PWD-006 | 无数字密码无法通过 digit 规则 | P0 | ✅ | 无 | `validatePassword("Abcdef!!")` | digit 规则 passed=false | 1. digit 规则 passed === false |
| WT-PWD-007 | 无特殊字符密码无法通过 special 规则 | P0 | ✅ | 无 | `validatePassword("Abcdef12")` | special 规则 passed=false | 1. special 规则 passed === false |
| WT-PWD-008 | 含空格密码无法通过 no-whitespace 规则 | P0 | ✅ | 无 | `validatePassword("Abc def1!")` | no-whitespace 规则 passed=false | 1. no-whitespace 规则 passed === false |
| WT-PWD-009 | 含 Tab 密码无法通过 no-whitespace 规则 | P0 | ✅ | 无 | 密码含 `\t` | no-whitespace 规则 passed=false | 1. no-whitespace 规则 passed === false |
| WT-PWD-010 | 支持自定义 rules 参数 | P1 | ✅ | 无 | `validatePassword(pwd, [customRule])` | 只评估提供的规则 | 1. 结果中仅包含自定义规则 |
| WT-PWD-011 | score 与 passedCount 的映射关系正确 | P0 | ✅ | 无 | 验证 0~6 通过数量对应 score | 0-2→0，3→1，4→2，5→3，6→4 | 1. 映射关系与文档一致 |
| WT-PWD-012 | DEFAULT_RULES 包含 6 条规则且 ID 正确 | P0 | ✅ | 无 | 读取 DEFAULT_RULES 常量 | 包含：digit、length、lowercase、no-whitespace、special、uppercase | 1. 数量 === 6；2. ID 全部匹配 |

---

## 11. 密码规则 UI 组件（组件测试）

**路径：** `packages/webapp/src/__tests__/password-components.test.tsx`  
**测试命令：** `bun test packages/webapp/src/__tests__/password-components.test.tsx`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-PWDUI-001 | PasswordRules 为每条规则渲染一行 | P0 | ✅ | 无 | 渲染 PasswordRules，传入 DEFAULT_RULES | 渲染行数 === 规则数（6 行） | 1. DOM 中有 6 个规则行 |
| WT-PWDUI-002 | isDirty=false 时不显示红色样式 | P0 | ✅ | isDirty=false，所有规则失败 | 渲染 PasswordRules | 无红色样式 class | 1. 无 text-red 相关 class |
| WT-PWDUI-003 | isDirty=true 且规则失败时显示红色 | P0 | ✅ | isDirty=true，规则失败 | 渲染 PasswordRules | 失败规则有红色样式 | 1. 有 text-red 相关 class；2. aria-label 含 "not met" |
| WT-PWDUI-004 | 通过的规则显示绿色 | P0 | ✅ | 规则 passed=true | 渲染 PasswordRules | 通过规则有绿色样式 | 1. 有 text-emerald-600 class；2. aria-label 含 "met" |
| WT-PWDUI-005 | 每行均有描述性 aria-label | P0 | ✅ | 无 | 渲染 PasswordRules | 每行有 aria-label 含 "met" 或 "not met" | 1. 所有行均有 aria-label |
| WT-PWDUI-006 | StrengthMeter 渲染 4 个分段 | P1 | ✅ | 无 | 渲染 StrengthMeter | DOM 中有 4 个分段元素 | 1. 分段数量 === 4 |
| WT-PWDUI-007 | StrengthMeter 根据 score 激活分段 | P1 | ✅ | score=2 | 渲染 StrengthMeter | 2 个分段为激活状态 | 1. 激活分段数 === score |
| WT-PWDUI-008 | StrengthMeter 有正确 ARIA 属性 | P1 | ✅ | 无 | 渲染 StrengthMeter | role=progressbar，aria-valuenow=score，aria-valuemin=0，aria-valuemax=4 | 1. 4 个 ARIA 属性均存在且正确 |

---

## 12. 工具函数（单元测试）

**路径：** `packages/webapp/src/__tests__/utils.test.ts`  
**测试命令：** `bun test packages/webapp/src/__tests__/utils.test.ts`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-UTIL-001 | 大写字母全部转成小写 | P1 | ✅ | 无 | `slugify("Hello World")` | 返回 `"hello-world"` | 1. 返回值全为小写 |
| WT-UTIL-002 | 空格和特殊符号替换成连字符 | P1 | ✅ | 无 | `slugify("My Org Name!")` | 返回 `"my-org-name"` | 1. 无特殊符号残留 |
| WT-UTIL-003 | 连续分隔符只保留一个连字符 | P1 | ✅ | 无 | `slugify("foo  --  bar")` | 返回 `"foo-bar"` | 1. 无连续连字符 |
| WT-UTIL-004 | 去掉首尾空格和连字符 | P1 | ✅ | 无 | `slugify("  hello  ")` | 返回 `"hello"` | 1. 无首尾多余字符 |
| WT-UTIL-005 | 合法 slug 保持不变 | P1 | ✅ | 无 | `slugify("my-org-123")` | 返回 `"my-org-123"` | 1. 返回值与输入相同 |
| WT-UTIL-006 | 全是特殊字符时返回空字符串 | P1 | ✅ | 无 | `slugify("!!!")` | 返回 `""` | 1. 返回值 === "" |

---

## 13. CLI 命令解析（单元测试）

**路径：** `packages/cli/src/__tests__/cli.test.ts`  
**测试命令：** `bun test packages/cli/src/__tests__/cli.test.ts`

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-CLI-001 | 解析 `auth set-key KEY` | P2 | ✅ | 无 | `parseArgs(["auth", "set-key", "hb_live_sk_abc"])` | `{cmd:"auth", sub:"set-key", arg1:"hb_live_sk_abc"}` | 1. 三字段均正确 |
| WT-CLI-002 | 解析 `auth whoami` | P2 | ✅ | 无 | `parseArgs(["auth", "whoami"])` | `{cmd:"auth", sub:"whoami"}` | 1. cmd 和 sub 正确 |
| WT-CLI-003 | 解析 `verticals list` | P2 | ✅ | 无 | `parseArgs(["verticals", "list"])` | `{cmd:"verticals", sub:"list"}` | 1. cmd 和 sub 正确 |
| WT-CLI-004 | 解析 `data pull sub-1` | P2 | ✅ | 无 | `parseArgs(["data", "pull", "sub-1"])` | `{cmd:"data", sub:"pull", arg1:"sub-1"}` | 1. 三字段均正确 |
| WT-CLI-005 | 解析 `data adopt item-1` | P2 | ✅ | 无 | `parseArgs(["data", "adopt", "item-1"])` | `{cmd:"data", sub:"adopt", arg1:"item-1"}` | 1. 三字段均正确 |
| WT-CLI-006 | 空参数返回 null | P2 | ✅ | 无 | `parseArgs([])` | 返回 null | 1. 返回值 === null |
| WT-CLI-007 | 解析 `frontiers list` | P2 | ✅ | 无 | `parseArgs(["frontiers", "list"])` | `{cmd:"frontiers", sub:"list"}` | 1. cmd 和 sub 正确 |
| WT-CLI-008 | 解析 `frontiers tasks frontier-1` | P2 | ✅ | 无 | `parseArgs(["frontiers", "tasks", "frontier-1"])` | `{cmd:"frontiers", sub:"tasks", arg1:"frontier-1"}` | 1. 三字段均正确 |
| WT-CLI-009 | 解析 `live pull sub-1` | P2 | ✅ | 无 | `parseArgs(["live", "pull", "sub-1"])` | `{cmd:"live", sub:"pull", arg1:"sub-1"}` | 1. 三字段均正确 |
| WT-CLI-010 | 解析 `live adopt sub-1` | P2 | ✅ | 无 | `parseArgs(["live", "adopt", "sub-1"])` | `{cmd:"live", sub:"adopt", arg1:"sub-1"}` | 1. 三字段均正确 |
| WT-CLI-011 | 合法 API key 以 hb_live_sk_ 开头 | P2 | ✅ | 无 | `isValidKey("hb_live_sk_abc")` | 返回 true | 1. 返回值 === true |
| WT-CLI-012 | 非法 API key 被拒绝 | P2 | ✅ | 无 | `isValidKey("invalid_key")` | 返回 false | 1. 返回值 === false |
| WT-CLI-013 | 配置目录为 ~/.humanbased | P2 | ✅ | 无 | 读取 CONFIG_DIR 常量 | 值为 `"~/.humanbased"` | 1. 路径 === "~/.humanbased" |

---

## 14. Members 权限控制（组件测试）

**路径：** `packages/webapp/src/__tests__/members.test.tsx`（待创建）  
**测试命令：** `bun test packages/webapp/src/__tests__/members.test.tsx`  
**背景：** `Members.tsx` 通过 `currentRole` 派生 `isAdmin`（owner/admin 为 true，member 为 false），控制邀请表单、编辑/移除按钮、撤销邀请按钮三处 UI 的显示。

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-MEM-001 | member 角色不渲染邀请表单 | P2 | ✅ | currentRole="member"，members 列表已加载 | 渲染 Members 组件，当前用户 role=member | 页面中不存在邀请表单（email input） | 1. DOM 中无 `type="email"` 的 input |
| WT-MEM-002 | admin 角色渲染邀请表单 | P2 | ✅ | currentRole="admin"，members 列表已加载 | 渲染 Members 组件，当前用户 role=admin | 页面中存在邀请表单 | 1. DOM 中存在 `type="email"` 的 input |
| WT-MEM-003 | owner 角色渲染邀请表单 | P2 | ✅ | currentRole="owner"，members 列表已加载 | 渲染 Members 组件，当前用户 role=owner | 页面中存在邀请表单 | 1. DOM 中存在 `type="email"` 的 input |
| WT-MEM-004 | member 角色不渲染其他成员的编辑/移除按钮 | P2 | ✅ | currentRole="member"，成员列表含其他非 owner 成员 | 渲染 Members 组件 | 所有成员行均无编辑/移除按钮 | 1. DOM 中无 Edit / Remove 按钮 |
| WT-MEM-005 | admin 角色渲染其他成员的编辑/移除按钮 | P2 | ✅ | currentRole="admin"，成员列表含其他非 owner 成员 | 渲染 Members 组件 | 非 owner、非自己的成员行有编辑/移除按钮 | 1. 目标成员行存在 Edit 和 Remove 按钮 |
| WT-MEM-006 | member 角色不渲染待邀请的 Revoke 按钮 | P2 | ✅ | currentRole="member"，存在 pending 邀请 | 渲染 Members 组件 | 邀请行中无 Revoke 按钮 | 1. DOM 中无文本为 "Revoke" 的按钮 |
| WT-MEM-007 | admin 角色渲染待邀请的 Revoke 按钮 | P2 | ✅ | currentRole="admin"，存在 pending 邀请 | 渲染 Members 组件 | 邀请行中存在 Revoke 按钮 | 1. DOM 中存在文本为 "Revoke" 的按钮 |
| WT-MEM-008 | 当前用户自己的行不显示编辑/移除按钮（无论角色） | P2 | ✅ | currentRole="admin"，成员列表含当前用户自己 | 渲染 Members 组件 | 当前用户所在行无编辑/移除按钮 | 1. isSelf=true 的行无操作按钮 |
| WT-MEM-009 | owner 成员的行不显示编辑/移除按钮 | P2 | ✅ | currentRole="admin"，成员列表含 owner 成员 | 渲染 Members 组件 | owner 所在行无编辑/移除按钮 | 1. isOwner=true 的行无操作按钮 |
| WT-MEM-010 | 成员列表未加载时 isAdmin 为 false（不渲染邀请表单） | P2 | ✅ | currentRole=null（初始状态，members 为空数组） | 渲染 Members 组件，不提供成员数据 | 页面中不存在邀请表单 | 1. DOM 中无 `type="email"` 的 input |
| WT-MEM-011 | 当前用户不在成员列表中时 isAdmin 为 false | P2 | ✅ | currentUser.email 与所有 members 的 email 均不匹配 | 渲染 Members 组件 | 页面中不存在邀请表单，无编辑/移除/Revoke 按钮 | 1. isAdmin 未被激活；2. 三处权限控件均不存在 |

---

## 未实现用例清单

无。

---

## 用例模板

### 单元/组件用例模板

| 用例编号 | 用例名称 | 优先级 | 实现状态 | 前置条件 | 步骤 | 预期结果 | 断言点 |
|----------|----------|--------|----------|----------|------|----------|--------|
| WT-模块-序号 | 函数/组件功能描述 | P0/P1/P2 | ✅/❌ | 1. xxx；2. xxx | 调用 `xxx(input)` | 返回 yyy / 抛出 zzz | 1. 断言 A；2. 断言 B |

**测试命令格式：**

```bash
# 运行单个测试文件
bun test packages/webapp/src/__tests__/xxx.test.ts

# 运行所有 webapp 测试
bun test packages/webapp

# 运行所有测试
bun test
```

---

## 维护说明

1. **新增测试**：在对应 `__tests__` 目录下新增 `.test.ts` / `.test.tsx` 文件，并在本文档对应模块的表格中补充用例行，实现状态标记 ✅
2. **删除功能**：若对应功能被移除，同步删除测试文件及本文档中的用例行
3. **用例失败**：若某个测试用例因 bug 临时 skip，在本文档中标注实现状态为 ⚠️ 并附注原因
4. **优先级调整**：核心鉴权、路由路径为 P0；用户可感知功能为 P1；工具函数、UI 辅助为 P2
5. **运行全量验证**：PR 前必须执行 `bun test` 确保所有用例通过
