#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
execute_query.py - 执行 SQL 并保存记录
Execute SQL Query and Save Record

功能:
- 通过 RDS MySQL (DuckDB FDW) 执行 SQL 查询
- 保存执行结果
- 更新查询记录状态
- 专业的错误处理和日志记录

Usage:
    python execute_query.py --query-id query_xxx --env-file .env
    python execute_query.py --sql "SELECT * FROM users LIMIT 10" --env-file .env
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

try:
    import pymysql
    import pandas as pd
except ImportError as e:
    logging.error(f"缺少依赖模块：{e}")
    sys.exit(1)


def setup_logging(log_level: str = "INFO"):
    """配置日志系统"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("execute_query.log", encoding="utf-8")
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))


def execute_query(sql: str, config: dict) -> dict:
    """
    通过 RDS MySQL (DuckDB FDW) 执行 SQL 查询
    
    Args:
        sql: SQL 查询语句
        config: 配置字典，包含 RDS 连接信息
        
    Returns:
        dict: 查询结果，包含 success/data/columns/row_count/execution_time_ms/error
    """
    start_time = time.time()
    
    try:
        # 通过 RDS MySQL 连接（DuckDB FDW）
        conn = pymysql.connect(
            host=config["rds"]["host"],
            port=config["rds"]["port"],
            user=config["rds"]["user"],
            password=config["rds"]["password"],
            database=config["rds"]["database"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10  # 10 秒连接超时
        )
        
        logger.info(f"数据库连接成功：{config['rds']['host']}:{config['rds']['port']}")
        
        with conn.cursor() as cursor:
            cursor.execute(sql)
            
            # 获取列名
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
            else:
                columns = []
            
            # 获取结果
            rows = cursor.fetchall()
            
        execution_time_ms = (time.time() - start_time) * 1000
        
        # 转换为 DataFrame 便于处理
        if rows:
            df = pd.DataFrame(rows)
            data = df.to_dict(orient="records")
        else:
            data = []
        
        conn.close()
        
        logger.info(f"查询执行成功：{len(rows)} 行，耗时 {execution_time_ms:.2f}ms")
        
        return {
            "success": True,
            "data": data,
            "columns": columns,
            "row_count": len(rows),
            "execution_time_ms": round(execution_time_ms, 2),
            "error": None
        }
        
    except pymysql.Error as e:
        logger.error(f"数据库连接失败：{e}")
        return {
            "success": False,
            "data": [],
            "columns": [],
            "row_count": 0,
            "execution_time_ms": 0,
            "error": f"数据库连接失败：{str(e)}"
        }
    except Exception as e:
        logger.error(f"查询执行失败：{e}")
        return {
            "success": False,
            "data": [],
            "columns": [],
            "row_count": 0,
            "execution_time_ms": 0,
            "error": f"查询执行失败：{str(e)}"
        }


def generate_summary(df: pd.DataFrame, sql: str) -> str:
    """生成结果摘要"""
    if df.empty:
        return "查询结果为空"
    
    first_row = df.iloc[0].to_dict()
    summary_parts = [f"{col}: {val}" for col, val in first_row.items()]
    return " | ".join(summary_parts[:5])


def save_result(query_id: str, result: dict, config: dict) -> tuple:
    """保存执行结果"""
    timestamp = datetime.now()
    date_dir = Path(config["records_dir"]) / "queries" / timestamp.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # 更新记录
    record_file = date_dir / f"{query_id}.json"
    
    if record_file.exists():
        with open(record_file, 'r', encoding='utf-8') as f:
            record = json.load(f)
    else:
        record = {"query_id": query_id}
    
    record["status"] = "completed"
    record["execution_time_ms"] = result.get("execution_time_ms")
    record["row_count"] = result.get("row_count")
    record["result_summary"] = result.get("summary")
    record["executed_at"] = timestamp.isoformat()
    
    # 保存结果数据
    result_file = date_dir / f"{query_id}_result.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    
    # 更新记录
    with open(record_file, 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    
    logger.info(f"结果已保存：{result_file}")
    return record_file, result_file


def main():
    parser = argparse.ArgumentParser(description="执行 SQL 查询")
    parser.add_argument("--query-id", help="查询记录 ID")
    parser.add_argument("--sql", help="SQL 查询语句")
    parser.add_argument("--env-file", "-e", default=".env", help=".env 文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--log-level", default="INFO", help="日志级别 (DEBUG/INFO/WARNING/ERROR)")
    
    args = parser.parse_args()
    
    if not args.query_id and not args.sql:
        logger.error("错误：需要指定 --query-id 或 --sql")
        return 1
    
    # 重新配置日志级别
    global logger
    logger = setup_logging(args.log_level)
    
    # 加载配置
    load_dotenv(args.env_file)
    config = {
        "rds": {
            "host": os.getenv("DUCKDB_HOST"),
            "port": int(os.getenv("DUCKDB_PORT", "3306")),
            "user": os.getenv("DUCKDB_USER"),
            "password": os.getenv("DUCKDB_PASSWORD"),
            "database": os.getenv("DUCKDB_DATABASE")
        },
        "records_dir": os.getenv("RECORDS_DIR", "/home/admin/.openclaw/workspace/skills/alibabacloud-rds-duckdb-analytics-skill/records")
    }
    
    # 验证 RDS 配置
    if not all([config["rds"]["host"], config["rds"]["user"], config["rds"]["password"]]):
        logger.error("RDS 配置不完整，请检查 .env 文件中的 DUCKDB_HOST/DUCKDB_USER/DUCKDB_PASSWORD")
        return 1
    
    # 获取 SQL
    if args.query_id:
        # 从记录文件读取 SQL（遍历所有日期目录）
        queries_dir = Path(config["records_dir"]) / "queries"
        record_file = None
        
        if queries_dir.exists():
            for date_dir in sorted(queries_dir.iterdir(), reverse=True):
                if not date_dir.is_dir():
                    continue
                candidate = date_dir / f"{args.query_id}.json"
                if candidate.exists():
                    record_file = candidate
                    break
        
        if not record_file:
            logger.error(f"错误：记录不存在 {args.query_id}")
            return 1
        
        with open(record_file, 'r', encoding='utf-8') as f:
            record = json.load(f)
        sql = record.get("generated_sql")
        if not sql:
            logger.error(f"记录中未找到 generated_sql 字段")
            return 1
    else:
        sql = args.sql
    
    logger.info(f"开始执行查询：{sql[:100]}...")
    
    # 执行查询
    result = execute_query(sql, config)
    
    if not result["success"]:
        logger.error(f"查询失败：{result.get('error')}")
        return 1
    
    # 保存结果
    if args.query_id:
        record_file, result_file = save_result(args.query_id, result, config)
        result["record_file"] = str(record_file)
        result["result_file"] = str(result_file)
    
    # 输出
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"结果已输出到：{args.output}")
    else:
        output = {
            "success": True,
            "row_count": result["row_count"],
            "execution_time_ms": result["execution_time_ms"],
            "summary": result.get("summary", ""),
            "data": result["data"][:10]  # 只显示前 10 行
        }
        print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
