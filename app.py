import os
import json
import uuid
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from multi_perspective_analyzer import analyze_text
from url_extractor import extract_content_from_url, is_valid_url
from html_generator import generate_html_report
from image_generator import generate_image, save_image, IMAGE_STYLES
from exporter import export_markdown, export_pdf

app = Flask(__name__)
CORS(app)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images')

for directory in [REPORTS_DIR, IMAGES_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

image_tasks: Dict[str, Dict[str, Any]] = {}
tasks_lock = threading.Lock()

analysis_results: Dict[str, Dict[str, Any]] = {}
results_lock = threading.Lock()


def update_task_status(task_id: str, status: str, progress: int = 0, image_url: str = None, error: str = None):
    with tasks_lock:
        if task_id in image_tasks:
            image_tasks[task_id].update({
                'status': status,
                'progress': progress,
                'image_url': image_url,
                'error': error,
                'updated_at': datetime.now().isoformat()
            })


def generate_image_task(task_id: str, event_description: str, analysis_data: Dict, style: str = "infographic"):
    try:
        update_task_status(task_id, 'processing', progress=10)
        
        update_task_status(task_id, 'processing', progress=30)
        
        image_data, text_response = generate_image(event_description, analysis_data, style)
        
        update_task_status(task_id, 'processing', progress=70)
        
        if image_data:
            filename = save_image(image_data, IMAGES_DIR, prefix=f"img_{task_id[:8]}")
            image_url = f'/static/images/{filename}'
            update_task_status(task_id, 'completed', progress=100, image_url=image_url)
        else:
            update_task_status(task_id, 'failed', progress=0, error=text_response or 'Image generation failed')
            
    except Exception as e:
        update_task_status(task_id, 'failed', progress=0, error=str(e))

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
        image_style = data.get('image_style', 'infographic')
        
        if not content:
            return jsonify({
                'success': False,
                'error': '输入内容不能为空'
            }), 400
        
        if image_style not in IMAGE_STYLES:
            image_style = 'infographic'
        
        original_content = content
        
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
        
        task_id = str(uuid.uuid4())
        with tasks_lock:
            image_tasks[task_id] = {
                'task_id': task_id,
                'status': 'pending',
                'progress': 0,
                'image_url': None,
                'error': None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        
        analysis_data = {
            'user_perspective': result.get('user_perspective', ''),
            'product_perspective': result.get('product_perspective', ''),
            'topic_perspective': result.get('topic_perspective', ''),
            'course_perspective': result.get('course_perspective', ''),
            'final_conclusion': result.get('final_conclusion', ''),
        }
        
        thread = threading.Thread(
            target=generate_image_task,
            args=(task_id, original_content, analysis_data, image_style)
        )
        thread.daemon = True
        thread.start()
        
        result_id = str(uuid.uuid4())
        
        response_data = {
            'success': True,
            'result_id': result_id,
            'data': {
                'input_text': result.get('input_text', ''),
                'user_perspective': result.get('user_perspective', ''),
                'product_perspective': result.get('product_perspective', ''),
                'topic_perspective': result.get('topic_perspective', ''),
                'course_perspective': result.get('course_perspective', ''),
                'final_conclusion': result.get('final_conclusion', ''),
            },
            'html_report': f'/reports/{html_filename}' if html_filename else None,
            'image_task_id': task_id,
            'image_styles': list(IMAGE_STYLES.keys())
        }
        
        with results_lock:
            analysis_results[result_id] = {
                'result_id': result_id,
                'analysis_data': response_data['data'],
                'image_task_id': task_id,
                'created_at': datetime.now().isoformat()
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

@app.route('/static/images/<filename>')
def get_image(filename):
    return send_from_directory(IMAGES_DIR, filename)

@app.route('/api/image-status/<task_id>')
def get_image_status(task_id):
    with tasks_lock:
        task = image_tasks.get(task_id)
    
    if not task:
        return jsonify({
            'success': False,
            'error': 'Task not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': task
    })

@app.route('/api/image-styles')
def get_image_styles():
    return jsonify({
        'success': True,
        'data': IMAGE_STYLES
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': '多视角分析Agent服务正常运行'
    })

@app.route('/api/export/markdown', methods=['POST'])
def export_to_markdown():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        result_id = data.get('result_id')
        
        if not result_id:
            return jsonify({
                'success': False,
                'error': '缺少 result_id 参数'
            }), 400
        
        with results_lock:
            result = analysis_results.get(result_id)
        
        if not result:
            return jsonify({
                'success': False,
                'error': '未找到对应的分析结果'
            }), 404
        
        analysis_data = result.get('analysis_data', {})
        image_task_id = result.get('image_task_id')
        
        image_url = None
        image_local_path = None
        
        if image_task_id:
            with tasks_lock:
                image_task = image_tasks.get(image_task_id)
            
            if image_task and image_task.get('status') == 'completed':
                image_url = image_task.get('image_url')
                if image_url and image_url.startswith('/static/images/'):
                    image_filename = image_url.replace('/static/images/', '')
                    image_local_path = os.path.join(IMAGES_DIR, image_filename)
        
        try:
            filename, filepath = export_markdown(
                analysis_data,
                REPORTS_DIR,
                image_url,
                image_local_path
            )
            
            download_url = f'/reports/{filename}'
            
            return jsonify({
                'success': True,
                'data': {
                    'filename': filename,
                    'download_url': download_url,
                    'file_path': filepath
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Markdown导出失败: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'导出过程中发生错误: {str(e)}'
        }), 500

@app.route('/api/export/pdf', methods=['POST'])
def export_to_pdf():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        result_id = data.get('result_id')
        
        if not result_id:
            return jsonify({
                'success': False,
                'error': '缺少 result_id 参数'
            }), 400
        
        with results_lock:
            result = analysis_results.get(result_id)
        
        if not result:
            return jsonify({
                'success': False,
                'error': '未找到对应的分析结果'
            }), 404
        
        analysis_data = result.get('analysis_data', {})
        image_task_id = result.get('image_task_id')
        
        image_url = None
        image_local_path = None
        
        if image_task_id:
            with tasks_lock:
                image_task = image_tasks.get(image_task_id)
            
            if image_task and image_task.get('status') == 'completed':
                image_url = image_task.get('image_url')
                if image_url and image_url.startswith('/static/images/'):
                    image_filename = image_url.replace('/static/images/', '')
                    image_local_path = os.path.join(IMAGES_DIR, image_filename)
        
        try:
            filename, filepath = export_pdf(
                analysis_data,
                REPORTS_DIR,
                image_url,
                image_local_path
            )
            
            download_url = f'/reports/{filename}'
            
            return jsonify({
                'success': True,
                'data': {
                    'filename': filename,
                    'download_url': download_url,
                    'file_path': filepath
                }
            })
            
        except ImportError as e:
            return jsonify({
                'success': False,
                'error': f'PDF导出依赖库未安装: {str(e)}'
            }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'PDF导出失败: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'导出过程中发生错误: {str(e)}'
        }), 500

@app.route('/api/export/all', methods=['POST'])
def export_all():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        result_id = data.get('result_id')
        
        if not result_id:
            return jsonify({
                'success': False,
                'error': '缺少 result_id 参数'
            }), 400
        
        with results_lock:
            result = analysis_results.get(result_id)
        
        if not result:
            return jsonify({
                'success': False,
                'error': '未找到对应的分析结果'
            }), 404
        
        analysis_data = result.get('analysis_data', {})
        image_task_id = result.get('image_task_id')
        
        image_url = None
        image_local_path = None
        
        if image_task_id:
            with tasks_lock:
                image_task = image_tasks.get(image_task_id)
            
            if image_task and image_task.get('status') == 'completed':
                image_url = image_task.get('image_url')
                if image_url and image_url.startswith('/static/images/'):
                    image_filename = image_url.replace('/static/images/', '')
                    image_local_path = os.path.join(IMAGES_DIR, image_filename)
        
        results = {}
        
        try:
            md_filename, md_filepath = export_markdown(
                analysis_data,
                REPORTS_DIR,
                image_url,
                image_local_path
            )
            results['markdown'] = {
                'filename': md_filename,
                'download_url': f'/reports/{md_filename}'
            }
        except Exception as e:
            results['markdown'] = {
                'error': f'Markdown导出失败: {str(e)}'
            }
        
        try:
            pdf_filename, pdf_filepath = export_pdf(
                analysis_data,
                REPORTS_DIR,
                image_url,
                image_local_path
            )
            results['pdf'] = {
                'filename': pdf_filename,
                'download_url': f'/reports/{pdf_filename}'
            }
        except Exception as e:
            results['pdf'] = {
                'error': f'PDF导出失败: {str(e)}'
            }
        
        return jsonify({
            'success': True,
            'data': results
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'导出过程中发生错误: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("    🤖 多视角分析 Agent Web 服务")
    print("=" * 60)
    print("\n📌 服务地址: http://localhost:5000")
    print("📌 API文档:")
    print("   - GET  /                        -> 主页")
    print("   - POST /api/analyze             -> 分析接口")
    print("   - GET  /api/image-status/<id>    -> 图片生成状态")
    print("   - GET  /api/image-styles        -> 图片风格列表")
    print("   - POST /api/export/markdown    -> 导出Markdown")
    print("   - POST /api/export/pdf          -> 导出PDF")
    print("   - POST /api/export/all           -> 导出所有格式")
    print("   - GET  /api/health              -> 健康检查")
    print("\n🚀 服务启动中...")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
