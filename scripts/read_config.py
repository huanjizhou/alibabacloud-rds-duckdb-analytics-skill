#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
read_config.py - 读取配置文件

功能:
- 从 .env 文件读取 DuckDB 连接配置
- 验证必填字段
- 返回配置字典

Usage:
    python read_config.py --env-file .env
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def load_config(env_file):
    """从 .env 文件加载配置"""
    # 检查文件是否存在
    if not Path(env_file).exists():
        logger.error(f".env 文件不存在：{env_file}")
        return {
            "success": False,
            "error": "config_file_not_found",
            "message": f".env 文件不存在：{env_file}",
            "solution": "运行 'cp .env.example .env' 创建配置文件"
        }
    
    # 加载配置
    load_dotenv(env_file)
    logger.info(f".env 文件加载成功：{env_file}")
    
    # 验证必填字段
    required_fields = {
        "DUCKDB_HOST": "DuckDB 实例地址",
        "DUCKDB_PORT": "DuckDB 端口",
        "DUCKDB_USER": "数据库用户名",
        "DUCKDB_PASSWORD": "数据库密码",
        "DUCKDB_DATABASE": "数据库名"
    }
    
    missing = [f for f in required_fields.keys() if not os.getenv(f)]
    
    if missing:
        missing_details = [f"{f} ({required_fields[f]})" for f in missing]
        logger.error(f"缺少必填字段：{missing_details}")
        return {
            "success": False,
            "error": "missing_required_fields",
            "message": "配置不完整，缺少以下必填字段",
            "missing_fields": missing_details,
            "solution": "编辑 .env 文件，填入所有必填字段"
        }
    
    # 构建配置
    config = {
        "duckdb": {
            "host": os.getenv("DUCKDB_HOST"),
            "port": int(os.getenv("DUCKDB_PORT")),
            "user": os.getenv("DUCKDB_USER"),
            "password": os.getenv("DUCKDB_PASSWORD"),
            "database": os.getenv("DUCKDB_DATABASE")
        },
        "records_dir": os.getenv("RECORDS_DIR", "./records")
    }
    
    # 可选字段
    if os.getenv("RDS_INSTANCE_ID"):
        config["rds_instance_id"] = os.getenv("RDS_INSTANCE_ID")
        logger.debug(f"RDS 实例 ID: {config['rds_instance_id']}")
    
    logger.info("配置加载完成")
    return {
        "success": True,
        "config": config
    }


def main():
    parser = argparse.ArgumentParser(
        description="读取配置文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python read_config.py --env-file .env
    python read_config.py -e .env -o config.json
        """
    )
    parser.add_argument("--env-file", "-e", default=".env", help=".env 文件路径（默认：.env）")
    parser.add_argument("--output", "-o", help="输出文件路径（可选）")
    parser.add_argument("--quiet", "-q", action="store_true", help="安静模式，只输出结果")
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    result = load_config(args.env_file)
    
    # 输出结果
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存到：{args.output}")
        except IOError as e:
            logger.error(f"保存文件失败：{e}")
            return 1
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
