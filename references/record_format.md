# 持久化记录格式

## 目录结构

```
records/
├── queries/              # SQL 查询记录
│   ├── 2026-03-19/
│   │   └── query_20260319_162000_abc123.json
│   └── 2026-03-20/
│       └── query_20260320_093000_def456.json
└── predictions/          # 预测分析记录
    ├── 2026-03-19/
    │   ├── pred_xxx.json       # 预测配置
    │   ├── pred_xxx.py         # 预测脚本
    │   └── results/            # 执行结果
    │       └── forecast_result.json
```

---

## 查询记录格式

### JSON 结构

```json
{
  "query_id": "query_20260319_162000_abc123",
  "timestamp": "2026-03-19T16:20:00+08:00",
  "natural_language": "最近 30 天的订单数据",
  "generated_sql": "SELECT DATE(order_date) as date, COUNT(*) as order_count FROM orders WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) GROUP BY DATE(order_date) ORDER BY date DESC",
  "user_confirmed": true,
  "execution_time_ms": 234,
  "row_count": 30,
  "status": "success",
  "error_message": null,
  "metadata": {
    "tables_accessed": ["orders"],
    "date_range": {
      "start": "2026-02-17",
      "end": "2026-03-19"
    }
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `query_id` | string | 唯一标识符 |
| `timestamp` | string | ISO 8601 时间戳 |
| `natural_language` | string | 用户原始查询 |
| `generated_sql` | string | 生成的 SQL |
| `user_confirmed` | boolean | 用户是否确认 |
| `execution_time_ms` | number | 执行时间（毫秒） |
| `row_count` | number | 返回行数 |
| `status` | string | 状态：success/failed |
| `error_message` | string|null | 错误信息 |
| `metadata` | object | 附加元数据 |

---

## 预测记录格式

### 预测配置（pred_xxx.json）

```json
{
  "prediction_id": "pred_20260319_162000_xyz789",
  "timestamp": "2026-03-19T16:20:00+08:00",
  "target": "未来 30 天销售趋势",
  "model": "arima",
  "model_params": {
    "order": [1, 1, 1],
    "seasonal_order": [1, 1, 1, 7]
  },
  "periods": 30,
  "data_source": {
    "table": "orders",
    "metric": "order_count",
    "date_column": "order_date",
    "history_days": 365
  },
  "schedule": {
    "enabled": true,
    "cron": "0 8 * * *",
    "timezone": "Asia/Shanghai"
  },
  "script_path": "predictions/2026-03-19/pred_xxx.py"
}
```

### 预测结果（forecast_result.json）

```json
{
  "prediction_id": "pred_20260319_162000_xyz789",
  "executed_at": "2026-03-20T08:00:00+08:00",
  "execution_time_ms": 1234,
  "status": "success",
  "forecast": {
    "dates": ["2026-03-20", "2026-03-21", ...],
    "values": [123.4, 125.6, ...],
    "confidence_intervals": {
      "lower_95": [118.2, 120.1, ...],
      "upper_95": [128.6, 131.1, ...]
    }
  },
  "metrics": {
    "mae": 5.23,
    "rmse": 6.78,
    "mape": 4.5
  }
}
```

---

## 记录管理

### 查看记录

```bash
# 查看所有查询记录
/duckdb 记录

# 查看指定日期
/duckdb 记录 2026-03-19

# 只看 SQL 记录
/duckdb 记录 sql

# 只看预测记录
/duckdb 记录 预测
```

### 重用记录

```bash
# 通过 ID 重用
/duckdb 问数 query_20260319_162000_abc123

# 通过关键词重用
/duckdb 问数 订单统计
```

### 清理记录

```bash
# 清理 30 天前的记录
find records/queries -type f -mtime +30 -delete
```
