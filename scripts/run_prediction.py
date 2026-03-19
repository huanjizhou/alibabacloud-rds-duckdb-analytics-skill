#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_prediction.py - 执行预测分析
Run Prediction Analysis

功能:
- 执行预测脚本
- 保存预测结果
- 更新预测配置状态

Usage:
    python run_prediction.py --prediction-id pred_xxx --env-file .env
    python run_prediction.py --script /path/to/prediction.py
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv


def run_script(script_file):
    """执行预测脚本"""
    try:
        result = subprocess.run(
            ["python3", script_file],
            capture_output=True,
            text=True,
            check=False,
            timeout=300
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "执行超时（超过 5 分钟）"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def load_prediction_config(prediction_id, config):
    """加载预测配置"""
    # 在预测目录中查找
    predictions_dir = Path(config["records_dir"]) / "predictions"
    
    for date_dir in predictions_dir.iterdir():
        if not date_dir.is_dir():
            continue
        
        for config_file in date_dir.glob(f"{prediction_id}.json"):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    return None


def save_result(prediction_id, result, config):
    """保存预测结果"""
    timestamp = datetime.now()
    date_dir = Path(config["records_dir"]) / "predictions" / timestamp.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # 更新配置
    config_file = date_dir / f"{prediction_id}.json"
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            pred_config = json.load(f)
    else:
        pred_config = {"prediction_id": prediction_id}
    
    pred_config["status"] = "completed" if result["success"] else "failed"
    pred_config["last_run"] = timestamp.isoformat()
    pred_config["last_result"] = result
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(pred_config, f, indent=2, ensure_ascii=False)
    
    return config_file


def main():
    parser = argparse.ArgumentParser(description="执行预测分析")
    parser.add_argument("--prediction-id", help="预测 ID")
    parser.add_argument("--script", help="预测脚本路径")
    parser.add_argument("--env-file", "-e", default=".env", help=".env 文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径")
    
    args = parser.parse_args()
    
    if not args.prediction_id and not args.script:
        print("错误：需要指定 --prediction-id 或 --script")
        return 1
    
    # 加载配置
    load_dotenv(args.env_file)
    config = {
        "records_dir": os.getenv("RECORDS_DIR", "/home/admin/.openclaw/workspace/skills/alibabacloud-rds-duckdb-analytics-skill/records")
    }
    
    # 获取脚本路径
    script_file = args.script
    
    if args.prediction_id and not script_file:
        # 从配置中读取脚本路径
        pred_config = load_prediction_config(args.prediction_id, config)
        
        if not pred_config:
            print(f"错误：预测配置不存在 {args.prediction_id}")
            return 1
        
        script_file = pred_config.get("script_file")
    
    if not script_file or not Path(script_file).exists():
        print(f"错误：脚本文件不存在 {script_file}")
        return 1
    
    # 执行脚本
    result = run_script(script_file)
    
    if not result["success"]:
        print(f"错误：{result.get('stderr', result.get('error', '执行失败'))}")
        return 1
    
    # 保存结果
    if args.prediction_id:
        config_file = save_result(args.prediction_id, result, config)
        result["config_file"] = str(config_file)
    
    # 输出
    output = {
        "success": True,
        "stdout": result["stdout"],
        "executed_at": datetime.now().isoformat()
    }
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
