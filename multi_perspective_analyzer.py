import os
import re
from typing import Dict, List, Annotated, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


def clean_llm_output(text: str) -> str:
    if not text:
        return ""
    
    text = text.strip()
    
    text = re.sub(r'^```[\w]*\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    
    text = re.sub(r'^(让我来分析一下|好的，我来|我来|下面|让我|首先|我将|接下来)[，。,.:：\s]*', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    text = re.sub(r'^(思考|思考过程|分析过程|我的思考|我的分析)[：:].*?\n\n', '', text, flags=re.DOTALL | re.MULTILINE | re.IGNORECASE)
    
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'【思考】.*?【/思考】', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    text = re.sub(r'^(注意|提示|说明|解释)[：:].*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    text = re.sub(r' +', ' ', text)
    
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.rstrip()
        if stripped:
            cleaned_lines.append(stripped)
    
    text = '\n'.join(cleaned_lines)
    
    return text.strip()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_KEY = 'AIzaSyCC0gj4MrHL-73NSSS6n8bsKSJMFcCrOD8'
if not GOOGLE_API_KEY:
    raise ValueError("请设置GOOGLE_API_KEY环境变量")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.3,
)

class AgentState(TypedDict):
    input_text: str
    user_perspective: str
    product_perspective: str
    topic_perspective: str
    course_perspective: str
    final_conclusion: str

SYSTEM_PROMPTS = {
    "user": """【角色】用户思维分析专家

【任务】直接输出分析结果，不要使用"让我来分析一下"、"好的"、"我来"等开头客套语。

【分析维度】
从最相关人群的角度出发，分析：
1. 真实感受：这群人此刻的情绪和心态
2. 担忧：他们最害怕、最焦虑的是什么
3. 期待：他们内心真正渴望的是什么

【输出要求】
- 直接开始分析，不需要任何开场白
- 内容要具体、有真情实感，避免空泛
- 可以分段阐述，逻辑清晰""",
    
    "product": """【角色】产品思维分析专家

【任务】直接输出分析结果，不要使用"让我来分析一下"、"好的"、"我来"等开头客套语。

【分析维度】
从产品设计角度出发，分析：
1. 需求缺口：这个现象背后暴露了什么未被满足的需求？
2. 产品方案：如何设计一个产品来解决这个问题？
3. 核心功能：这个产品最关键的3个功能是什么？
4. 目标用户：谁是这个产品的核心用户群体？

【输出要求】
- 直接开始分析，不需要任何开场白
- 内容要具体、有可操作性
- 可以分段阐述，逻辑清晰""",
    
    "topic": """【角色】选题思维分析专家

【任务】直接输出分析结果，不要使用"让我来分析一下"、"好的"、"我来"等开头客套语。

【分析维度】
从内容传播角度出发，分析：
1. 时机洞察：这个现象为什么在此刻引发关注？
2. 情绪洞察：它触动了什么集体情绪？
3. 潜台词分析：人们讨论这个话题时，真正想说的是什么？
4. 选题建议：给出5个具体的选题方向，每个选题包含：
   - 选题标题
   - 核心角度
   - 目标受众

【输出要求】
- 直接开始分析，不需要任何开场白
- 选题建议要具体、有吸引力
- 可以分段阐述，逻辑清晰""",
    
    "course": """【角色】课程思维分析专家

【任务】直接输出分析结果，不要使用"让我来分析一下"、"好的"、"我来"等开头客套语。

【分析维度】
从教育学习角度出发，分析：
1. 方法论提炼：从这个现象中能总结出什么可复制的方法论？
2. 步骤拆解：这个方法论可以拆解成哪些具体的执行步骤？
3. 适用场景：这些方法适用于什么场景？不适用于什么场景？
4. 验证方式：如何判断学习者是否真正掌握了这些方法？

【输出要求】
- 直接开始分析，不需要任何开场白
- 内容要结构化、可落地
- 可以分段阐述，逻辑清晰""",
    
    "conclusion": """【角色】综合分析专家

【任务】直接输出分析结果，不要使用"让我来分析一下"、"好的"、"我来"等开头客套语。

【输入信息】
你将收到以下四个维度的分析结果：
1. 用户思维 - 相关人群的真实感受、担忧和期待
2. 产品思维 - 未满足的需求缺口和产品解决方案
3. 选题思维 - 现象背后的社会情绪和传播价值
4. 课程思维 - 可提炼的方法论和教育价值

【分析维度】
请综合以上信息，进行跨维度分析：
1. 内在联系：这四个维度之间有什么深层的关联和呼应？
2. 现象本质：这个现象的真正本质是什么？
3. 长期影响：它对个人、企业、社会可能产生什么长期影响？
4. 行动建议：给不同人群的具体建议
   - 普通用户：应该如何应对？
   - 创业者：有什么机会？
   - 内容创作者：如何把握这个趋势？
   - 学习者：应该学习什么？

【输出要求】
- 直接开始分析，不需要任何开场白
- 内容要全面、深刻、有洞见
- 可以分段阐述，逻辑清晰"""
}

def call_llm(system_prompt: str, user_content: str, context: Dict = None) -> str:
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    
    if context:
        context_str = "\n\n【上下文信息】\n"
        for key, value in context.items():
            context_str += f"\n【{key}】\n{value}\n"
        messages.append(HumanMessage(content=context_str))
    
    response = llm.invoke(messages)
    cleaned_content = clean_llm_output(response.content)
    return cleaned_content

def analyze_user_perspective(state: AgentState) -> Dict:
    input_text = state["input_text"]
    result = call_llm(SYSTEM_PROMPTS["user"], input_text)
    return {"user_perspective": result}

def analyze_product_perspective(state: AgentState) -> Dict:
    input_text = state["input_text"]
    result = call_llm(SYSTEM_PROMPTS["product"], input_text)
    return {"product_perspective": result}

def analyze_topic_perspective(state: AgentState) -> Dict:
    input_text = state["input_text"]
    result = call_llm(SYSTEM_PROMPTS["topic"], input_text)
    return {"topic_perspective": result}

def analyze_course_perspective(state: AgentState) -> Dict:
    input_text = state["input_text"]
    result = call_llm(SYSTEM_PROMPTS["course"], input_text)
    return {"course_perspective": result}

def synthesize_conclusion(state: AgentState) -> Dict:
    input_text = state["input_text"]
    context = {
        "用户思维分析": state["user_perspective"],
        "产品思维分析": state["product_perspective"],
        "选题思维分析": state["topic_perspective"],
        "课程思维分析": state["course_perspective"]
    }
    result = call_llm(SYSTEM_PROMPTS["conclusion"], input_text, context)
    return {"final_conclusion": result}

def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    workflow.add_node("analyze_user", analyze_user_perspective)
    workflow.add_node("analyze_product", analyze_product_perspective)
    workflow.add_node("analyze_topic", analyze_topic_perspective)
    workflow.add_node("analyze_course", analyze_course_perspective)
    workflow.add_node("synthesize", synthesize_conclusion)
    
    workflow.set_entry_point("analyze_user")
    
    workflow.add_edge("analyze_user", "analyze_product")
    workflow.add_edge("analyze_product", "analyze_topic")
    workflow.add_edge("analyze_topic", "analyze_course")
    workflow.add_edge("analyze_course", "synthesize")
    workflow.add_edge("synthesize", END)
    
    return workflow

def analyze_text(input_text: str) -> Dict:
    graph = build_graph()
    app = graph.compile()
    
    initial_state = {
        "input_text": input_text,
        "user_perspective": "",
        "product_perspective": "",
        "topic_perspective": "",
        "course_perspective": "",
        "final_conclusion": ""
    }
    
    result = app.invoke(initial_state)
    return result

def format_result(result: Dict) -> str:
    output = """
═══════════════════════════════════════════════════════════════
                    📊 多视角分析报告
═══════════════════════════════════════════════════════════════
"""
    
    output += f"""
📝 【原始输入】
───────────────────────────────────────────────────────────────
{result['input_text']}
"""
    
    output += f"""
👤 【视角一：用户思维】
───────────────────────────────────────────────────────────────
{result['user_perspective']}
"""
    
    output += f"""
💡 【视角二：产品思维】
───────────────────────────────────────────────────────────────
{result['product_perspective']}
"""
    
    output += f"""
📰 【视角三：选题思维】
───────────────────────────────────────────────────────────────
{result['topic_perspective']}
"""
    
    output += f"""
📚 【视角四：课程思维】
───────────────────────────────────────────────────────────────
{result['course_perspective']}
"""
    
    output += f"""
🎯 【跨维度综合结论】
═══════════════════════════════════════════════════════════════
{result['final_conclusion']}
═══════════════════════════════════════════════════════════════
"""
    
    return output
