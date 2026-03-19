# 脚本使用文档

## 核心脚本列表

| 脚本 | 功能 | 调用方式 |
|------|------|----------|
| `scripts/check_dependencies.sh` | 检查系统依赖 | Shell |
| `scripts/read_config.py` | 读取 .env 配置 | Python |
| `scripts/generate_sql.py` | 自然语言生成 SQL | Python |
| `scripts/execute_query.py` | 执行 SQL 查询 | Python |
| `scripts/generate_prediction.py` | 生成预测脚本 | Python |
| `scripts/run_prediction.py` | 执行预测分析 | Python |

---

## 脚本详解

### check_dependencies.sh

检查系统依赖是否已安装。

**用法**:
```bash
./scripts/check_dependencies.sh
```

**检查项**:
- python3
- pip
- 必需的 Python 包

---

### read_config.py

从 .env 文件读取配置并验证。

**用法**:
```bash
python3 scripts/read_config.py --env-file .env
```

**参数**:
- `--env-file`: .env 文件路径

**输出**:
```json
{
  "host": "rm-xxx.mysql.rds.aliyuncs.com",
  "port": 3306,
  "user": "analytics_user",
  "database": "ecommerce"
}
```

---

### generate_sql.py

将自然语言转换为 SQL 查询。

**用法**:
```bash
python3 scripts/generate_sql.py \
  --query "最近 30 天的订单数据" \
  --env-file .env
```

**参数**:
- `--query`: 自然语言查询描述
- `--env-file`: .env 文件路径

**输出**:
```json
{
  "sql": "SELECT DATE(order_date) as date, COUNT(*) as order_count FROM orders WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) GROUP BY DATE(order_date) ORDER BY date DESC",
  "tables": ["orders"],
  "confidence": 0.95
}
```

---

### execute_query.py

执行 SQL 查询并保存记录。

**用法**:
```bash
python3 scripts/execute_query.py \
  --sql "SELECT * FROM orders LIMIT 10" \
  --env-file .env \
  --save-record
```

**参数**:
- `--sql`: SQL 查询语句
- `--env-file`: .env 文件路径
- `--save-record`: 是否保存记录

**输出**:
```json
{
  "success": true,
  "execution_time_ms": 234,
  "row_count": 10,
  "record_id": "query_20260319_162000_abc123"
}
```

---

### generate_prediction.py

生成预测分析脚本（支持多模型自动对比）。

**支持的模型**：
- `ARIMA` - 时间序列模型（适合有趋势/季节性的数据）
- `线性回归` - 简单趋势预测
- `Lasso 回归` - 带 L1 正则化和特征选择（适合多特征场景）
- `指数平滑` - 短期预测
- `Prophet` - Facebook 开源模型（适合复杂模式）

**用法**:
```bash
# 自动对比所有模型（推荐）
python3 scripts/generate_prediction.py \
  --target "未来 30 天销售预测" \
  --table orders --date-column order_date --metric-column order_amount \
  --models auto \
  --periods 30 \
  --env-file .env

# 指定单一模型
python3 scripts/generate_prediction.py \
  --target "未来 30 天销售预测" \
  --table orders --metric-column order_amount \
  --models arima \
  --periods 30 \
  --env-file .env
```

**参数**:
- `--target`: 预测目标描述
- `--table`: 数据表名（默认：your_table）
- `--date-column`: 日期列名（默认：created_at）
- `--metric-column`: 指标列名（默认：metric_value）
- `--models`: 模型选择
  - `auto`（默认）- 自动训练所有可用模型，选择最优
  - `arima` - 只使用 ARIMA
  - `linear_regression` - 只使用线性回归
  - `lasso` - 只使用 Lasso 回归
  - `exponential_smoothing` - 只使用指数平滑
  - `prophet` - 只使用 Prophet
- `--periods`: 预测期数（天数）
- `--env-file`: .env 文件路径

**输出**:
- 生成预测脚本文件
- 返回预测配置 JSON（包含所有模型对比结果）
- 自动选择 MSE/AIC 最优的模型作为最终预测

---

### run_prediction.py

执行预测分析。

**用法**:
```bash
python3 scripts/run_prediction.py \
  --prediction-script /path/to/pred_xxx.py \
  --env-file .env
```

**参数**:
- `--prediction-script`: 预测脚本路径
- `--env-file`: .env 文件路径

**输出**:
- 预测结果 JSON
- 可视化图表（可选）
