from multi_perspective_analyzer import analyze_text, format_result

def main():
    print("=" * 60)
    print("        🤖 多视角分析 Agent")
    print("=" * 60)
    print("\n请输入一段新闻或现象描述（输入 'exit' 退出）：")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\n📝 请输入内容: ").strip()
            
            if user_input.lower() == 'exit':
                print("\n👋 感谢使用，再见！")
                break
            
            if not user_input:
                print("⚠️  输入不能为空，请重新输入。")
                continue
            
            print("\n🔍 正在进行多视角分析，请稍候...\n")
            
            result = analyze_text(user_input)
            formatted_output = format_result(result)
            
            print(formatted_output)
            
            print("\n" + "=" * 60)
            print("输入新的内容继续分析，或输入 'exit' 退出")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 程序已中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            print("\n请检查您的GOOGLE_API_KEY是否正确设置，或稍后重试。")

if __name__ == "__main__":
    main()
