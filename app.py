import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from multi_perspective_analyzer import analyze_text
from url_extractor import extract_content_from_url, is_valid_url
from html_generator import generate_html_report

app = Flask(__name__)
CORS(app)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        input_type = data.get('type', 'text')
        content = data.get('content', '')
        
        if not content:
            return jsonify({
                'success': False,
                'error': '输入内容不能为空'
            }), 400
        
        if input_type == 'url':
            if not is_valid_url(content):
                return jsonify({
                    'success': False,
                    'error': 'URL格式不正确，请确保包含 http:// 或 https://'
                }), 400
            
            try:
                url_result = extract_content_from_url(content)
                content = url_result['full_text']
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'获取URL内容失败: {str(e)}'
                }), 400
        
        result = analyze_text(content)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f'analysis_report_{timestamp}.html'
        html_path = os.path.join(REPORTS_DIR, html_filename)
        
        try:
            generate_html_report(result, html_path)
        except Exception as e:
            print(f'生成HTML报告失败: {e}')
            html_filename = None
        
        response_data = {
            'success': True,
            'data': {
                'input_text': result.get('input_text', ''),
                'user_perspective': result.get('user_perspective', ''),
                'product_perspective': result.get('product_perspective', ''),
                'topic_perspective': result.get('topic_perspective', ''),
                'course_perspective': result.get('course_perspective', ''),
                'final_conclusion': result.get('final_conclusion', ''),
            },
            'html_report': f'/reports/{html_filename}' if html_filename else None
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'分析过程中发生错误: {str(e)}'
        }), 500

@app.route('/reports/<filename>')
def get_report(filename):
    return send_from_directory(REPORTS_DIR, filename)

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': '多视角分析Agent服务正常运行'
    })

if __name__ == '__main__':
    print("=" * 60)
    print("    🤖 多视角分析 Agent Web 服务")
    print("=" * 60)
    print("\n📌 服务地址: http://localhost:5000")
    print("📌 API文档:")
    print("   - GET  /                -> 主页")
    print("   - POST /api/analyze    -> 分析接口")
    print("   - GET  /api/health      -> 健康检查")
    print("\n🚀 服务启动中...")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
