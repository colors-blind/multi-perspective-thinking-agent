import os
import re
from datetime import datetime
from typing import Dict, Optional, Tuple
from urllib.parse import quote


def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = filename.strip('_')
    return filename[:100] if len(filename) > 100 else filename


def get_export_title(input_text: str) -> str:
    lines = input_text.strip().split('\n')
    if lines:
        title = lines[0].strip()
        if len(title) > 50:
            title = title[:50] + '...'
        return title
    return '多视角分析报告'


def get_file_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def generate_markdown(
    analysis_data: Dict,
    image_url: Optional[str] = None,
    image_local_path: Optional[str] = None
) -> str:
    input_text = analysis_data.get('input_text', '')
    title = get_export_title(input_text)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    markdown_parts = []
    
    markdown_parts.append(f'# {title}\n')
    markdown_parts.append(f'> 生成时间：{timestamp}\n')
    markdown_parts.append(f'> 由多视角分析 Agent 生成\n\n')
    markdown_parts.append('---\n\n')
    
    if image_url or image_local_path:
        markdown_parts.append('## 🖼️ 分析插图\n\n')
        if image_local_path and os.path.exists(image_local_path):
            img_filename = os.path.basename(image_local_path)
            markdown_parts.append(f'![分析插图](./{img_filename})\n\n')
        elif image_url:
            markdown_parts.append(f'![分析插图]({image_url})\n\n')
    
    markdown_parts.append('## 📋 事件描述\n\n')
    markdown_parts.append(f'{input_text}\n\n')
    markdown_parts.append('---\n\n')
    
    user_perspective = analysis_data.get('user_perspective', '')
    if user_perspective:
        markdown_parts.append('## 👤 视角一：用户思维\n\n')
        markdown_parts.append('> 相关人群的真实感受、担忧与期待\n\n')
        markdown_parts.append(f'{user_perspective}\n\n')
        markdown_parts.append('---\n\n')
    
    product_perspective = analysis_data.get('product_perspective', '')
    if product_perspective:
        markdown_parts.append('## 💡 视角二：产品思维\n\n')
        markdown_parts.append('> 需求缺口分析与产品解决方案\n\n')
        markdown_parts.append(f'{product_perspective}\n\n')
        markdown_parts.append('---\n\n')
    
    topic_perspective = analysis_data.get('topic_perspective', '')
    if topic_perspective:
        markdown_parts.append('## 📰 视角三：选题思维\n\n')
        markdown_parts.append('> 社会情绪洞察与传播价值分析\n\n')
        markdown_parts.append(f'{topic_perspective}\n\n')
        markdown_parts.append('---\n\n')
    
    course_perspective = analysis_data.get('course_perspective', '')
    if course_perspective:
        markdown_parts.append('## 📚 视角四：课程思维\n\n')
        markdown_parts.append('> 可提炼的方法论与教育价值\n\n')
        markdown_parts.append(f'{course_perspective}\n\n')
        markdown_parts.append('---\n\n')
    
    final_conclusion = analysis_data.get('final_conclusion', '')
    if final_conclusion:
        markdown_parts.append('## 🎯 跨维度综合结论\n\n')
        markdown_parts.append('> 整合四维度分析的深度洞察\n\n')
        markdown_parts.append(f'{final_conclusion}\n\n')
    
    markdown_parts.append('---\n\n')
    markdown_parts.append('*本文档由多视角分析 Agent 自动生成*  \n')
    markdown_parts.append('*Powered by LangGraph & Google Gemini*\n')
    
    return ''.join(markdown_parts)


def generate_html_for_pdf(
    analysis_data: Dict,
    image_url: Optional[str] = None,
    image_local_path: Optional[str] = None
) -> str:
    input_text = analysis_data.get('input_text', '')
    title = get_export_title(input_text)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    image_html = ''
    
    if image_local_path and os.path.exists(image_local_path):
        import base64
        with open(image_local_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
        image_html = f'''
        <div class="image-section">
            <h2>🖼️ 分析插图</h2>
            <div class="image-container">
                <img src="data:image/png;base64,{img_data}" alt="分析插图" style="max-width: 100%; border-radius: 8px;">
            </div>
        </div>
        '''
    elif image_url:
        image_html = f'''
        <div class="image-section">
            <h2>🖼️ 分析插图</h2>
            <div class="image-container">
                <img src="{image_url}" alt="分析插图" style="max-width: 100%; border-radius: 8px;">
            </div>
        </div>
        '''
    
    def format_content(content):
        if not content:
            return ''
        lines = content.split('\n')
        formatted = []
        for line in lines:
            line = line.strip()
            if line:
                if re.match(r'^#{1,4}\s+', line):
                    line = re.sub(r'^#+\s+', '', line)
                    formatted.append(f'<h4>{line}</h4>')
                elif re.match(r'^[\*\-\+]\s+', line):
                    line = re.sub(r'^[\*\-\+]\s+', '', line)
                    formatted.append(f'<li>{line}</li>')
                elif re.match(r'^\d+\.\s+', line):
                    line = re.sub(r'^\d+\.\s+', '', line)
                    formatted.append(f'<li>{line}</li>')
                else:
                    line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                    line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
                    formatted.append(f'<p>{line}</p>')
        
        result = []
        in_list = False
        for item in formatted:
            if item.startswith('<li>'):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
            else:
                if in_list:
                    result.append('</ul>')
                    in_list = False
            result.append(item)
        if in_list:
            result.append('</ul>')
        
        return '\n'.join(result)
    
    html = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: 'Noto Sans SC', 'Microsoft YaHei', 'SimHei', sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 12px;
        }}
        h1 {{
            font-size: 24px;
            color: #1f2937;
            text-align: center;
            margin-bottom: 10px;
        }}
        h2 {{
            font-size: 16px;
            color: #374151;
            margin-top: 20px;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #667eea;
        }}
        h3 {{
            font-size: 14px;
            color: #4b5563;
            margin-top: 15px;
            margin-bottom: 8px;
        }}
        h4 {{
            font-size: 13px;
            color: #6b7280;
            margin-top: 12px;
            margin-bottom: 6px;
        }}
        .subtitle {{
            text-align: center;
            color: #6b7280;
            font-size: 11px;
            margin-bottom: 20px;
        }}
        .subtitle span {{
            margin: 0 10px;
        }}
        hr {{
            border: none;
            border-top: 1px solid #e5e7eb;
            margin: 20px 0;
        }}
        blockquote {{
            border-left: 3px solid #667eea;
            padding-left: 10px;
            margin: 10px 0;
            color: #6b7280;
            font-size: 11px;
        }}
        p {{
            margin: 8px 0;
        }}
        ul, ol {{
            margin: 8px 0;
            padding-left: 20px;
        }}
        li {{
            margin: 4px 0;
        }}
        strong {{
            color: #1f2937;
            font-weight: 600;
        }}
        em {{
            color: #6b7280;
            font-style: italic;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #9ca3af;
            font-size: 10px;
        }}
        .image-section {{
            margin: 15px 0;
        }}
        .image-container {{
            text-align: center;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="subtitle">
        <span>📅 生成时间：{timestamp}</span>
        <span>🤖 由多视角分析 Agent 生成</span>
    </div>
    <hr>
    
    {image_html}
    
    <h2>📋 事件描述</h2>
    {format_content(input_text)}
    <hr>
    
    <h2>👤 视角一：用户思维</h2>
    <blockquote>相关人群的真实感受、担忧与期待</blockquote>
    {format_content(analysis_data.get('user_perspective', ''))}
    <hr>
    
    <h2>💡 视角二：产品思维</h2>
    <blockquote>需求缺口分析与产品解决方案</blockquote>
    {format_content(analysis_data.get('product_perspective', ''))}
    <hr>
    
    <h2>📰 视角三：选题思维</h2>
    <blockquote>社会情绪洞察与传播价值分析</blockquote>
    {format_content(analysis_data.get('topic_perspective', ''))}
    <hr>
    
    <h2>📚 视角四：课程思维</h2>
    <blockquote>可提炼的方法论与教育价值</blockquote>
    {format_content(analysis_data.get('course_perspective', ''))}
    <hr>
    
    <h2>🎯 跨维度综合结论</h2>
    <blockquote>整合四维度分析的深度洞察</blockquote>
    {format_content(analysis_data.get('final_conclusion', ''))}
    
    <div class="footer">
        <p>本文档由多视角分析 Agent 自动生成</p>
        <p>Powered by LangGraph & Google Gemini</p>
    </div>
</body>
</html>
'''
    return html


def export_markdown(
    analysis_data: Dict,
    output_dir: str,
    image_url: Optional[str] = None,
    image_local_path: Optional[str] = None
) -> Tuple[str, str]:
    input_text = analysis_data.get('input_text', '')
    title = get_export_title(input_text)
    timestamp = get_file_timestamp()
    
    safe_title = sanitize_filename(title)
    filename = f'{safe_title}_{timestamp}.md'
    filepath = os.path.join(output_dir, filename)
    
    markdown_content = generate_markdown(analysis_data, image_url, image_local_path)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return filename, filepath


def export_pdf_with_weasyprint(
    analysis_data: Dict,
    output_dir: str,
    image_url: Optional[str] = None,
    image_local_path: Optional[str] = None
) -> Tuple[str, str]:
    input_text = analysis_data.get('input_text', '')
    title = get_export_title(input_text)
    timestamp = get_file_timestamp()
    
    safe_title = sanitize_filename(title)
    filename = f'{safe_title}_{timestamp}.pdf'
    filepath = os.path.join(output_dir, filename)
    
    html_content = generate_html_for_pdf(analysis_data, image_url, image_local_path)
    
    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(filepath)
        return filename, filepath
    except ImportError:
        raise ImportError('weasyprint not installed. Please install with: pip install weasyprint')


def export_pdf_with_pdfkit(
    analysis_data: Dict,
    output_dir: str,
    image_url: Optional[str] = None,
    image_local_path: Optional[str] = None
) -> Tuple[str, str]:
    input_text = analysis_data.get('input_text', '')
    title = get_export_title(input_text)
    timestamp = get_file_timestamp()
    
    safe_title = sanitize_filename(title)
    filename = f'{safe_title}_{timestamp}.pdf'
    filepath = os.path.join(output_dir, filename)
    
    html_content = generate_html_for_pdf(analysis_data, image_url, image_local_path)
    
    try:
        import pdfkit
        options = {
            'page-size': 'A4',
            'margin-top': '2cm',
            'margin-right': '2cm',
            'margin-bottom': '2cm',
            'margin-left': '2cm',
            'encoding': 'UTF-8',
            'no-outline': None,
        }
        pdfkit.from_string(html_content, filepath, options=options)
        return filename, filepath
    except ImportError:
        raise ImportError('pdfkit not installed. Please install with: pip install pdfkit')


def export_pdf(
    analysis_data: Dict,
    output_dir: str,
    image_url: Optional[str] = None,
    image_local_path: Optional[str] = None
) -> Tuple[str, str]:
    errors = []
    
    try:
        return export_pdf_with_weasyprint(analysis_data, output_dir, image_url, image_local_path)
    except ImportError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f'weasyprint error: {e}')
    
    try:
        return export_pdf_with_pdfkit(analysis_data, output_dir, image_url, image_local_path)
    except ImportError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f'pdfkit error: {e}')
    
    raise Exception(f'PDF导出失败，请安装依赖库。错误信息：{"; ".join(errors)}')


if __name__ == '__main__':
    test_data = {
        'input_text': 'AI造成了大量裁员\n\n近年来，人工智能技术的快速发展引发了广泛的社会关注...',
        'user_perspective': '## 真实感受\n作为一名可能被AI影响的从业者，我感到焦虑和不安...',
        'product_perspective': '## 需求缺口\n这个现象暴露了AI时代的职业转型需求...',
        'topic_perspective': '## 传播价值\n这个话题之所以引发关注，是因为它触及了...',
        'course_perspective': '## 可提炼的方法论\n从这个现象中可以提炼出以下方法论...',
        'final_conclusion': '## 综合结论\n综合四个维度的分析，我们可以看到...'
    }
    
    output_dir = './reports'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print('测试Markdown导出...')
    md_filename, md_filepath = export_markdown(test_data, output_dir)
    print(f'Markdown已保存: {md_filepath}')
    
    print('\n测试PDF导出...')
    try:
        pdf_filename, pdf_filepath = export_pdf(test_data, output_dir)
        print(f'PDF已保存: {pdf_filepath}')
    except Exception as e:
        print(f'PDF导出失败: {e}')
