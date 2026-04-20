import os
from typing import Dict, List, Annotated, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
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
    "user": """你现在需要从【用户思维】的角度来分析以下内容。
请假设你是最相关的那群人，思考：
1. 你的真实感受是什么？
2. 你有什么担忧？
3. 你有什么期待？

请详细阐述你的分析，要具体、有真情实感。""",
    
    "product": """你现在需要从【产品思维】的角度来分析以下内容。
请思考：
1. 这个现象/事物背后反映了什么未能满足的需求缺口？
2. 如何设计一个产品来满足这个需求？
3. 这个产品的核心功能是什么？
4. 目标用户是谁？

请详细阐述你的分析，要具体、有可操作性。""",
    
    "topic": """你现在需要从【选题思维】的角度来分析以下内容。
请思考：
1. 这个现象为什么在此刻引发关注？
2. 它触动了什么集体情绪？
3. 潜台词是什么？
4. 由此给出5个具体的选题建议（每个选题都要明确角度和切入点）

请详细阐述你的分析，选题建议要具体、有吸引力。""",
    
    "course": """你现在需要从【课程思维】的角度来分析以下内容。
请思考：
1. 从中能提炼出什么可教授的方法论？
2. 能拆解成哪些具体步骤？
3. 这些方法论和步骤适用于什么场景？
4. 如何验证学习效果？

请详细阐述你的分析，要结构化、可落地。""",
    
    "conclusion": """你现在需要综合以下四个维度的分析，给出一个跨维度的结论。
四个维度分别是：
1. 用户思维 - 相关人群的真实感受、担忧和期待
2. 产品思维 - 未满足的需求缺口和产品解决方案
3. 选题思维 - 现象背后的社会情绪和传播价值
4. 课程思维 - 可提炼的方法论和教育价值

请综合分析：
1. 这四个维度之间有什么内在联系？
2. 这个现象的本质是什么？
3. 它的长期影响可能是什么？
4. 给不同人群（普通用户、创业者、内容创作者、学习者）的建议是什么？

请给出一个全面、深刻、有洞见的跨维度结论。"""
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
    return response.content

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
