#!/bin/bash
# PDF 生成工具依赖安装脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            echo "debian"
        elif [ -f /etc/redhat-release ]; then
            echo "redhat"
        elif [ -f /etc/arch-release ]; then
            echo "arch"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# 安装系统依赖
install_system_dependencies() {
    local os_type=$(detect_os)
    
    print_info "检测到操作系统: $os_type"
    print_info "安装系统依赖..."
    
    case $os_type in
        "debian")
            sudo apt-get update
            sudo apt-get install -y \
                python3 \
                python3-pip \
                python3-dev \
                build-essential \
                libcairo2-dev \
                libpango1.0-dev \
                libgdk-pixbuf2.0-dev \
                libffi-dev \
                shared-mime-info \
                ghostscript \
                fonts-noto-cjk \
                fonts-noto-color-emoji
            ;;
            
        "redhat")
            sudo yum update -y
            sudo yum install -y \
                python3 \
                python3-pip \
                python3-devel \
                gcc \
                gcc-c++ \
                cairo-devel \
                pango-devel \
                gdk-pixbuf2-devel \
                libffi-devel \
                ghostscript \
                google-noto-cjk-fonts \
                google-noto-emoji-fonts
            ;;
            
        "arch")
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm \
                python \
                python-pip \
                base-devel \
                cairo \
                pango \
                gdk-pixbuf2 \
                libffi \
                ghostscript \
                noto-fonts-cjk \
                noto-fonts-emoji
            ;;
            
        "macos")
            if ! command -v brew &> /dev/null; then
                print_info "安装 Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            brew update
            brew install \
                python@3.11 \
                cairo \
                pango \
                gdk-pixbuf \
                libffi \
                ghostscript
            ;;
            
        "windows")
            print_warning "Windows 系统请手动安装以下依赖:"
            echo "1. Python 3.8+ (https://www.python.org/downloads/)"
            echo "2. Microsoft Visual C++ Build Tools"
            echo "3. GTK+ for Windows (https://gtk.org/download/windows.php)"
            echo "4. Ghostscript (https://www.ghostscript.com/download/gsdnld.html)"
            return 0
            ;;
            
        *)
            print_warning "未识别的操作系统，请手动安装系统依赖"
            return 0
            ;;
    esac
    
    print_success "系统依赖安装完成"
}

# 安装 Python 依赖
install_python_dependencies() {
    print_info "安装 Python 依赖包..."
    
    # 升级 pip
    python3 -m pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt
    else
        # 直接安装主要依赖
        python3 -m pip install \
            markdown>=3.4.0 \
            weasyprint>=59.0 \
            pygments>=2.14.0 \
            fonttools>=4.38.0 \
            beautifulsoup4>=4.11.0 \
            lxml>=4.9.0 \
            pillow>=9.0.0 \
            requests>=2.28.0
    fi
    
    print_success "Python 依赖包安装完成"
}

# 下载和安装字体
install_fonts() {
    print_info "安装中文字体..."
    
    local font_dir
    local os_type=$(detect_os)
    
    case $os_type in
        "debian"|"redhat"|"arch"|"linux")
            font_dir="$HOME/.local/share/fonts"
            mkdir -p "$font_dir"
            ;;
        "macos")
            font_dir="$HOME/Library/Fonts"
            mkdir -p "$font_dir"
            ;;
        *)
            print_warning "跳过字体安装"
            return 0
            ;;
    esac
    
    # 下载 Noto Sans SC 字体
    if [ ! -f "$font_dir/NotoSansSC-Regular.otf" ]; then
        print_info "下载 Noto Sans SC 字体..."
        curl -L "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansSC-Regular.otf" \
             -o "$font_dir/NotoSansSC-Regular.otf" 2>/dev/null || {
            print_warning "字体下载失败，将使用系统默认字体"
        }
    fi
    
    # 下载 Fira Code 字体
    if [ ! -f "$font_dir/FiraCode-Regular.ttf" ]; then
        print_info "下载 Fira Code 字体..."
        curl -L "https://github.com/tonsky/FiraCode/raw/master/distr/ttf/FiraCode-Regular.ttf" \
             -o "$font_dir/FiraCode-Regular.ttf" 2>/dev/null || {
            print_warning "代码字体下载失败，将使用系统默认字体"
        }
    fi
    
    # 刷新字体缓存
    if command -v fc-cache &> /dev/null; then
        fc-cache -f "$font_dir"
        print_success "字体缓存已更新"
    fi
    
    print_success "字体安装完成"
}

# 验证安装
verify_installation() {
    print_info "验证安装..."
    
    local errors=0
    
    # 检查 Python
    if command -v python3 &> /dev/null; then
        print_success "Python 3: $(python3 --version)"
    else
        print_error "Python 3 未安装"
        errors=$((errors + 1))
    fi
    
    # 检查 pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3: $(pip3 --version)"
    else
        print_error "pip3 未安装"
        errors=$((errors + 1))
    fi
    
    # 检查 Python 包
    local packages=("markdown" "weasyprint" "pygments")
    for package in "${packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            local version=$(python3 -c "import $package; print($package.__version__)" 2>/dev/null || echo "unknown")
            print_success "$package: $version"
        else
            print_error "$package 未安装"
            errors=$((errors + 1))
        fi
    done
    
    # 检查可选工具
    if command -v gs &> /dev/null; then
        print_success "Ghostscript: $(gs --version)"
    else
        print_warning "Ghostscript 未安装 (PDF 压缩功能不可用)"
    fi
    
    if [ $errors -eq 0 ]; then
        print_success "所有依赖验证通过！"
        return 0
    else
        print_error "发现 $errors 个错误"
        return 1
    fi
}

# 创建测试文档
create_test_document() {
    print_info "创建测试文档..."
    
    cat > test-document.md << 'EOF'
# PDF 生成测试文档

这是一个测试文档，用于验证 PDF 生成功能。

## 中文支持测试

这里是中文内容测试：你好世界！🌍

## 代码块测试

```python
def hello_world():
    print("Hello, World!")
    return "PDF generation works!"

# 测试中文注释
hello_world()
```

## 表格测试

| 功能 | 状态 | 说明 |
|------|------|------|
| 中文支持 | ✅ | 支持中文字体 |
| 代码高亮 | ✅ | 支持语法高亮 |
| 表格 | ✅ | 支持表格格式 |

## 列表测试

1. 第一项
2. 第二项
   - 子项目 A
   - 子项目 B
3. 第三项

**粗体文本** 和 *斜体文本* 测试。

> 这是一个引用块测试。

---

测试完成！如果你能看到这个 PDF，说明生成功能正常工作。
EOF

    print_success "测试文档已创建: test-document.md"
}

# 运行测试
run_test() {
    print_info "运行 PDF 生成测试..."
    
    if [ ! -f "test-document.md" ]; then
        create_test_document
    fi
    
    if python3 scripts/generate-pdf.py test-document.md -o test-document.pdf; then
        print_success "PDF 生成测试通过！"
        print_info "测试文档: test-document.pdf"
        
        # 显示文件大小
        if [ -f "test-document.pdf" ]; then
            local file_size=$(stat -c%s "test-document.pdf" 2>/dev/null || stat -f%z "test-document.pdf" 2>/dev/null || echo "unknown")
            print_info "文件大小: $((file_size / 1024)) KB"
        fi
        
        return 0
    else
        print_error "PDF 生成测试失败"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo "PDF 生成工具依赖安装脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  --system-only       仅安装系统依赖"
    echo "  --python-only       仅安装 Python 依赖"
    echo "  --fonts-only        仅安装字体"
    echo "  --verify            仅验证安装"
    echo "  --test              运行测试"
    echo "  --skip-system       跳过系统依赖安装"
    echo "  --skip-fonts        跳过字体安装"
    echo ""
    echo "示例:"
    echo "  $0                  # 完整安装"
    echo "  $0 --python-only    # 仅安装 Python 依赖"
    echo "  $0 --verify --test  # 验证并测试"
}

# 主函数
main() {
    local install_system=true
    local install_python=true
    local install_fonts=true
    local verify=false
    local run_test_flag=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --system-only)
                install_python=false
                install_fonts=false
                verify=false
                shift
                ;;
            --python-only)
                install_system=false
                install_fonts=false
                verify=false
                shift
                ;;
            --fonts-only)
                install_system=false
                install_python=false
                verify=false
                shift
                ;;
            --verify)
                install_system=false
                install_python=false
                install_fonts=false
                verify=true
                shift
                ;;
            --test)
                run_test_flag=true
                shift
                ;;
            --skip-system)
                install_system=false
                shift
                ;;
            --skip-fonts)
                install_fonts=false
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_info "PDF 生成工具依赖安装"
    echo ""
    
    # 执行安装步骤
    if [ "$install_system" = true ]; then
        install_system_dependencies
        echo ""
    fi
    
    if [ "$install_python" = true ]; then
        install_python_dependencies
        echo ""
    fi
    
    if [ "$install_fonts" = true ]; then
        install_fonts
        echo ""
    fi
    
    # 验证安装
    if [ "$verify" = true ] || [ "$install_system" = true ] || [ "$install_python" = true ]; then
        if verify_installation; then
            echo ""
        else
            exit 1
        fi
    fi
    
    # 运行测试
    if [ "$run_test_flag" = true ]; then
        echo ""
        if run_test; then
            echo ""
        else
            exit 1
        fi
    fi
    
    print_success "安装完成！"
    
    if [ "$install_system" = true ] || [ "$install_python" = true ]; then
        echo ""
        print_info "现在你可以使用以下命令生成 PDF:"
        echo "  python3 scripts/generate-pdf.py README.md"
        echo "  ./scripts/batch-generate-pdf.sh --single README.md"
        echo "  ./scripts/batch-generate-pdf.sh -c -i . output"
    fi
}

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi