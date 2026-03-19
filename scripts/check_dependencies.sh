#!/bin/bash
# check_dependencies.sh - 依赖检查脚本
# Dependency Check Script for AlibabaCloud RDS DuckDB Analytics Skill

set -e

echo "🔍 开始依赖检查 | Starting dependency check..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查结果追踪
MISSING_DEPS=()

# 检查命令是否存在
check_command() {
    local cmd=$1
    local name=$2
    
    if command -v "$cmd" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $name 已安装 | installed: $(command -v "$cmd")"
        return 0
    else
        echo -e "${RED}✗${NC} $name 未安装 | not installed"
        MISSING_DEPS+=("$name")
        return 1
    fi
}

# 检查 Python 包
check_python_package() {
    local package=$1
    local version=${2:-}
    
    if python3 -c "import $package" 2>/dev/null; then
        if [ -n "$version" ]; then
            installed_version=$(python3 -c "import $package; print($package.__version__)" 2>/dev/null || echo "unknown")
            echo -e "${GREEN}✓${NC} $package ($installed_version)"
        else
            echo -e "${GREEN}✓${NC} $package"
        fi
        return 0
    else
        echo -e "${RED}✗${NC} $package 未安装 | not installed"
        MISSING_DEPS+=("python-$package")
        return 1
    fi
}

# 检查阿里云 CLI
echo ""
echo "=== CLI 工具检查 | CLI Tools Check ==="
check_command "aliyun" "Aliyun CLI"
check_command "duckdb" "DuckDB CLI"

# 检查 Python
echo ""
echo "=== Python 环境检查 | Python Environment Check ==="
check_command "python3" "Python 3"

# 检查 Python 包
echo ""
echo "=== Python 包检查 | Python Packages Check ==="
check_python_package "duckdb"
check_python_package "pymysql"
check_python_package "pandas"
check_python_package "yaml"
check_python_package "requests"

# 检查阿里云凭证
echo ""
echo "=== 阿里云凭证检查 | AlibabaCloud Credentials Check ==="
if [ -f "$HOME/.aliyun/config.json" ]; then
    echo -e "${GREEN}✓${NC} 阿里云配置文件存在 | Aliyun config exists"
    
    # 尝试读取配置（不显示敏感信息）
    if aliyun configure get 2>/dev/null | grep -q "mode"; then
        echo -e "${GREEN}✓${NC} 阿里云 CLI 已配置 | Aliyun CLI configured"
    else
        echo -e "${YELLOW}⚠${NC} 阿里云 CLI 可能未正确配置 | Aliyun CLI may not be configured correctly"
        echo "   请运行：aliyun configure"
    fi
else
    echo -e "${YELLOW}⚠${NC} 阿里云配置文件不存在 | Aliyun config not found"
    echo "   请运行：aliyun configure"
fi

# 检查网络连接
echo ""
echo "=== 网络连接检查 | Network Connectivity Check ==="
if ping -c 1 -W 2 rds.aliyuncs.com &> /dev/null; then
    echo -e "${GREEN}✓${NC} 可以访问阿里云 RDS | Can access AlibabaCloud RDS"
else
    echo -e "${YELLOW}⚠${NC} 无法访问阿里云 RDS | Cannot access AlibabaCloud RDS"
    echo "   请检查网络连接"
fi

# 总结
echo ""
echo "=== 检查结果总结 | Check Summary ==="
if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ 所有依赖已满足 | All dependencies satisfied${NC}"
    echo ""
    echo "可以开始下一步！| Ready for next step!"
    exit 0
else
    echo -e "${RED}✗ 缺少以下依赖 | Missing dependencies:${NC}"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "  - $dep"
    done
    echo ""
    echo "请运行安装脚本：./scripts/install_dependencies.sh"
    echo "Please run install script: ./scripts/install_dependencies.sh"
    exit 1
fi
