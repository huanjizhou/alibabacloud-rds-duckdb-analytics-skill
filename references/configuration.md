# 配置与故障排查参考

## .env 配置文件

文件位置：`{baseDir}/.env`（模板：`.env.example`）

### 必填字段

| 字段 | 说明 | 示例 |
|------|------|------|
| DUCKDB_HOST | DuckDB 实例地址<br>⚠️ **推荐使用公网地址**，避免内网连接问题 | `rm-xxx.mysql.rds.aliyuncs.com` |
| DUCKDB_PORT | 端口<br>MySQL 默认：3306 | `3306` |
| DUCKDB_USER | 用户名 | `analytics_user` |
| DUCKDB_PASSWORD | 密码 | `your_password` |
| DUCKDB_DATABASE | 数据库名 | `ecommerce` |

### 可选字段

| 字段 | 说明 | 默认值 |
|------|------|--------|
| RDS_INSTANCE_ID | RDS 实例 ID（用于验证） | 无 |
| ALIYUN_REGION | 阿里云 Region | `cn-hangzhou` |
| ALIYUN_ACCESS_KEY_ID | AccessKey ID | 无 |
| ALIYUN_ACCESS_KEY_SECRET | AccessKey Secret | 无 |
| RECORDS_DIR | 记录持久化目录 | `{baseDir}/records` |

---

## 脚本参考

| 脚本 | 用途 | 调用方式 |
|------|------|----------|
| `check_dependencies.sh` | 检查 Python 和依赖包 | `bash scripts/check_dependencies.sh` |
| `install_dependencies.sh` | 自动安装依赖 | `bash scripts/install_dependencies.sh` |
| `fix_whitelist.py` | **自动修复白名单** | `python3 scripts/fix_whitelist.py --instance-id rm-xxx` |
| `read_config.py` | 读取并验证 .env | `python3 scripts/read_config.py --env-file .env` |
| `generate_sql.py` | 自然语言生成 SQL | `python3 scripts/generate_sql.py --query "..." --env-file .env` |
| `execute_query.py` | 执行 SQL 并保存记录 | `python3 scripts/execute_query.py --env-file .env` |
| `generate_prediction.py` | 生成预测方案和脚本 | `python3 scripts/generate_prediction.py --target "..." --env-file .env` |
| `run_prediction.py` | 执行预测分析 | `python3 scripts/run_prediction.py --prediction-id pred_xxx --env-file .env` |

---

## 故障排查

### 连接失败（最常见）

```
错误：无法连接到 DuckDB 实例
```

**常见原因：**
1. 实例地址或端口错误
2. 用户名或密码错误
3. **本机 IP 不在白名单中**（最常见）
4. 实例未运行或网络不通

**排查步骤：**

**方法 1：自动修复白名单（推荐）**
```bash
python3 scripts/fix_whitelist.py \
  --instance-id rm-xxx \
  --region cn-hangzhou \
  --env-file .env \
  --test-connection
```

**方法 2：手动配置白名单**
1. 登录阿里云 RDS 控制台
2. 进入实例详情页 → 白名单设置
3. 添加本机公网 IP（可通过 https://ifconfig.me/ip 查询）
4. 保存后重新测试

**方法 3：检查配置**
1. 确认 `.env` 中 HOST、PORT、USER、PASSWORD 是否正确
2. 确认实例是否运行中（阿里云控制台检查）
3. 测试网络：`telnet {host} {port}`
4. 运行 `/duckdb 配置 测试连接`

**⚠️ 重要提示：**
- 推荐使用**公网地址**连接，避免内网可达性问题
- 连接超时时间设置为 **10 秒**，超时会自动报错
- 白名单修改后可能需要 1-2 分钟生效

---

### SQL 执行失败

```
错误：SQL 语法错误或表不存在
```

排查步骤：
1. 检查生成的 SQL 中表名和字段名是否正确
2. 通过 DuckDB 客户端手动执行 SQL 验证
3. 回复「修改 表名改为 xxx」让 Agent 调整

---

### 预测模型失败

```
错误：数据不足
```

排查步骤：
1. 确认历史数据至少 30 条记录
2. 检查数据时间字段格式是否标准
3. 尝试更换模型：使用 `--model linear_regression`
4. 扩大数据时间范围

---

### 依赖安装失败

排查步骤：
1. 确认 Python 3.7+ 已安装：`python3 --version`
2. 确认 pip 可用：`pip3 --version`
3. 手动安装：`pip3 install duckdb pandas statsmodels pymysql python-dotenv`

---

## 安全注意事项

1. `.env` 文件已在 `.gitignore` 中，不会被提交到仓库
2. 建议数据库用户仅授予 SELECT 权限（最小权限原则）
3. 所有查询记录自动保存在 `records/` 目录，支持审计追溯
4. 白名单脚本需要阿里云 CLI 授权，请妥善保管 AccessKey
