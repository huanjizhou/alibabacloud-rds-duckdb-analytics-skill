---
name: alibabacloud-rds-duckdb-analytics
description: >-
 Natural language data analytics for Alibaba Cloud RDS DuckDB instances. Provides text-to-SQL
 query generation, ARIMA/linear regression prediction, query history persistence, and OpenClaw
 cron scheduling. Use when user mentions: DuckDB 分析，数据查询，自然语言问数，DuckDB 预测，
 数据分析，text-to-sql, /duckdb, 查询记录，预测分析，DuckDB 定时任务.
metadata: { "openclaw": { "emoji": "🦆", "requires": { "bins": ["python3"] }, "homepage": "https://github.com/huanjizhou/alibabacloud-rds-duckdb-analytics-skill" } }
---

# Alibaba Cloud RDS DuckDB 数据分析技能

本技能采用「主 Agent + 子 Agent」协作协议，为 RDS DuckDB 用户提供自然语言问数、预测分析和定时任务能力。

## 协议约定

- **主 Agent**：负责命令分发、用户交互、状态流转
- **子 Agent**：负责环境检查、SQL 生成与执行、预测分析、定时任务配置
- 所有回复**必须严格遵循**下方定义的回复模板
- 模板中 `{variable}` 为占位符，替换为实际值

## 命令体系

| 命令 | 功能 |
|------|------|
| `/duckdb 分析 <描述>` | 自然语言生成 SQL 并执行 |
| `/duckdb 问数 <ID 或关键词>` | 重用历史查询 |
| `/duckdb 运行预测 <描述>` | 创建并执行预测任务 |
| `/duckdb 记录 [类型] [日期]` | 查看查询/预测历史 |
| `/duckdb 配置 [子命令]` | 管理连接配置 |

详细命令参数见 [references/commands.md](references/commands.md)。

## 安装方式

用户需要先将本技能安装到 OpenClaw 中（告知用户以下任一方式）：

```bash
# 方式 1：复制到 workspace skills 目录
cp -r alibabacloud-rds-duckdb-analytics-skill ~/.openclaw/workspace/skills/

# 方式 2：clone 到 skills 目录
cd ~/.openclaw/workspace/skills && git clone https://github.com/huanjizhou/alibabacloud-rds-duckdb-analytics-skill
```

安装后 OpenClaw 自动发现该技能，用户发送任意 `/duckdb` 命令即可开始使用。

## 前置检查规则（重要）

**每次**收到 `/duckdb` 相关命令时，必须按以下顺序前置检查：

1. **检查依赖**：执行 `bash {baseDir}/scripts/check_dependencies.sh`
   - 未通过 → 进入 Phase A（A1 场景），完成后继续
2. **检查 .env**：确认 `{baseDir}/.env` 存在且包含必要字段
   - 不存在 → 进入 Phase A（A2 场景），完成后继续
3. **测试连接**：执行 `python3 {baseDir}/scripts/read_config.py --env-file {baseDir}/.env`
   - 失败 → 进入 Phase A（A3 场景），完成后继续

**全部通过后**，再根据用户命令分发到对应 Phase。

如果环境已就绪（此前已通过检查），可跳过前置检查，直接分发命令。

## 工作流程总览

```
[用户发送 /duckdb 命令]
 │
 ▼
前置检查 ─── 依赖？─✗──→ Phase A（A1: 自动安装）──→ 重新检查
 │ │
 ✓ │
 ├─── .env? ──✗──→ Phase A（A2: 引导配置）──→ 重新检查 │
 │ │
 ✓ │
 ├─── 连接？─✗──→ Phase A（A3: 排查连接）──→ 重新检查 │
 │ │
 ✓ 全部通过 ←──────────────────────────────────────────┘
 │
 ▼
命令分发 ──┬─ /duckdb 分析 → Phase B（数据分析）
 ├─ /duckdb 问数 → Phase B-2（查询复用）
 ├─ /duckdb 运行预测 → Phase C（预测分析）
 ├─ /duckdb 记录 → Phase D（查看记录）
 └─ /duckdb 配置 → Phase A（重新配置）
```

---

## Phase A：环境与连接配置

**执行者**：子 Agent `env-setup`

### 步骤

1. 执行 `bash {baseDir}/scripts/check_dependencies.sh`，检查 Python 及依赖包
2. 检查 `{baseDir}/.env` 是否存在且包含必要连接信息
3. 测试数据库连接：`python3 {baseDir}/scripts/read_config.py --env-file {baseDir}/.env`

### 回复模板

**A1 — 依赖未安装**

严格回复：

```
🔧 环境检查结果

❌ 缺少必要依赖

是否授权我为您自动安装？（是/否）
```

用户回答「是」后自动执行 `bash {baseDir}/scripts/install_dependencies.sh`，完成后重新检查。

**A2 — .env 未配置**

严格回复：

```
🔧 环境检查结果

✅ 依赖已就绪
❌ 未检测到数据库连接配置

请提供 DuckDB 连接信息：
  1. 实例地址（如：rm-xxx.duckdb.rds.aliyuncs.com）
  2. 端口
  3. 用户名
  4. 密码
  5. 数据库名

您可以直接回复以上信息，或编辑 {baseDir}/.env 文件后告诉我。
```

收到信息后写入 `.env` 文件并测试连接。

**A3 — 连接失败**

严格回复：

```
🔧 连接测试

❌ 连接失败
 错误信息：{error_message}

请检查：
 • 实例地址和端口是否正确
 • 用户名和密码是否正确
 • 网络是否可达（白名单是否已添加）

修改后请告诉我，我将重新测试。
```

**A4 — 环境就绪**

严格回复：

```
🔧 环境检查结果

✅ 依赖已就绪
✅ 数据库连接成功（{database}@{host}）

您现在可以使用以下命令：
 • /duckdb 分析 <问题描述> — 自然语言查询
 • /duckdb 运行预测 <目标> — 预测分析
 • /duckdb 记录 — 查看历史
```

---

## Phase B：数据分析（/duckdb 分析）

**执行者**：子 Agent `query-runner`

### 步骤

1. 解析用户自然语言描述
2. 生成 SQL：`python3 {baseDir}/scripts/generate_sql.py --query "{用户描述}" --env-file {baseDir}/.env`
3. 展示 SQL 并等待用户确认
4. 确认后执行：`python3 {baseDir}/scripts/execute_query.py --env-file {baseDir}/.env`
5. 保存查询记录

### 回复模板

**B1 — SQL 确认**

严格回复：

```
📊 数据分析

【生成 SQL】

{generated_sql}

请确认：
 • 回复「确认」→ 执行查询
 • 回复「修改 XXX」→ 调整 SQL
 • 回复「取消」→ 取消本次分析
```

**B2 — 查询成功**

严格回复：

```
📊 查询结果

✅ 执行完成（{execution_time_ms}ms）
✅ 返回 {row_count} 行数据

【结果摘要】
{对查询结果进行关键指标汇总}

【记录保存】
✅ 已保存：{query_id}
✅ 可通过 /duckdb 问数 {short_keyword} 复用此查询

接下来可以：
 • 回复「查看明细」→ 展示完整数据
 • 回复「每天自动执行」→ 配置为定时任务
 • 发送新请求 → 开始新的分析
```

**B3 — 查询失败**

严格回复：

```
📊 查询结果

❌ 执行失败
 错误信息：{error_message}

可能原因：
 • 表名或字段名不存在
 • SQL 语法错误

回复「修改」可调整 SQL 后重试。
```

### Phase B-2：查询复用（/duckdb 问数）

从 `records/queries/` 中按 ID 或关键词匹配历史查询，找到后直接执行并展示结果（使用 B2 模板）。未找到严格回复：

```
📊 查询复用

❌ 未找到匹配的查询记录：{keyword}

使用 /duckdb 记录 查看所有可用记录。
```

---

## Phase C：预测分析（/duckdb 运行预测）

**执行者**：子 Agent `prediction-runner`

### 步骤

1. 解析预测目标
2. 生成预测方案：`python3 {baseDir}/scripts/generate_prediction.py --target "{目标}" --env-file {baseDir}/.env`
3. 展示方案并等待确认
4. 确认后执行：`python3 {baseDir}/scripts/run_prediction.py --env-file {baseDir}/.env`

### 回复模板

**C1 — 预测方案确认**

严格回复：

```
📈 预测分析

【预测方案】
 • 预测目标：{target}
 • 模型类型：{model}（ARIMA / 线性回归）
 • 数据范围：{data_range}
 • 预测周期：{periods}

请确认：
 • 回复「确认」→ 执行预测
 • 回复「修改 XXX」→ 调整参数
 • 回复「取消」→ 取消
```

**C2 — 预测成功**

严格回复：

```
📈 预测结果

✅ 预测完成
 • 预测 ID：{prediction_id}
 • 模型：{model}

【预测摘要】
{预测结果的关键趋势和数值}

【记录保存】
✅ 预测脚本已保存，可通过 /duckdb 运行预测 {prediction_id} 重新执行

是否配置为定时任务？（是/否）
```

用户回答「是」→ 进入 Phase E。

**C3 — 预测失败**

严格回复：

```
📈 预测结果

❌ 预测失败
 错误信息：{error_message}

可能原因：
 • 历史数据不足（至少需要 30 条）
 • 数据格式不符合模型要求

建议：
 • 增加数据范围
 • 尝试更换模型：回复「修改 模型 linear_regression」
```

---

## Phase D：查看记录（/duckdb 记录）

**执行者**：子 Agent `record-viewer`

读取 `records/` 目录下的查询和预测记录。

### 回复模板

**D1 — 记录列表**

严格回复：

```
📜 历史记录（{date}）

【查询记录】
{按时间倒序列出，每条一行}
 {序号}. {query_id} — {natural_language}（{row_count} 行，{execution_time_ms}ms）

【预测记录】
{按时间倒序列出}
 {序号}. {prediction_id} — {target}（{model}）

共 {total} 条记录。可用 /duckdb 问数 <ID> 复用查询。
```

**D2 — 无记录**

严格回复：

```
📜 历史记录

暂无记录。使用 /duckdb 分析 <问题> 开始您的第一次查询。
```

---

## Phase E：配置定时任务

**执行者**：子 Agent `cron-scheduler`

### 步骤

1. 收集调度参数（频率、时间）
2. 配置 OpenClaw cron

### 回复模板

**E1 — 收集参数**

严格回复：

```
⏰ 定时任务配置

请告诉我您期望的执行方案：
 1. 执行频率：每天 / 每周 / 每月
 2. 执行时间：如 08:00
 3. 如选每周，请指定星期几

示例：「每天早上 8:00 执行」
```

**E2 — 配置完成**

根据用户回答生成 cron 表达式，写入 `~/.openclaw/openclaw.json`：

```json
{
 "agents": {
 "duckdb-prediction-cron": {
 "cron": "{cron_expression}",
 "message": "执行 DuckDB 预测任务：python3 {baseDir}/scripts/run_prediction.py --prediction-id {prediction_id} --env-file {baseDir}/.env",
 "skill": "alibabacloud-rds-duckdb-analytics"
 }
 }
}
```

严格回复：

```
✅ 定时任务配置完成！

📋 配置摘要：
 • 任务：{prediction_target}
 • 频率：{frequency}
 • 执行时间：{time}
 • Cron 表达式：{cron_expression}

🔄 下次执行时间：{next_run_time}

如需修改配置，随时告诉我。
```

---

## 持久化记录

所有查询和预测自动保存到 `{baseDir}/records/`：

```
records/
├── queries/ # SQL 查询记录
│ └── YYYY-MM-DD/
│ └── query_{timestamp}_{hash}.json
└── predictions/ # 预测分析记录
 └── YYYY-MM-DD/
 ├── pred_{id}.json # 预测配置
 ├── pred_{id}.py # 预测脚本
 └── results/ # 执行结果
```

---

## 参考文档

- 命令详细参数与确认流程：[references/commands.md](references/commands.md)
- 连接配置说明：[references/configuration.md](references/configuration.md)
- 脚本使用参考：[references/scripts.md](references/scripts.md)
- 持久化记录格式：[references/record_format.md](references/record_format.md)
- 故障排查指南：[references/troubleshooting.md](references/troubleshooting.md)
