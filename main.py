import os
from datetime import datetime
from typing import Dict, Optional
from multi_perspective_analyzer import analyze_text, format_result
from url_extractor import extract_content_from_url, is_valid_url
from html_generator import generate_html_report

def get_input_mode() -> str:
    print("\n📋 请选择输入模式:")
    print("   1. 直接输入文本")
    print("   2. 输入URL地址")
    print("   0. 退出程序")
    
    while True:
        choice = input("\n请输入选项 (0/1/2): ").strip()
        if choice in ['0', '1', '2']:
            return choice
        print("⚠️  无效选项，请输入 0, 1 或 2")

def get_text_input() -> str:
    print("\n✍️  请输入新闻或现象描述（输入空行结束）：")
    print("-" * 60)
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "" and len(lines) > 0:
                break
            lines.append(line)
        except EOFError:
            break
    
    return '\n'.join(lines).strip()

def get_url_input() -> str:
    print("\n🌐 请输入新闻URL地址：")
    print("-" * 60)
    
    while True:
        url = input("\n� 请输入URL: ").strip()
        
        if url.lower() == 'exit':
            return None
        
        if not url:
            print("⚠️  URL不能为空，请重新输入。")
            continue
        
        if not is_valid_url(url):
            print("⚠️  URL格式不正确，请检查是否包含 http:// 或 https://")
            retry = input("是否重新输入? (y/n): ").strip().lower()
            if retry != 'y':
                return None
            continue
        
        return url

def generate_html_output(result: Dict) -> Optional[str]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.getcwd(), "reports")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_path = os.path.join(output_dir, f"analysis_report_{timestamp}.html")
    
    try:
        generate_html_report(result, output_path)
        return output_path
    except Exception as e:
        print(f"⚠️  生成HTML报告失败: {e}")
        return None

def analyze_with_content(content: str, source_type: str = "文本") -> Dict:
    print(f"\n🔍 正在分析{source_type}内容，请稍候...\n")
    
    result = analyze_text(content)
    formatted_output = format_result(result)
    
    print(formatted_output)
    
    return result

def main():
    print("=" * 60)
    print("        🤖 多视角分析 Agent")
    print("=" * 60)
    print("\n支持两种输入模式：直接输入文本 或 输入新闻URL")
    print("-" * 60)
    
    while True:
        try:
            mode = get_input_mode()
            
            if mode == '0':
                print("\n👋 感谢使用，再见！")
                break
            
            result = None
            
            if mode == '1':
                content = get_text_input()
                if not content:
                    print("⚠️  输入内容为空，请重新选择。")
                    continue
                
                print(f"\n✅ 成功获取文本内容 ({len(content)} 字符)")
                result = analyze_with_content(content, "文本")
            
            elif mode == '2':
                url = get_url_input()
                if not url:
                    continue
                
                print(f"\n📥 正在获取URL内容: {url}")
                try:
                    url_result = extract_content_from_url(url)
                    content = url_result['full_text']
                    
                    print(f"✅ 成功获取网页内容")
                    print(f"   标题: {url_result['title']}")
                    print(f"   内容长度: {len(url_result['content'])} 字符")
                    
                    result = analyze_with_content(content, "URL")
                    
                except Exception as e:
                    print(f"\n❌ 获取URL内容失败: {e}")
                    print("\n请检查:")
                    print("   1. URL是否正确")
                    print("   2. 网络连接是否正常")
                    print("   3. 网站是否需要特殊权限访问")
                    continue
            
            if result:
                print("\n" + "=" * 60)
                print("📄 是否生成HTML报告？")
                print("=" * 60)
                print("   y - 生成优美的HTML报告")
                print("   n - 不生成，继续使用")
                
                html_choice = input("\n请选择 (y/n): ").strip().lower()
                
                if html_choice == 'y':
                    print("\n📤 正在生成HTML报告...")
                    html_path = generate_html_output(result)
                    
                    if html_path:
                        print(f"\n✅ HTML报告已生成:")
                        print(f"   📁 保存位置: {html_path}")
                        print(f"\n💡 提示: 您可以用浏览器打开此文件查看美观的报告")
            
            print("\n" + "=" * 60)
            print("分析完成！选择下一步操作：")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 程序已中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            print("\n请检查您的GOOGLE_API_KEY是否正确设置，或稍后重试。")
            retry = input("是否继续使用? (y/n): ").strip().lower()
            if retry != 'y':
                print("\n👋 再见！")
                break

if __name__ == "__main__":
    main()
