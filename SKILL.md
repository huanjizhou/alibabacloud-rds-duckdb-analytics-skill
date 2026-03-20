---
name: alibabacloud-rds-duckdb-analytics
description: >-
 阿里云 RDS DuckDB 自然语言数据分析：text-to-SQL、多版本预测、定时任务。
 触发词：/duckdb, DuckDB 分析, 数据查询, 预测分析.
metadata: { "openclaw": { "emoji": "🦆", "requires": { "bins": ["python3", "pip3", "aliyun"] }, "homepage": "https://github.com/huanjizhou/alibabacloud-rds-duckdb-analytics-skill" } }
---

# Alibaba Cloud RDS DuckDB 数据分析技能

本技能采用「主 Agent + 子 Agent」协作协议，为 RDS DuckDB 用户提供自然语言问数、预测分析和定时任务能力。

## 协议约定

- **主 Agent**：负责命令分发、交互与状态流转
- **子 Agent**：负责环境检查、SQL 执行、预测与定时任务
- 所有回复**必须严格遵循**下方定义的回复模板

## 功能支持概览

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| SQL 查询 | ✅ | 自然语言转 SQL，在 RDS DuckDB FDW 执行 |
| 多模型预测 | ✅ | 多基线模型竞技 + Plus/Pro 版本进化支持 |
| 数据清洗 | ✅ | 深度分析前结构化排查空值与重复项 |
| 报告生成 | ✅ | 自动汇总评估结果输出标准 Markdown 报告 |
| 数据可视化 | ✅ | 内置 ASCII 趋势图表控制台原生绘制能力 |

## 命令体系

| 命令 | 功能 |
|------|------|
| `/duckdb 分析 <描述>` | 自然语言生成 SQL 并执行 |
| `/duckdb 问数 <ID 或关键词>` | 重用历史查询 |
| `/duckdb 运行预测 <描述>` | 创建并执行预测任务（支持多版本） |
| `/duckdb 记录 [类型] [日期]` | 查看查询/预测历史 |
| `/duckdb 配置 [子命令]` | 管理连接配置、版本切换 |

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

默认安装 Basic 版依赖（`pip3 install -r requirements-basic.txt`）。如需预测增强版本（Plus/Pro），见下方 Phase C 的「多版本架构」章节。

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
  前置检查 ── 依赖？ ─✗─→ Phase A（A1: 自动安装）─┐
       │                                           │
       ✓                                           │
       ├── .env？ ─✗─→ Phase A（A2: 引导配置）─────┤
       │                                           │
       ✓                                           │
       ├── 连接？ ─✗─→ Phase A（A3: 排查连接）─────┤
       │                                           │
       ✓ 全部通过 ←────────────────────────────────┘
       │
       ▼
  命令分发 ─┬─ /duckdb 分析     → Phase B（数据分析）
            ├─ /duckdb 问数     → Phase B-2（查询复用）
            ├─ /duckdb 运行预测 → Phase C（预测分析）
            ├─ /duckdb 记录     → Phase D（查看记录）
            └─ /duckdb 配置     → Phase A（重新配置）
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
  1. 实例地址（如：rm-xxx.mysql.rds.aliyuncs.com）
     ⚠️ 推荐使用公网地址，避免内网连接问题
  2. 端口
  3. 用户名
  4. 密码
  5. 数据库名

您可以直接回复以上信息，或编辑 {baseDir}/.env 文件后告诉我。
```

收到信息后写入 `.env` 文件并测试连接。

**A3 — 连接失败**

严格回复（连接超时或失败）：

```
🔧 连接测试

❌ 连接失败
 错误信息：{error_message}

请检查：
 • 实例地址和端口是否正确
 • 用户名和密码是否正确
 • 网络是否可达（白名单是否已添加）

【自动修复】
检测到可能是白名单问题，是否授权我自动将本机 IP 加入实例白名单？
 • 回复「是」→ 自动配置白名单（需要阿里云 CLI 授权）
 • 回复「否」→ 手动配置（见下方说明）

【手动配置白名单】
1. 登录阿里云 RDS 控制台
2. 进入实例详情页 → 白名单设置
3. 添加本机公网 IP：{local_ip}
4. 保存后回复「已配置」，我将重新测试
```

用户回答「是」后，执行以下命令自动添加白名单：
```bash
python3 {baseDir}/scripts/fix_whitelist.py \
  --instance-id {instance_id} \
  --region {region} \
  --env-file {baseDir}/.env \
  --test-connection
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

## Phase B：高级数据查验与分析（/duckdb 分析）

**执行者**：子 Agent `query-runner`

本阶段包含两步核心操作：**1.数据查验（清洗审核）** → **2.专业商业分析**

### 步骤 1：数据查验（Data Quality Audit）

在进行任何深度分析或预测前，如果用户未提供清洗好的数据视图，Agent **必须主动**先执行查询获取表的质量概况。
1. Agent **自行通过 `execute_query.py --sql "<SQL>"`** 执行质量稽查（如查询空值数量、异常极值、重复行）。
2. 在最终分析前输出简要的【数据体检报告】给用户。

### 步骤 2：专业商业分析执行

Agent 应根据用户需求，使用专业的商业分析思维，**自主编写高级 SQL**。
*不要局限于 `generate_sql.py` 的基础规则，鼓励 Agent 给子 Agent 发送复杂的探索性分析 SQL（如：漏斗分析、同期群分析、同环比分析等）*。

1. Agent 分析查验结果并根据自然语言直接构造最合适的 SQL 语句。
2. 展示构造的 SQL 给用户确认。
3. 执行：`python3 {baseDir}/scripts/execute_query.py --sql "{SQL}" --env-file {baseDir}/.env`
4. 将返回的查询结果分析得出商业 Insights 面向用户进行解读。

### 回复模板

**B1 — 数据体检报告与 SQL 确认**

严格回复：

```
📊 数据分析稽查

【数据体检报告】
 • 空值率：...
 • 重复数据：...
 • 极值提示：...

【即将执行的分析 SQL】
{Agent 生成的专业商业分析 SQL}

请确认：
 • 回复「确认」→ 执行查询
 • 回复「修改 XXX」→ 调整逻辑
 • 回复「取消」→ 取消本次分析
```

**B2 — 分析成功**

严格回复：

```
📊 深度分析结论

✅ 执行完成（{execution_time_ms}ms），返回 {row_count} 行数据

【核心数据指标】
{对查询结果的数据切片进行核心度量说明}

【业务洞察 (Insights)】
 1. 发现 XX 现象：因为...
 2. ...

【落地方案建议 (Recommendations)】
 • 针对该洞察的可行性建议...

可使用 /duckdb 运行预测 <该核心指标> 进一步推演未来趋势。
```

**B3 — 查询失败**

严格回复：

```
📊 查询结果

❌ 执行失败
 错误信息：{error_message}

可能原因：表名、字段不存在或 SQL 语法错误。
建议让 Agent 重新检视 Schema 并修改 SQL 测试。
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

### 多版本架构

预测功能支持三个版本层级，按需升级：

| 版本 | 核心特性 | 依赖文件 |
|------|----------|----------|
| 🟢 Basic（默认） | ARIMA / 线性回归 / Lasso / 指数平滑 / Prophet | `requirements-basic.txt` |
| 🔵 Plus | + 自动特征工程、交叉验证、SHAP 解释 | `requirements-plus.txt` |
| 🟣 Pro | + 深度学习 (LSTM/Transformer)、因果推断 | `requirements-pro.txt` |

版本管理命令：`/duckdb 配置 查看版本` · `/duckdb 配置 升级 plus` · `/duckdb 配置 降级 basic`

详细对比见 [references/tier_comparison.md](references/tier_comparison.md)。

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
 • 当前版本：{current_tier}
 • 模型选择：自动对比所有可用模型
 • 数据范围：{data_range}
 • 预测周期：{periods} 天
 • 评估指标：MSE / AIC

系统自动训练当前版本所有可用模型，选择误差最小的作为最优模型。
如需更多模型能力，可升级版本：/duckdb 配置 升级 plus

请确认：
 • 回复「确认」→ 执行预测
 • 回复「修改 模型 XXX」→ 指定单一模型
 • 回复「取消」→ 取消
```

**C2 — 预测成功（标准预测分析报告）**

强制使用以下标准化 Markdown 报告模板：

```
# 预测分析报告：{target}
**当前版本：** {current_tier} | **最优模型：** {best_model_name}

## 1. 执行摘要 (Executive Summary)
经过 {models_trained} 个模型的自动竞技，最终选择 {best_model_name}。预计未来 {periods} 天内，目标指标平均值为 {mean_forecast}，将在 {min_forecast} 至 {max_forecast} 范围内波动。

## 2. 预测趋势 (ASCII Trend Visuals)
```text
{从执行结果中直接复制脚本输出的 ASCII 趋势图，不要删除或修改它}
```

## 3. 模型指标对比
 | 模型 | MSE | MAE |
 |---|---|---|
 | {model_1_name} | {mse_1} | {mae_1} |
 | ... | ... | ... |

## 4. 深度洞察与建议 (Insights & Recommendations)
 1. **趋势洞察**：{Agent 根据走势解释}
 2. **业务建议**：{Agent 基于此开出的落地“处方”}
 {Plus/Pro 版额外显示特征重要性、SHAP 解释等}

---
✅ 本次预测 ID：`{prediction_id}`
是否将此任务配置为定时调度执行？（是/否）
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

读取 `records/` 下的查询和预测记录。若无记录，回复暂无。
有记录严格回复：
```
📜 历史记录（{date}）
【查询】
 {序号}. {query_id} — {nl_query} ({time}ms)
【预测】
 {序号}. {prediction_id} — {target} ({model})
```

---

## Phase E：配置定时任务

1. 先向用户明确提问：「请告诉我期望的执行频率（每天/每周）和具体时间（如 08:00）。」
2. 根据回答生成 cron 表达式，并写入 `~/.openclaw/openclaw.json`：
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
✅ 任务配置完成！( {frequency} {time} ) 
Cron: {cron_expression} | 下次运行: {next_run_time}
```

---

## 持久化记录

所有查询和预测自动保存到 `{baseDir}/records/`（`queries/` 和 `predictions/` 按日期分目录）。详细格式见 [references/record_format.md](references/record_format.md)。

---

## 参考文档

- **多版本架构说明**：[references/tier_comparison.md](references/tier_comparison.md)
- 命令详细参数与确认流程：[references/commands.md](references/commands.md)
- 连接配置说明：[references/configuration.md](references/configuration.md)
- 脚本使用参考：[references/scripts.md](references/scripts.md)
- 持久化记录格式：[references/record_format.md](references/record_format.md)
- 故障排查指南：[references/troubleshooting.md](references/troubleshooting.md)
