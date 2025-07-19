#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions SSH 使用指南 PDF 生成器
支持从 Markdown 文件生成精美的 PDF 文档
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

try:
    import markdown
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
except ImportError as e:
    print(f"❌ 缺少必要的依赖包: {e}")
    print("请安装: pip install markdown weasyprint")
    sys.exit(1)

class PDFGenerator:
    def __init__(self):
        self.font_config = FontConfiguration()
        self.css_styles = self._get_css_styles()
        
    def _get_css_styles(self):
        """定义 PDF 样式"""
        return """
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&family=Fira+Code:wght@300;400;500&display=swap');
        
        body {
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            margin: 0;
            padding: 20px;
            font-size: 14px;
        }
        
        /* 页面设置 */
        @page {
            size: A4;
            margin: 2cm;
            @top-center {
                content: "GitHub Actions SSH 使用指南";
                font-size: 10px;
                color: #666;
            }
            @bottom-center {
                content: "第 " counter(page) " 页";
                font-size: 10px;
                color: #666;
            }
        }
        
        /* 标题样式 */
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
            font-size: 24px;
            page-break-before: always;
        }
        
        h1:first-child {
            page-break-before: avoid;
        }
        
        h2 {
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
            margin-top: 30px;
            font-size: 20px;
        }
        
        h3 {
            color: #2c3e50;
            margin-top: 25px;
            font-size: 16px;
        }
        
        h4 {
            color: #34495e;
            margin-top: 20px;
            font-size: 14px;
        }
        
        /* 代码样式 */
        code {
            font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
            color: #e74c3c;
        }
        
        pre {
            font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
            background-color: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 11px;
            line-height: 1.4;
            margin: 15px 0;
            page-break-inside: avoid;
        }
        
        pre code {
            background: none;
            padding: 0;
            color: inherit;
            font-size: inherit;
        }
        
        /* 列表样式 */
        ul, ol {
            margin: 10px 0;
            padding-left: 20px;
        }
        
        li {
            margin: 5px 0;
        }
        
        /* 表格样式 */
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            font-size: 12px;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 500;
        }
        
        /* 引用样式 */
        blockquote {
            border-left: 4px solid #3498db;
            margin: 15px 0;
            padding: 10px 15px;
            background-color: #f8f9fa;
            font-style: italic;
        }
        
        /* 链接样式 */
        a {
            color: #3498db;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        /* 图片样式 */
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 15px auto;
        }
        
        /* 徽章样式 */
        .badge {
            display: inline-block;
            padding: 3px 8px;
            font-size: 10px;
            font-weight: bold;
            border-radius: 12px;
            margin: 2px;
        }
        
        .badge-success {
            background-color: #28a745;
            color: white;
        }
        
        .badge-warning {
            background-color: #ffc107;
            color: #212529;
        }
        
        .badge-danger {
            background-color: #dc3545;
            color: white;
        }
        
        .badge-info {
            background-color: #17a2b8;
            color: white;
        }
        
        /* 提示框样式 */
        .alert {
            padding: 12px;
            margin: 15px 0;
            border-radius: 4px;
            border-left: 4px solid;
        }
        
        .alert-info {
            background-color: #d1ecf1;
            border-color: #bee5eb;
            color: #0c5460;
        }
        
        .alert-warning {
            background-color: #fff3cd;
            border-color: #ffeaa7;
            color: #856404;
        }
        
        .alert-success {
            background-color: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
        }
        
        .alert-danger {
            background-color: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }
        
        /* 目录样式 */
        .toc {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .toc h2 {
            margin-top: 0;
            color: #495057;
            border-bottom: none;
        }
        
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .toc li {
            margin: 8px 0;
        }
        
        .toc a {
            text-decoration: none;
            color: #007bff;
        }
        
        /* 页面分隔 */
        .page-break {
            page-break-before: always;
        }
        
        /* 首页样式 */
        .cover-page {
            text-align: center;
            padding: 100px 0;
        }
        
        .cover-title {
            font-size: 36px;
            color: #2c3e50;
            margin-bottom: 20px;
            font-weight: 700;
        }
        
        .cover-subtitle {
            font-size: 18px;
            color: #7f8c8d;
            margin-bottom: 40px;
        }
        
        .cover-meta {
            font-size: 14px;
            color: #95a5a6;
        }
        
        /* 脚注样式 */
        .footnote {
            font-size: 10px;
            color: #6c757d;
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #e9ecef;
        }
        
        /* Emoji 支持 */
        .emoji {
            font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;
        }
        """
    
    def _markdown_to_html(self, markdown_file):
        """将 Markdown 转换为 HTML"""
        print(f"📖 读取 Markdown 文件: {markdown_file}")
        
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # 配置 Markdown 扩展
        md = markdown.Markdown(
            extensions=[
                'codehilite',
                'fenced_code',
                'tables',
                'toc',
                'attr_list',
                'def_list',
                'footnotes',
                'md_in_html'
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True
                },
                'toc': {
                    'permalink': True,
                    'title': '目录'
                }
            }
        )
        
        # 预处理 Markdown 内容
        markdown_content = self._preprocess_markdown(markdown_content)
        
        # 转换为 HTML
        html_content = md.convert(markdown_content)
        
        # 生成完整的 HTML 文档
        full_html = self._create_full_html(html_content, md.toc)
        
        return full_html
    
    def _preprocess_markdown(self, content):
        """预处理 Markdown 内容"""
        # 添加封面页
        cover_page = f"""
<div class="cover-page">
    <h1 class="cover-title">GitHub Actions SSH 使用指南</h1>
    <p class="cover-subtitle">完整的 SSH 密钥配置与自动化部署指南</p>
    <div class="cover-meta">
        <p>生成时间: {datetime.now().strftime('%Y年%m月%d日')}</p>
        <p>版本: v1.0</p>
    </div>
</div>

<div class="page-break"></div>

"""
        
        # 处理特殊标记
        content = content.replace('🔐', '<span class="emoji">🔐</span>')
        content = content.replace('🚀', '<span class="emoji">🚀</span>')
        content = content.replace('✅', '<span class="emoji">✅</span>')
        content = content.replace('❌', '<span class="emoji">❌</span>')
        content = content.replace('⚠️', '<span class="emoji">⚠️</span>')
        content = content.replace('📖', '<span class="emoji">📖</span>')
        content = content.replace('💡', '<span class="emoji">💡</span>')
        content = content.replace('🛠️', '<span class="emoji">🛠️</span>')
        content = content.replace('🌟', '<span class="emoji">🌟</span>')
        content = content.replace('🔒', '<span class="emoji">🔒</span>')
        
        return cover_page + content
    
    def _create_full_html(self, body_content, toc):
        """创建完整的 HTML 文档"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Actions SSH 使用指南</title>
    <style>{self.css_styles}</style>
</head>
<body>
    {body_content}
    
    <div class="footnote">
        <p>本文档由 GitHub Actions SSH 指南生成器自动生成</p>
        <p>更多信息请访问: https://github.com/actions</p>
    </div>
</body>
</html>
"""
    
    def generate_pdf(self, markdown_file, output_file):
        """生成 PDF 文件"""
        print(f"🔄 开始生成 PDF: {output_file}")
        
        try:
            # 转换 Markdown 到 HTML
            html_content = self._markdown_to_html(markdown_file)
            
            # 创建临时 HTML 文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', 
                                           encoding='utf-8', delete=False) as f:
                f.write(html_content)
                temp_html = f.name
            
            print(f"📝 生成临时 HTML 文件: {temp_html}")
            
            # 使用 WeasyPrint 生成 PDF
            html_doc = HTML(filename=temp_html)
            css_doc = CSS(string=self.css_styles, font_config=self.font_config)
            
            print("🖨️ 正在生成 PDF...")
            html_doc.write_pdf(output_file, stylesheets=[css_doc], 
                             font_config=self.font_config)
            
            # 清理临时文件
            os.unlink(temp_html)
            
            print(f"✅ PDF 生成成功: {output_file}")
            
            # 显示文件信息
            file_size = os.path.getsize(output_file)
            print(f"📊 文件大小: {file_size / 1024:.1f} KB")
            
        except Exception as e:
            print(f"❌ PDF 生成失败: {e}")
            if 'temp_html' in locals():
                os.unlink(temp_html)
            raise

def main():
    parser = argparse.ArgumentParser(description='GitHub Actions SSH 使用指南 PDF 生成器')
    parser.add_argument('input', help='输入的 Markdown 文件路径')
    parser.add_argument('-o', '--output', help='输出的 PDF 文件路径')
    parser.add_argument('--css', help='自定义 CSS 样式文件')
    parser.add_argument('--font-size', type=int, default=14, help='基础字体大小')
    parser.add_argument('--margin', default='2cm', help='页面边距')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"❌ 输入文件不存在: {args.input}")
        sys.exit(1)
    
    # 设置输出文件
    if args.output:
        output_file = args.output
    else:
        input_path = Path(args.input)
        output_file = input_path.parent / f"{input_path.stem}.pdf"
    
    # 确保输出目录存在
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 生成 PDF
    try:
        generator = PDFGenerator()
        
        # 如果提供了自定义 CSS，则加载
        if args.css and os.path.exists(args.css):
            with open(args.css, 'r', encoding='utf-8') as f:
                generator.css_styles = f.read()
        
        generator.generate_pdf(args.input, str(output_file))
        
        print(f"\n🎉 PDF 文档生成完成!")
        print(f"📁 输出文件: {output_file}")
        
    except Exception as e:
        print(f"❌ 生成过程中出现错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()