#!/bin/bash
# 批量生成 PDF 文档脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印函数
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

# 检查 Python 和依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 未安装"
        return 1
    fi
    
    print_success "Python 3 已安装: $(python3 --version)"
    
    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 未安装"
        return 1
    fi
    
    # 检查 Python 依赖
    print_info "检查 Python 依赖包..."
    local missing_packages=()
    
    for package in markdown weasyprint pygments; do
        if ! python3 -c "import $package" 2>/dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -ne 0 ]; then
        print_warning "缺少 Python 依赖包: ${missing_packages[*]}"
        print_info "正在安装依赖包..."
        
        if pip3 install -r requirements.txt; then
            print_success "依赖包安装成功"
        else
            print_error "依赖包安装失败"
            return 1
        fi
    else
        print_success "所有 Python 依赖包已安装"
    fi
}

# 生成单个 PDF
generate_single_pdf() {
    local input_file="$1"
    local output_file="$2"
    
    print_info "生成 PDF: $(basename "$input_file")"
    
    if python3 scripts/generate-pdf.py "$input_file" -o "$output_file"; then
        print_success "PDF 生成成功: $output_file"
        return 0
    else
        print_error "PDF 生成失败: $input_file"
        return 1
    fi
}

# 批量生成 PDF
batch_generate() {
    local input_dir="$1"
    local output_dir="$2"
    
    print_info "开始批量生成 PDF..."
    print_info "输入目录: $input_dir"
    print_info "输出目录: $output_dir"
    
    # 创建输出目录
    mkdir -p "$output_dir"
    
    local success_count=0
    local fail_count=0
    local total_count=0
    
    # 查找所有 Markdown 文件
    while IFS= read -r -d '' markdown_file; do
        total_count=$((total_count + 1))
        
        # 获取相对路径和输出文件名
        local relative_path=$(realpath --relative-to="$input_dir" "$markdown_file")
        local output_file="$output_dir/${relative_path%.md}.pdf"
        
        # 创建输出子目录
        local output_subdir=$(dirname "$output_file")
        mkdir -p "$output_subdir"
        
        # 生成 PDF
        if generate_single_pdf "$markdown_file" "$output_file"; then
            success_count=$((success_count + 1))
        else
            fail_count=$((fail_count + 1))
        fi
        
    done < <(find "$input_dir" -name "*.md" -type f -print0)
    
    # 显示统计信息
    echo ""
    print_info "批量生成完成"
    echo "总计: $total_count 个文件"
    echo "成功: $success_count 个文件"
    if [ $fail_count -gt 0 ]; then
        echo "失败: $fail_count 个文件"
    fi
}

# 生成目录索引
generate_index() {
    local output_dir="$1"
    local index_file="$output_dir/index.html"
    
    print_info "生成 PDF 索引页面..."
    
    cat > "$index_file" << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Actions SSH 使用指南 - PDF 文档集</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        
        .pdf-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .pdf-card {
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            padding: 20px;
            background: #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .pdf-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .pdf-title {
            font-size: 16px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
        }
        
        .pdf-info {
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 15px;
        }
        
        .pdf-actions {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            text-decoration: none;
            font-size: 14px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .btn-primary {
            background-color: #3498db;
            color: white;
        }
        
        .btn-primary:hover {
            background-color: #2980b9;
        }
        
        .btn-secondary {
            background-color: #95a5a6;
            color: white;
        }
        
        .btn-secondary:hover {
            background-color: #7f8c8d;
        }
        
        .stats {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .stats h2 {
            margin-top: 0;
            color: #495057;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e1e8ed;
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <h1>📚 GitHub Actions SSH 使用指南</h1>
    <p>完整的 SSH 密钥配置与自动化部署指南 PDF 文档集</p>
    
    <div class="stats">
        <h2>📊 文档统计</h2>
        <div id="stats-content">
            <p>正在加载统计信息...</p>
        </div>
    </div>
    
    <div class="pdf-list" id="pdf-list">
        <!-- PDF 列表将通过 JavaScript 动态生成 -->
    </div>
    
    <div class="footer">
        <p>生成时间: <span id="generate-time"></span></p>
        <p>GitHub Actions SSH 使用指南 © 2024</p>
    </div>

    <script>
        // 设置生成时间
        document.getElementById('generate-time').textContent = new Date().toLocaleString('zh-CN');
        
        // 获取 PDF 文件列表
        async function loadPDFList() {
            try {
                // 这里应该从服务器获取 PDF 文件列表
                // 由于这是静态页面，我们先创建一个示例列表
                const pdfFiles = [
                    {
                        name: 'GitHub Actions SSH 使用指南',
                        filename: 'README.pdf',
                        size: '1.2 MB',
                        pages: '25 页',
                        description: '完整的 SSH 密钥配置与自动化部署指南'
                    }
                ];
                
                renderPDFList(pdfFiles);
                updateStats(pdfFiles);
                
            } catch (error) {
                console.error('加载 PDF 列表失败:', error);
            }
        }
        
        function renderPDFList(pdfFiles) {
            const container = document.getElementById('pdf-list');
            container.innerHTML = '';
            
            pdfFiles.forEach(pdf => {
                const card = document.createElement('div');
                card.className = 'pdf-card';
                card.innerHTML = `
                    <div class="pdf-title">${pdf.name}</div>
                    <div class="pdf-info">
                        📄 ${pdf.pages} • 📦 ${pdf.size}
                    </div>
                    <p>${pdf.description}</p>
                    <div class="pdf-actions">
                        <a href="${pdf.filename}" class="btn btn-primary" target="_blank">
                            📖 阅读
                        </a>
                        <a href="${pdf.filename}" class="btn btn-secondary" download>
                            💾 下载
                        </a>
                    </div>
                `;
                container.appendChild(card);
            });
        }
        
        function updateStats(pdfFiles) {
            const totalFiles = pdfFiles.length;
            const totalSize = pdfFiles.reduce((sum, pdf) => {
                const size = parseFloat(pdf.size.replace(/[^\d.]/g, ''));
                return sum + size;
            }, 0);
            
            document.getElementById('stats-content').innerHTML = `
                <p>📁 总文档数: ${totalFiles} 个</p>
                <p>📦 总大小: ${totalSize.toFixed(1)} MB</p>
                <p>🕒 最后更新: ${new Date().toLocaleDateString('zh-CN')}</p>
            `;
        }
        
        // 页面加载完成后执行
        document.addEventListener('DOMContentLoaded', loadPDFList);
    </script>
</body>
</html>
EOF

    print_success "索引页面生成完成: $index_file"
}

# 压缩 PDF 文件
compress_pdfs() {
    local output_dir="$1"
    
    print_info "压缩 PDF 文件..."
    
    if command -v ghostscript &> /dev/null || command -v gs &> /dev/null; then
        local gs_cmd="gs"
        if command -v ghostscript &> /dev/null; then
            gs_cmd="ghostscript"
        fi
        
        find "$output_dir" -name "*.pdf" -type f | while read -r pdf_file; do
            local compressed_file="${pdf_file%.pdf}_compressed.pdf"
            
            if $gs_cmd -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
                      -dPDFSETTINGS=/screen -dNOPAUSE -dQUIET \
                      -dBATCH -sOutputFile="$compressed_file" "$pdf_file"; then
                
                local original_size=$(stat -c%s "$pdf_file")
                local compressed_size=$(stat -c%s "$compressed_file")
                local reduction=$((100 - compressed_size * 100 / original_size))
                
                if [ $reduction -gt 10 ]; then
                    mv "$compressed_file" "$pdf_file"
                    print_success "压缩 $(basename "$pdf_file"): 减少 ${reduction}%"
                else
                    rm "$compressed_file"
                fi
            fi
        done
    else
        print_warning "未找到 Ghostscript，跳过 PDF 压缩"
    fi
}

# 显示帮助信息
show_help() {
    echo "GitHub Actions SSH 使用指南 PDF 批量生成工具"
    echo ""
    echo "用法:"
    echo "  $0 [选项] [输入目录] [输出目录]"
    echo ""
    echo "选项:"
    echo "  -h, --help      显示帮助信息"
    echo "  -c, --compress  压缩生成的 PDF 文件"
    echo "  -i, --index     生成索引页面"
    echo "  --single FILE   生成单个文件的 PDF"
    echo ""
    echo "示例:"
    echo "  $0 . output                    # 批量生成当前目录的 PDF"
    echo "  $0 --single README.md          # 生成单个文件的 PDF"
    echo "  $0 -c -i . pdfs               # 批量生成并压缩，创建索引"
}

# 主函数
main() {
    local compress=false
    local generate_index_page=false
    local single_file=""
    local input_dir="."
    local output_dir="output"
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--compress)
                compress=true
                shift
                ;;
            -i|--index)
                generate_index_page=true
                shift
                ;;
            --single)
                single_file="$2"
                shift 2
                ;;
            -*)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                if [ -z "$input_dir" ] || [ "$input_dir" = "." ]; then
                    input_dir="$1"
                elif [ -z "$output_dir" ] || [ "$output_dir" = "output" ]; then
                    output_dir="$1"
                fi
                shift
                ;;
        esac
    done
    
    print_info "GitHub Actions SSH 使用指南 PDF 生成工具"
    
    # 检查依赖
    if ! check_dependencies; then
        print_error "依赖检查失败"
        exit 1
    fi
    
    # 处理单个文件
    if [ -n "$single_file" ]; then
        if [ ! -f "$single_file" ]; then
            print_error "文件不存在: $single_file"
            exit 1
        fi
        
        local output_file="${single_file%.md}.pdf"
        generate_single_pdf "$single_file" "$output_file"
        exit $?
    fi
    
    # 检查输入目录
    if [ ! -d "$input_dir" ]; then
        print_error "输入目录不存在: $input_dir"
        exit 1
    fi
    
    # 批量生成
    batch_generate "$input_dir" "$output_dir"
    
    # 压缩 PDF
    if [ "$compress" = true ]; then
        compress_pdfs "$output_dir"
    fi
    
    # 生成索引页面
    if [ "$generate_index_page" = true ]; then
        generate_index "$output_dir"
    fi
    
    print_success "所有任务完成！"
    print_info "输出目录: $output_dir"
}

# 如果脚本被直接执行，运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi