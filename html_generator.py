import re
from datetime import datetime
from typing import Dict, Optional
import html

def markdown_to_html(text: str) -> str:
    if not text:
        return ""
    
    text = html.escape(text, quote=False)
    
    text = re.sub(r'\n{2,}', '</p><p class="mb-4">', text)
    
    lines = text.split('\n')
    result_lines = []
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        h1_match = re.match(r'^#{1}\s+(.+)$', line)
        if h1_match:
            result_lines.append(f'<h1 class="text-3xl font-bold text-gray-800 mb-4 mt-6">{h1_match.group(1)}</h1>')
            continue
        
        h2_match = re.match(r'^#{2}\s+(.+)$', line)
        if h2_match:
            result_lines.append(f'<h2 class="text-2xl font-semibold text-gray-700 mb-3 mt-5">{h2_match.group(1)}</h2>')
            continue
        
        h3_match = re.match(r'^#{3}\s+(.+)$', line)
        if h3_match:
            result_lines.append(f'<h3 class="text-xl font-medium text-gray-700 mb-2 mt-4">{h3_match.group(1)}</h3>')
            continue
        
        h4_match = re.match(r'^#{4,6}\s+(.+)$', line)
        if h4_match:
            result_lines.append(f'<h4 class="text-lg font-medium text-gray-600 mb-2 mt-3">{h4_match.group(1)}</h4>')
            continue
        
        ul_match = re.match(r'^[\*\-\+]\s+(.+)$', line)
        if ul_match:
            result_lines.append(f'<li class="ml-6 mb-2 text-gray-700 list-disc">{ul_match.group(1)}</li>')
            continue
        
        ol_match = re.match(r'^\d+\.\s+(.+)$', line)
        if ol_match:
            result_lines.append(f'<li class="ml-6 mb-2 text-gray-700 list-decimal">{ol_match.group(1)}</li>')
            continue
        
        bold_matches = re.findall(r'\*\*(.+?)\*\*', line)
        for match in bold_matches:
            line = line.replace(f'**{match}**', f'<strong class="font-semibold text-gray-800">{match}</strong>')
        
        italic_matches = re.findall(r'(?<!\*)\*(.+?)\*(?!\*)', line)
        for match in italic_matches:
            line = line.replace(f'*{match}*', f'<em class="italic text-gray-600">{match}</em>')
        
        result_lines.append(f'<p class="mb-3 text-gray-700 leading-relaxed">{line}</p>')
    
    final_html = '\n'.join(result_lines)
    
    final_html = re.sub(r'</li>\s*<li class="ml-6 mb-2 text-gray-700 list-disc">', '</li>\n<li class="ml-6 mb-2 text-gray-700 list-disc">', final_html)
    final_html = re.sub(r'</li>\s*<li class="ml-6 mb-2 text-gray-700 list-decimal">', '</li>\n<li class="ml-6 mb-2 text-gray-700 list-decimal">', final_html)
    
    return final_html

def generate_html_report(result: Dict, output_path: Optional[str] = None) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    input_text_html = markdown_to_html(result.get('input_text', ''))
    user_html = markdown_to_html(result.get('user_perspective', ''))
    product_html = markdown_to_html(result.get('product_perspective', ''))
    topic_html = markdown_to_html(result.get('topic_perspective', ''))
    course_html = markdown_to_html(result.get('course_perspective', ''))
    conclusion_html = markdown_to_html(result.get('final_conclusion', ''))
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>多视角分析报告</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');
        
        * {{
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        
        .gradient-bg {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        .card-hover {{
            transition: all 0.3s ease;
        }}
        
        .card-hover:hover {{
            transform: translateY(-2px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }}
        
        .perspective-card {{
            border-left: 4px solid;
        }}
        
        .user-card {{
            border-left-color: #3b82f6;
        }}
        
        .product-card {{
            border-left-color: #10b981;
        }}
        
        .topic-card {{
            border-left-color: #f59e0b;
        }}
        
        .course-card {{
            border-left-color: #8b5cf6;
        }}
        
        .conclusion-card {{
            border-left-color: #ec4899;
            background: linear-gradient(135deg, #fdf4ff 0%, #f5f3ff 100%);
        }}
        
        .tab-active {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .tab-inactive {{
            background: #f3f4f6;
            color: #6b7280;
        }}
        
        .tab-inactive:hover {{
            background: #e5e7eb;
        }}
        
        .fade-in {{
            animation: fadeIn 0.5s ease-in-out;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .scroll-smooth {{
            scroll-behavior: smooth;
        }}
        
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f5f9;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #cbd5e1;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #94a3b8;
        }}
    </style>
</head>
<body class="bg-gray-50 min-h-screen scroll-smooth">
    <header class="gradient-bg text-white py-12 px-6">
        <div class="max-w-5xl mx-auto">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-4xl font-bold mb-3">📊 多视角分析报告</h1>
                    <p class="text-purple-100 text-lg">从五个维度深度洞察事件本质</p>
                </div>
                <div class="text-right">
                    <p class="text-purple-200 text-sm">生成时间</p>
                    <p class="text-white font-medium">{timestamp}</p>
                </div>
            </div>
        </div>
    </header>

    <nav class="sticky top-0 bg-white shadow-md z-50">
        <div class="max-w-5xl mx-auto px-6">
            <div class="flex space-x-2 py-3 overflow-x-auto">
                <button onclick="scrollToSection('input')" class="tab-inactive px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all">
                    📝 原始输入
                </button>
                <button onclick="scrollToSection('user')" class="tab-inactive px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all">
                    👤 用户思维
                </button>
                <button onclick="scrollToSection('product')" class="tab-inactive px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all">
                    💡 产品思维
                </button>
                <button onclick="scrollToSection('topic')" class="tab-inactive px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all">
                    📰 选题思维
                </button>
                <button onclick="scrollToSection('course')" class="tab-inactive px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all">
                    📚 课程思维
                </button>
                <button onclick="scrollToSection('conclusion')" class="tab-active px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all">
                    🎯 综合结论
                </button>
            </div>
        </div>
    </nav>

    <main class="max-w-5xl mx-auto px-6 py-10">
        
        <section id="input" class="mb-10 fade-in">
            <div class="bg-white rounded-2xl shadow-lg p-8 card-hover">
                <div class="flex items-center mb-6">
                    <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
                        <span class="text-2xl">📝</span>
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-gray-800">原始输入</h2>
                        <p class="text-gray-500 text-sm">分析的事件内容</p>
                    </div>
                </div>
                <div class="bg-gray-50 rounded-xl p-6 border border-gray-200">
                    <div class="prose max-w-none">
                        {input_text_html}
                    </div>
                </div>
            </div>
        </section>

        <section id="user" class="mb-10 fade-in">
            <div class="bg-white rounded-2xl shadow-lg p-8 card-hover perspective-card user-card">
                <div class="flex items-center mb-6">
                    <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
                        <span class="text-2xl">👤</span>
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-gray-800">视角一：用户思维</h2>
                        <p class="text-gray-500 text-sm">相关人群的真实感受、担忧与期待</p>
                    </div>
                </div>
                <div class="bg-blue-50 rounded-xl p-6 border border-blue-100">
                    <div class="prose max-w-none">
                        {user_html}
                    </div>
                </div>
            </div>
        </section>

        <section id="product" class="mb-10 fade-in">
            <div class="bg-white rounded-2xl shadow-lg p-8 card-hover perspective-card product-card">
                <div class="flex items-center mb-6">
                    <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mr-4">
                        <span class="text-2xl">💡</span>
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-gray-800">视角二：产品思维</h2>
                        <p class="text-gray-500 text-sm">需求缺口分析与产品解决方案</p>
                    </div>
                </div>
                <div class="bg-green-50 rounded-xl p-6 border border-green-100">
                    <div class="prose max-w-none">
                        {product_html}
                    </div>
                </div>
            </div>
        </section>

        <section id="topic" class="mb-10 fade-in">
            <div class="bg-white rounded-2xl shadow-lg p-8 card-hover perspective-card topic-card">
                <div class="flex items-center mb-6">
                    <div class="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center mr-4">
                        <span class="text-2xl">📰</span>
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-gray-800">视角三：选题思维</h2>
                        <p class="text-gray-500 text-sm">社会情绪洞察与传播价值分析</p>
                    </div>
                </div>
                <div class="bg-amber-50 rounded-xl p-6 border border-amber-100">
                    <div class="prose max-w-none">
                        {topic_html}
                    </div>
                </div>
            </div>
        </section>

        <section id="course" class="mb-10 fade-in">
            <div class="bg-white rounded-2xl shadow-lg p-8 card-hover perspective-card course-card">
                <div class="flex items-center mb-6">
                    <div class="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mr-4">
                        <span class="text-2xl">📚</span>
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-gray-800">视角四：课程思维</h2>
                        <p class="text-gray-500 text-sm">可提炼的方法论与教育价值</p>
                    </div>
                </div>
                <div class="bg-purple-50 rounded-xl p-6 border border-purple-100">
                    <div class="prose max-w-none">
                        {course_html}
                    </div>
                </div>
            </div>
        </section>

        <section id="conclusion" class="mb-10 fade-in">
            <div class="bg-white rounded-2xl shadow-lg p-8 card-hover perspective-card conclusion-card">
                <div class="flex items-center mb-6">
                    <div class="w-12 h-12 bg-pink-100 rounded-xl flex items-center justify-center mr-4">
                        <span class="text-2xl">🎯</span>
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-gray-800">跨维度综合结论</h2>
                        <p class="text-gray-500 text-sm">整合四维度分析的深度洞察</p>
                    </div>
                </div>
                <div class="bg-gradient-to-r from-pink-50 to-purple-50 rounded-xl p-6 border border-pink-200">
                    <div class="prose max-w-none">
                        {conclusion_html}
                    </div>
                </div>
            </div>
        </section>

    </main>

    <footer class="bg-gray-800 text-gray-400 py-8 px-6 mt-12">
        <div class="max-w-5xl mx-auto text-center">
            <p class="mb-2">🤖 多视角分析 Agent</p>
            <p class="text-sm text-gray-500">报告生成时间: {timestamp}</p>
            <p class="text-xs text-gray-600 mt-4">Powered by LangGraph & Google Gemini</p>
        </div>
    </footer>

    <script>
        function scrollToSection(sectionId) {{
            const element = document.getElementById(sectionId);
            if (element) {{
                const offset = 80;
                const elementPosition = element.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - offset;
                
                window.scrollTo({{
                    top: offsetPosition,
                    behavior: 'smooth'
                }});
            }}
        }}

        const observerOptions = {{
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        }};

        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.classList.add('fade-in');
                }}
            }});
        }}, observerOptions);

        document.querySelectorAll('section').forEach(section => {{
            observer.observe(section);
        }});

        const sections = document.querySelectorAll('section');
        const navButtons = document.querySelectorAll('nav button');

        function updateActiveTab() {{
            let currentSection = 'conclusion';
            
            sections.forEach(section => {{
                const rect = section.getBoundingClientRect();
                if (rect.top <= 150) {{
                    currentSection = section.id;
                }}
            }});

            navButtons.forEach(button => {{
                const buttonSection = button.getAttribute('onclick')?.match(/'([^']+)'/)?.[1];
                if (buttonSection === currentSection) {{
                    button.classList.remove('tab-inactive');
                    button.classList.add('tab-active');
                }} else {{
                    button.classList.remove('tab-active');
                    button.classList.add('tab-inactive');
                }}
            }});
        }}

        window.addEventListener('scroll', updateActiveTab);
        updateActiveTab();
    </script>
</body>
</html>"""
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path
    
    return html_content

if __name__ == "__main__":
    test_result = {
        'input_text': 'AI造成了大量裁员\n\n近年来，人工智能技术的快速发展...',
        'user_perspective': '## 真实感受\n\n作为一名可能被AI影响的从业者，我感到...',
        'product_perspective': '## 需求缺口分析\n\n这个现象暴露了...',
        'topic_perspective': '## 时机洞察\n\nAI裁员话题此刻引发关注是因为...',
        'course_perspective': '## 方法论提炼\n\n从这个现象中可以提炼出...',
        'final_conclusion': '## 综合分析\n\n这四个维度之间存在着深刻的内在联系...'
    }
    
    output = generate_html_report(test_result, 'test_report.html')
    print(f"测试报告已生成: test_report.html")
