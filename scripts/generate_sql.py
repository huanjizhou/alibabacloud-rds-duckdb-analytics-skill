#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_sql.py - 自然语言生成 SQL

功能:
- 基于 Schema 和规则生成 SQL
- 支持用户确认流程
- 保存生成的 SQL 记录

Usage:
    python generate_sql.py --query "最近 30 天的订单数据" --env-file .env
"""

import argparse
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

try:
    import pymysql
except ImportError:
    logger.error("需要安装 pymysql：pip install pymysql")
    sys.exit(1)


class SQLGenerator:
    """SQL 生成器 - 通过 MySQL 协议连接 RDS DuckDB FDW"""
    
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.schema_info = {}
        
    def connect(self):
        """连接到 RDS MySQL (DuckDB FDW)"""
        try:
            rds_config = self.config["duckdb"]
            logger.info(f"正在连接 RDS: {rds_config['host']}:{rds_config['port']}")
            self.connection = pymysql.connect(
                host=rds_config["host"],
                port=rds_config["port"],
                user=rds_config["user"],
                password=rds_config["password"],
                database=rds_config["database"],
                charset="utf8mb4",
                connect_timeout=10
            )
            logger.info("RDS 连接成功")
            return True
        except pymysql.Error as e:
            logger.error(f"连接失败：{e}")
            return False
        except Exception as e:
            logger.error(f"连接失败：{e}")
            return False
    
    def load_schema(self):
        """加载数据库 Schema 信息"""
        try:
            logger.info("正在加载数据库 Schema...")
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = DATABASE()
                """)
                tables_result = cursor.fetchall()
                
                logger.info(f"发现 {len(tables_result)} 个表")
                
                for table_row in tables_result:
                    table_name = table_row[0]
                    cursor.execute(
                        "SELECT column_name, data_type "
                        "FROM information_schema.columns "
                        "WHERE table_name = %s "
                        "ORDER BY ordinal_position",
                        (table_name,)
                    )
                    columns_result = cursor.fetchall()
                    
                    self.schema_info[table_name] = [
                        {"name": col[0], "type": col[1]}
                        for col in columns_result
                    ]
                    logger.debug(f"表 {table_name}: {len(columns_result)} 个字段")
            
            return True
        except Exception as e:
            logger.error(f"加载 Schema 失败：{e}")
            return False
    
    def generate_sql(self, natural_language):
        """基于规则生成 SQL（示例）"""
        query_lower = natural_language.lower()
        
        logger.info(f"分析查询意图：{natural_language}")
        
        # 时间范围查询
        if "最近" in query_lower or "近期" in query_lower:
            if "天" in query_lower or "日" in query_lower:
                logger.debug("识别为：最近 N 天查询")
                return """
SELECT order_date, user_id, order_amount
FROM orders
WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY order_date DESC
LIMIT 100
"""
            elif "月" in query_lower:
                logger.debug("识别为：最近 N 月查询")
                return """
SELECT order_date, user_id, order_amount
FROM orders
WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
ORDER BY order_date DESC
"""
        
        # 统计查询
        elif "统计" in query_lower or "汇总" in query_lower:
            if "按" in query_lower and "分组" in query_lower:
                logger.debug("识别为：分组统计查询")
                return """
SELECT category,
       COUNT(*) as count,
       AVG(amount) as avg_amount,
       SUM(amount) as total_amount
FROM orders
GROUP BY category
ORDER BY count DESC
"""
            else:
                logger.debug("识别为：总体统计查询")
                return """
SELECT COUNT(*) as total_count,
       AVG(order_amount) as avg_amount,
       SUM(order_amount) as total_amount,
       MIN(order_amount) as min_amount,
       MAX(order_amount) as max_amount
FROM orders
WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
"""
        
        # 趋势查询
        elif "趋势" in query_lower or "变化" in query_lower:
            logger.debug("识别为：趋势分析查询")
            return """
SELECT DATE(order_date) as date,
       COUNT(*) as order_count,
       AVG(order_amount) as avg_amount
FROM orders
WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY DATE(order_date)
ORDER BY date DESC
"""
        
        # Top N 查询
        elif "最高" in query_lower or "最多" in query_lower or "top" in query_lower:
            logger.debug("识别为：Top N 查询")
            return """
SELECT user_id, SUM(order_amount) as total_amount
FROM orders
GROUP BY user_id
ORDER BY total_amount DESC
LIMIT 10
"""
        
        # 最新数据
        elif "最新" in query_lower or "最近" in query_lower:
            logger.debug("识别为：最新数据查询")
            return """
SELECT *
FROM orders
ORDER BY order_date DESC
LIMIT 20
"""
        
        # 默认：显示表
        else:
            logger.debug("未识别具体意图，返回表列表")
            return "SHOW TABLES"
    
    def save_record(self, natural_language, sql):
        """保存生成的 SQL 记录"""
        try:
            timestamp = datetime.now()
            query_id = f"query_{timestamp.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
            
            date_dir = Path(self.config["records_dir"]) / "queries" / timestamp.strftime("%Y-%m-%d")
            date_dir.mkdir(parents=True, exist_ok=True)
            
            record = {
                "query_id": query_id,
                "timestamp": timestamp.isoformat(),
                "natural_language": natural_language,
                "generated_sql": sql.strip(),
                "status": "pending_confirmation",
                "schema_snapshot": list(self.schema_info.keys())
            }
            
            record_file = date_dir / f"{query_id}.json"
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
            
            logger.info(f"SQL 记录已保存：{record_file}")
            return record
        except IOError as e:
            logger.error(f"保存记录失败：{e}")
            return None
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.debug("数据库连接已关闭")


def main():
    parser = argparse.ArgumentParser(
        description="自然语言生成 SQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python generate_sql.py --query "最近 30 天的订单数据" --env-file .env
    python generate_sql.py -q "订单统计" -e .env -o result.json
        """
    )
    parser.add_argument("--query", "-q", required=True, help="自然语言查询")
    parser.add_argument("--env-file", "-e", default=".env", help=".env 文件路径（默认：.env）")
    parser.add_argument("--output", "-o", help="输出文件路径（可选）")
    parser.add_argument("--quiet", action="store_true", help="安静模式")
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # 加载配置
    logger.info(f"加载配置文件：{args.env_file}")
    load_dotenv(args.env_file)
    
    config = {
        "duckdb": {
            "host": os.getenv("DUCKDB_HOST"),
            "port": int(os.getenv("DUCKDB_PORT", "3306")),
            "user": os.getenv("DUCKDB_USER"),
            "password": os.getenv("DUCKDB_PASSWORD"),
            "database": os.getenv("DUCKDB_DATABASE")
        },
        "records_dir": os.getenv("RECORDS_DIR", "./records")
    }
    
    # 生成 SQL
    generator = SQLGenerator(config)
    
    if not generator.connect():
        logger.error("无法连接到数据库")
        return 1
    
    if not generator.load_schema():
        logger.warning("Schema 加载失败，使用默认规则生成")
    
    sql = generator.generate_sql(args.query)
    record = generator.save_record(args.query, sql)
    
    generator.close()
    
    if not record:
        logger.error("保存记录失败")
        return 1
    
    # 输出结果
    result = {
        "success": True,
        "query_id": record["query_id"],
        "natural_language": record["natural_language"],
        "generated_sql": record["generated_sql"],
        "record_file": str(Path(config["records_dir"]) / "queries" / datetime.now().strftime("%Y-%m-%d") / f"{record['query_id']}.json")
    }
    
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"结果已保存到：{args.output}")
        except IOError as e:
            logger.error(f"保存输出失败：{e}")
            return 1
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
