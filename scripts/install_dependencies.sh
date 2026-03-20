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
    
    # 尝试使用 brew 安装 (如果有)
    if [ "$OS" = "macos" ] && command -v brew &> /dev/null; then
        echo "检测到 Homebrew，尝试使用 brew 安装..."
        if brew install aliyun-cli; then
            echo -e "${GREEN}✓${NC} 阿里云 CLI (Homebrew) 安装完成"
            return
        fi
        echo -e "${YELLOW}⚠${NC} brew 安装失败，尝试使用官方包下载..."
    fi
    
    OS_TYPE=""
    if [ "$OS" = "macos" ]; then
        OS_TYPE="macosx"
    else
        OS_TYPE="linux"
    fi
    
    ARCH=$(uname -m)
    ARCH_TYPE=""
    if [ "$ARCH" = "x86_64" ] || [ "$ARCH" = "amd64" ]; then
        ARCH_TYPE="amd64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        ARCH_TYPE="arm64"
    else
        echo -e "${RED}✗${NC} 不支持的架构: $ARCH"
        exit 1
    fi
    
    VERSION="3.3.2"
    CLI_URL="https://github.com/aliyun/aliyun-cli/releases/download/v${VERSION}/aliyun-cli-${OS_TYPE}-${VERSION}-${ARCH_TYPE}.tgz"
    
    echo "正在下载: $CLI_URL"
    if curl -Lo aliyun-cli.tgz "$CLI_URL"; then
        tar xzf aliyun-cli.tgz
        sudo mv aliyun /usr/local/bin/
        rm -f aliyun-cli.tgz
        echo -e "${GREEN}✓${NC} 阿里云 CLI 安装完成"
    else
        echo -e "${RED}✗${NC} 下载失败，请检查网络或配置"
        rm -f aliyun-cli.tgz
        exit 1
    fi
    
    echo ""
    echo "请运行配置：aliyun configure"
}

# 注意：不需要安装本地 DuckDB
# 本技能通过 MySQL 协议连接 RDS DuckDB FDW

# 安装 Python 包
install_python_packages() {
    echo ""
    echo "=== 安装 Python 包 | Installing Python Packages ==="
    
    pip3 install --upgrade pip
    
    pip3 install \
        pymysql>=1.0.0 \
        pandas>=2.0.0 \
        requests>=2.28.0 \
        python-dotenv>=1.0.0 \
        statsmodels>=0.14.0 \
        scikit-learn>=1.0.0
    
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
