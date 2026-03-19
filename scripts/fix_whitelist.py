#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_whitelist.py - 自动修复 RDS 白名单

功能:
- 获取本机公网 IP
- 检查 RDS 实例当前白名单
- 自动将本机 IP 加入白名单
- 使用阿里云 CLI 执行

Usage:
    python fix_whitelist.py --instance-id rm-xxx --region cn-hangzhou
"""

import argparse
import json
import logging
import subprocess
import sys
import urllib.request
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_public_ip():
    """获取本机公网 IP"""
    try:
        # 使用多个服务获取公网 IP，提高可靠性
        services = [
            'https://api.ipify.org?format=json',
            'https://ifconfig.me/ip',
            'https://icanhazip.com'
        ]
        
        for service in services:
            try:
                logger.info(f"尝试从 {service} 获取公网 IP...")
                req = urllib.request.Request(service, headers={'User-Agent': 'curl/7.68.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    if 'ipify' in service:
                        data = json.loads(response.read().decode())
                        ip = data['ip']
                    else:
                        ip = response.read().decode().strip()
                    
                    logger.info(f"获取到公网 IP: {ip}")
                    return ip
            except Exception as e:
                logger.warning(f"从 {service} 获取 IP 失败：{e}")
                continue
        
        logger.error("无法从任何服务获取公网 IP")
        return None
        
    except Exception as e:
        logger.error(f"获取公网 IP 失败：{e}")
        return None


def check_aliyun_cli():
    """检查阿里云 CLI 是否安装"""
    try:
        result = subprocess.run(
            ['aliyun', 'version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info(f"阿里云 CLI 已安装：{result.stdout.strip()}")
            return True
        else:
            logger.error("阿里云 CLI 未正确安装")
            return False
    except FileNotFoundError:
        logger.error("阿里云 CLI 未安装")
        logger.info("安装方法：https://help.aliyun.com/document_detail/110317.html")
        return False
    except subprocess.TimeoutExpired:
        logger.error("检查阿里云 CLI 超时")
        return False


def get_current_whitelist(instance_id, region):
    """获取当前白名单"""
    try:
        logger.info(f"查询实例 {instance_id} 的当前白名单...")
        result = subprocess.run(
            [
                'aliyun', 'rds', 'DescribeDBInstanceIPLists',
                '--DBInstanceId', instance_id,
                '--RegionId', region
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            items = data.get('Items', {}).get('DBInstanceIPList', [])
            
            whitelist = []
            for item in items:
                ips = item.get('SecurityIPList', '')
                if ips:
                    whitelist.extend(ips.split(','))
            
            logger.info(f"当前白名单：{whitelist}")
            return whitelist
        else:
            logger.error(f"查询白名单失败：{result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error("查询白名单超时")
        return None
    except Exception as e:
        logger.error(f"查询白名单失败：{e}")
        return None


def add_ip_to_whitelist(instance_id, region, ip):
    """将 IP 加入白名单"""
    try:
        # 先获取当前白名单
        current = get_current_whitelist(instance_id, region)
        if current is None:
            logger.error("无法获取当前白名单，操作取消")
            return False
        
        # 检查 IP 是否已在白名单中
        ip_with_cidr = f"{ip}/32"
        if ip in current or ip_with_cidr in current:
            logger.info(f"IP {ip} 已在白名单中，无需添加")
            return True
        
        # 添加新 IP（保留现有白名单）
        new_whitelist = ','.join(current + [ip])
        
        logger.info(f"将 IP {ip} 加入白名单...")
        result = subprocess.run(
            [
                'aliyun', 'rds', 'ModifySecurityIps',
                '--DBInstanceId', instance_id,
                '--RegionId', region,
                '--SecurityIps', new_whitelist,
                '--SecurityGroupName', 'default'
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"✓ 成功将 IP {ip} 加入白名单")
            return True
        else:
            logger.error(f"添加白名单失败：{result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("添加白名单超时")
        return False
    except Exception as e:
        logger.error(f"添加白名单失败：{e}")
        return False


def test_connection(host, port, user, password, database, timeout=10):
    """测试数据库连接"""
    try:
        import pymysql
        
        logger.info(f"测试连接：{host}:{port}...")
        conn = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            charset="utf8mb4",
            connect_timeout=timeout
        )
        conn.close()
        logger.info("✓ 连接测试成功")
        return True
        
    except pymysql.Error as e:
        logger.error(f"连接失败：{e}")
        return False
    except Exception as e:
        logger.error(f"连接测试失败：{e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="自动修复 RDS 白名单")
    parser.add_argument("--instance-id", required=True, help="RDS 实例 ID")
    parser.add_argument("--region", default="cn-hangzhou", help="阿里云区域（默认：cn-hangzhou）")
    parser.add_argument("--env-file", "-e", default=".env", help=".env 文件路径")
    parser.add_argument("--test-connection", action="store_true", help="修复后测试连接")
    parser.add_argument("--dry-run", action="store_true", help="仅检查，不实际修改")
    
    args = parser.parse_args()
    
    logger.info("=" * 50)
    logger.info("RDS 白名单自动修复工具")
    logger.info("=" * 50)
    
    # 步骤 1: 检查阿里云 CLI
    logger.info("\n【步骤 1/4】检查阿里云 CLI")
    if not check_aliyun_cli():
        logger.error("\n❌ 阿里云 CLI 未安装，无法继续")
        logger.info("请先安装阿里云 CLI:")
        logger.info("  https://help.aliyun.com/document_detail/110317.html")
        return 1
    logger.info("✓ 阿里云 CLI 已就绪\n")
    
    # 步骤 2: 获取公网 IP
    logger.info("【步骤 2/4】获取本机公网 IP")
    public_ip = get_public_ip()
    if not public_ip:
        logger.error("\n❌ 无法获取公网 IP，请检查网络连接")
        return 1
    logger.info(f"✓ 本机公网 IP: {public_ip}\n")
    
    # 步骤 3: 检查当前白名单
    logger.info("【步骤 3/4】检查当前白名单")
    current_whitelist = get_current_whitelist(args.instance_id, args.region)
    if current_whitelist is None:
        logger.error("\n❌ 无法查询白名单，请检查实例 ID 和区域是否正确")
        return 1
    
    if public_ip in current_whitelist or f"{public_ip}/32" in current_whitelist:
        logger.info(f"✓ IP {public_ip} 已在白名单中")
    else:
        logger.info(f"⚠ IP {public_ip} 不在白名单中，需要添加\n")
    
    # 步骤 4: 添加 IP 到白名单
    if args.dry_run:
        logger.info("【干跑模式】不实际修改白名单")
    else:
        logger.info("【步骤 4/4】添加 IP 到白名单")
        success = add_ip_to_whitelist(args.instance_id, args.region, public_ip)
        if not success:
            logger.error("\n❌ 添加白名单失败")
            return 1
    
    # 可选：测试连接
    if args.test_connection:
        from dotenv import load_dotenv
        import os
        
        logger.info("\n【额外步骤】测试数据库连接")
        load_dotenv(args.env_file)
        
        host = os.getenv("DUCKDB_HOST")
        port = os.getenv("DUCKDB_PORT", "3306")
        user = os.getenv("DUCKDB_USER")
        password = os.getenv("DUCKDB_PASSWORD")
        database = os.getenv("DUCKDB_DATABASE")
        
        if not all([host, user, password, database]):
            logger.warning("⚠ .env 文件配置不完整，跳过连接测试")
        else:
            if test_connection(host, port, user, password, database):
                logger.info("\n✅ 白名单修复完成，连接测试成功！")
            else:
                logger.warning("\n⚠ 白名单已修复，但连接测试仍失败，请检查其他配置")
    
    logger.info("\n" + "=" * 50)
    logger.info("✅ 白名单修复完成！")
    logger.info("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
