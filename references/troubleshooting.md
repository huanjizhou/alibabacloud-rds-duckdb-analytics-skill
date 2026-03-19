# 错误处理与故障排查

## 常见错误

### 连接失败

**错误信息**:
```
【步骤 1/4】检查实例连接
⚠️ 连接失败：无法连接到 rm-xxx.mysql.rds.aliyuncs.com:3306
```

**可能原因**:
1. .env 配置错误（主机名、端口、用户名、密码）
2. 网络问题（安全组未开放 3306 端口）
3. RDS 实例未运行

**解决步骤**:
1. 检查 .env 文件配置是否正确
2. 确认端口是 3306（不是 5432！）
3. 在阿里云控制台检查安全组规则
4. 测试连接：`/duckdb 配置 测试连接`

---

### SQL 执行失败

**错误信息**:
```
【步骤 4/4】执行查询
⚠️ SQL 执行失败：Table 'orders' doesn't exist
```

**可能原因**:
1. 表名不存在
2. 字段名错误
3. 数据库权限不足

**解决步骤**:
1. 检查表名是否正确（区分大小写）
2. 查看数据库 Schema：`SHOW TABLES;`
3. 确认用户有查询权限
4. 手动测试 SQL

---

### 预测模型失败

**错误信息**:
```
⚠️ 预测模型创建失败：数据量不足（需要至少 30 条记录）
```

**可能原因**:
1. 历史数据太少
2. 查询条件过于严格
3. 数据时间范围太短

**解决步骤**:
1. 增加历史数据时间范围
2. 放宽查询条件
3. 更换为简单模型（如线性回归）

---

### 记录不存在

**错误信息**:
```
⚠️ 记录不存在：query_xxx
```

**可能原因**:
1. 记录 ID 不正确
2. 记录已被删除
3. 日期范围错误

**解决步骤**:
1. 使用 `/duckdb 记录` 查看现有记录
2. 检查记录 ID 是否正确
3. 确认日期范围

---

### 依赖缺失

**错误信息**:
```
ModuleNotFoundError: No module named 'duckdb'
```

**可能原因**:
1. Python 包未安装
2. 虚拟环境未激活

**解决步骤**:
```bash
# 安装依赖
pip install duckdb pandas pymysql statsmodels pyyaml

# 或运行安装脚本
./scripts/install_dependencies.sh
```

---

## 错误响应格式

所有错误统一使用以下格式：

```
[操作] 失败

【错误信息】
[具体错误描述]

【可能的原因】
1. 原因一
2. 原因二

【解决步骤】
1. 步骤一
2. 步骤二

需要帮助吗？
```

---

## 调试技巧

### 启用详细日志

```bash
# 设置环境变量
export DEBUG=true
python3 scripts/execute_query.py --sql "SELECT 1"
```

### 手动测试连接

```bash
python3 -c "
import pymysql
conn = pymysql.connect(
    host='rm-xxx.mysql.rds.aliyuncs.com',
    port=3306,
    user='analytics_user',
    password='your_password',
    database='ecommerce'
)
print('连接成功！')
conn.close()
"
```

### 检查 Python 环境

```bash
# 检查 Python 版本
python3 --version

# 检查已安装的包
pip list | grep -E 'duckdb|pandas|pymysql|statsmodels'
```

---

## 获取帮助

如果以上方法无法解决问题：

1. 查看完整日志
2. 搜索错误信息
3. 联系技术支持
