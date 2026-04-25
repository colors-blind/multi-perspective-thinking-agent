import os
import re
import time
import uuid
from typing import Dict, List, Annotated, TypedDict, Optional, Generator, Any
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


class AnalysisStage(Enum):
    USER = "user"
    PRODUCT = "product"
    TOPIC = "topic"
    COURSE = "course"
    CONCLUSION = "conclusion"


STAGE_INFO = {
    AnalysisStage.USER: {
        "name": "用户思维",
        "description": "相关人群的真实感受、担忧与期待",
        "key": "user_perspective"
    },
    AnalysisStage.PRODUCT: {
        "name": "产品思维",
        "description": "需求缺口分析与产品解决方案",
        "key": "product_perspective"
    },
    AnalysisStage.TOPIC: {
        "name": "选题思维",
        "description": "社会情绪洞察与传播价值分析",
        "key": "topic_perspective"
    },
    AnalysisStage.COURSE: {
        "name": "课程思维",
        "description": "可提炼的方法论与教育价值",
        "key": "course_perspective"
    },
    AnalysisStage.CONCLUSION: {
        "name": "综合结论",
        "description": "整合四维度分析的深度洞察",
        "key": "final_conclusion"
    }
}


class EventType(Enum):
    STAGE_START = "stage_start"
    TOKEN = "token"
    STAGE_END = "stage_end"
    COMPLETE = "complete"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class StreamEvent:
    event_type: str
    stage: Optional[str] = None
    stage_name: Optional[str] = None
    stage_description: Optional[str] = None
    elapsed_ms: float = 0.0
    content: str = ""
    result_id: str = ""
    is_complete: bool = False
    is_error: bool = False
    error_message: Optional[str] = None
    token: str = ""


def clean_llm_output(text) -> str:
    if not text:
        return ""
    
    if isinstance(text, list):
        text_parts = []
        for part in text:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and 'text' in part:
                text_parts.append(part['text'])
        text = ''.join(text_parts)
    
    if not isinstance(text, str):
        text = str(text)
    
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
    
    content = response.content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and 'text' in part:
                text_parts.append(part['text'])
        content = ''.join(text_parts)
    
    cleaned_content = clean_llm_output(content)
    return cleaned_content


def call_llm_stream(system_prompt: str, user_content: str, context: Dict = None) -> Generator[str, None, str]:
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    
    if context:
        context_str = "\n\n【上下文信息】\n"
        for key, value in context.items():
            context_str += f"\n【{key}】\n{value}\n"
        messages.append(HumanMessage(content=context_str))
    
    full_content = []
    
    for chunk in llm.stream(messages):
        if hasattr(chunk, 'content') and chunk.content:
            content = chunk.content
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, str):
                        full_content.append(part)
                        yield part
                    elif isinstance(part, dict) and 'text' in part:
                        text = part['text']
                        full_content.append(text)
                        yield text
            elif isinstance(content, str):
                full_content.append(content)
                yield content
    
    final_content = ''.join(full_content)
    cleaned_content = clean_llm_output(final_content)
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


class AnalysisStopFlag:
    def __init__(self):
        self._stopped = False
    
    def stop(self):
        self._stopped = True
    
    @property
    def is_stopped(self):
        return self._stopped


def analyze_stream(
    input_text: str,
    stop_flag: Optional[AnalysisStopFlag] = None,
    result_id: Optional[str] = None
) -> Generator[StreamEvent, None, Dict]:
    if stop_flag is None:
        stop_flag = AnalysisStopFlag()
    
    if result_id is None:
        result_id = str(uuid.uuid4())
    
    total_start_time = time.time()
    
    state = {
        "input_text": input_text,
        "user_perspective": "",
        "product_perspective": "",
        "topic_perspective": "",
        "course_perspective": "",
        "final_conclusion": ""
    }
    
    def create_stage_config(stage_enum, state_key):
        stage_info = STAGE_INFO[stage_enum]
        return {
            "enum": stage_enum,
            "key": state_key,
            "name": stage_info["name"],
            "description": stage_info["description"],
            "prompt": SYSTEM_PROMPTS[stage_enum.value],
            "needs_context": stage_enum == AnalysisStage.CONCLUSION
        }
    
    stage_configs = [
        create_stage_config(AnalysisStage.USER, "user_perspective"),
        create_stage_config(AnalysisStage.PRODUCT, "product_perspective"),
        create_stage_config(AnalysisStage.TOPIC, "topic_perspective"),
        create_stage_config(AnalysisStage.COURSE, "course_perspective"),
        create_stage_config(AnalysisStage.CONCLUSION, "final_conclusion"),
    ]
    
    for stage_config in stage_configs:
        if stop_flag.is_stopped:
            break
        
        stage_enum = stage_config["enum"]
        stage_key = stage_config["key"]
        stage_name = stage_config["name"]
        stage_description = stage_config["description"]
        system_prompt = stage_config["prompt"]
        needs_context = stage_config["needs_context"]
        
        stage_start_event = StreamEvent(
            event_type=EventType.STAGE_START.value,
            stage=stage_enum.value,
            stage_name=stage_name,
            stage_description=stage_description,
            result_id=result_id
        )
        yield stage_start_event
        
        try:
            stage_start_time = time.time()
            
            context = None
            if needs_context:
                context = {
                    "用户思维分析": state["user_perspective"],
                    "产品思维分析": state["product_perspective"],
                    "选题思维分析": state["topic_perspective"],
                    "课程思维分析": state["course_perspective"]
                }
            
            full_content = []
            stream_generator = call_llm_stream(system_prompt, input_text, context)
            
            while True:
                if stop_flag.is_stopped:
                    break
                
                try:
                    token = next(stream_generator)
                    if token:
                        full_content.append(token)
                        token_event = StreamEvent(
                            event_type=EventType.TOKEN.value,
                            stage=stage_enum.value,
                            stage_name=stage_name,
                            stage_description=stage_description,
                            token=token,
                            result_id=result_id
                        )
                        yield token_event
                except StopIteration:
                    break
            
            stage_elapsed_ms = (time.time() - stage_start_time) * 1000
            
            final_content = ''.join(full_content)
            state[stage_key] = final_content
            
            stage_end_event = StreamEvent(
                event_type=EventType.STAGE_END.value,
                stage=stage_enum.value,
                stage_name=stage_name,
                stage_description=stage_description,
                elapsed_ms=round(stage_elapsed_ms, 2),
                content=final_content,
                result_id=result_id
            )
            yield stage_end_event
            
        except Exception as e:
            error_event = StreamEvent(
                event_type=EventType.ERROR.value,
                stage=stage_enum.value,
                stage_name=stage_name,
                stage_description=stage_description,
                result_id=result_id,
                is_error=True,
                error_message=str(e)
            )
            yield error_event
            break
    
    if stop_flag.is_stopped:
        stopped_event = StreamEvent(
            event_type=EventType.STOPPED.value,
            result_id=result_id,
            content="分析已被中断"
        )
        yield stopped_event
        return state
    
    total_elapsed_ms = (time.time() - total_start_time) * 1000
    
    complete_event = StreamEvent(
        event_type=EventType.COMPLETE.value,
        stage="complete",
        stage_name="分析完成",
        stage_description="所有阶段分析已完成",
        elapsed_ms=round(total_elapsed_ms, 2),
        result_id=result_id,
        is_complete=True
    )
    yield complete_event
    
    return state


def analyze_text_streaming(
    input_text: str,
    stop_flag: Optional[AnalysisStopFlag] = None,
    result_id: Optional[str] = None
) -> Dict:
    if stop_flag is None:
        stop_flag = AnalysisStopFlag()
    
    if result_id is None:
        result_id = str(uuid.uuid4())
    
    final_state = None
    for event in analyze_stream(input_text, stop_flag, result_id):
        if event.is_complete:
            pass
    
    return analyze_text(input_text)
