#!/bin/bash
# install_dependencies.sh - 安装依赖脚本
# Install Dependencies Script

set -e

echo "📦 开始安装依赖 | Starting dependency installation..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    elif [ "$(uname)" = "Darwin" ]; then
        OS="macos"
    else
        OS="unknown"
    fi
    echo $OS
}

OS=$(detect_os)
echo "检测到操作系统 | Detected OS: $OS"

# 安装系统包
install_system_packages() {
    echo ""
    echo "=== 安装系统包 | Installing System Packages ==="
    
    case $OS in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip curl wget
            ;;
        centos|rhel|fedora)
            sudo yum install -y python3 python3-pip curl wget
            ;;
        macos)
            if command -v brew &> /dev/null; then
                brew install python3
            else
                echo -e "${YELLOW}⚠${NC} Homebrew 未安装，请先安装 Homebrew"
            fi
            ;;
        *)
            echo -e "${YELLOW}⚠${NC} 未知操作系统，请手动安装 Python 3"
            ;;
    esac
}

# 安装阿里云 CLI
install_aliyun_cli() {
    echo ""
    echo "=== 安装阿里云 CLI | Installing Aliyun CLI ==="
    
    if command -v aliyun &> /dev/null; then
        echo -e "${GREEN}✓${NC} 阿里云 CLI 已安装"
        return
    fi
    
    curl -Lo aliyun-cli.zip https://aliyuncli.oss-cn-hangzhou.aliyuncs.com/aliyun-cli-linux-3.0.44-amd64.zip
    unzip aliyun-cli.zip
    sudo mv aliyun /usr/local/bin/
    rm -rf aliyun-cli.zip aliyun
    echo -e "${GREEN}✓${NC} 阿里云 CLI 安装完成"
    
    echo ""
    echo "请运行配置：aliyun configure"
}

# 安装 DuckDB
install_duckdb() {
    echo ""
    echo "=== 安装 DuckDB | Installing DuckDB ==="
    
    if command -v duckdb &> /dev/null; then
        echo -e "${GREEN}✓${NC} DuckDB 已安装"
        return
    fi
    
    # 下载 DuckDB CLI
    curl -Lo duckdb https://github.com/duckdb/duckdb/releases/download/v1.0.0/duckdb_cli-linux-amd64.zip
    unzip duckdb.zip
    sudo mv duckdb /usr/local/bin/
    rm -rf duckdb.zip duckdb_cli-linux-amd64.zip
    echo -e "${GREEN}✓${NC} DuckDB 安装完成"
}

# 安装 Python 包
install_python_packages() {
    echo ""
    echo "=== 安装 Python 包 | Installing Python Packages ==="
    
    pip3 install --upgrade pip
    
    pip3 install \
        duckdb>=0.9.0 \
        pymysql>=1.0.0 \
        pandas>=2.0.0 \
        pyyaml>=6.0 \
        requests>=2.28.0 \
        sqlalchemy>=2.0.0
    
    echo -e "${GREEN}✓${NC} Python 包安装完成"
}

# 主流程
echo ""
echo "警告 | Warning: 此脚本需要管理员权限 | This script requires admin privileges"
read -p "是否继续？| Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消 | Cancelled"
    exit 1
fi

install_system_packages
install_aliyun_cli
install_duckdb
install_python_packages

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ 所有依赖安装完成！| All dependencies installed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "下一步：配置阿里云凭证 | Next: Configure AlibabaCloud credentials"
echo "运行：aliyun configure"
echo ""
echo "然后运行依赖检查 | Then run dependency check:"
echo "./scripts/check_dependencies.sh"
