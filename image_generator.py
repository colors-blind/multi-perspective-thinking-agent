import os
import base64
from datetime import datetime
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

IMAGE_MODEL = "gemini-3.1-flash-image-preview"

IMAGE_STYLES = {
    "professional": "专业商务风格，适合企业报告和演示",
    "artistic": "艺术插画风格，富有创意和视觉冲击力",
    "minimalist": "极简风格，简洁现代，适合科技主题",
    "photorealistic": "写实照片风格，真实感强",
    "infographic": "信息图表风格，数据可视化，适合分析报告",
}

def get_image_prompt(event_description: str, analysis_summary: str, style: str = "infographic") -> str:
    style_description = IMAGE_STYLES.get(style, IMAGE_STYLES["infographic"])
    
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in event_description)
    
    language_instruction = ""
    if has_chinese:
        language_instruction = """
CRITICAL LANGUAGE REQUIREMENT:
- All text, labels, and captions in the image MUST be in CHINESE
- Use Simplified Chinese characters exclusively
- Do NOT use any English text anywhere in the image
- If you need to include numbers or statistics, keep them as numbers but add Chinese context
"""
    else:
        language_instruction = """
Language: Use the same language as the event description for any text in the image.
"""
    
    prompt = f"""Create a high-quality visual illustration for this event analysis report.

{language_instruction}

Event Description:
{event_description[:500]}

Key Insights from Multi-Perspective Analysis:
{analysis_summary[:800]}

Style Requirements:
- Visual Style: {style} - {style_description}
- Image Type: Professional quality digital illustration
- Aspect Ratio: 16:9 (wide format)
- Resolution: 2K high quality
- Color Palette: Modern, professional, visually appealing

Content Elements to Include:
1. Central visual theme related to the event/topic
2. Supporting visual elements that represent the key insights
3. Clean, readable composition suitable for a report
4. Professional typography if text is included
5. Balanced negative space for visual clarity

Make it visually engaging and professional, suitable for a business or analysis report cover.

IMPORTANT: Focus on creating a beautiful visual illustration. The visual elements should tell the story of the analysis.
"""
    return prompt

def generate_image_with_google_genai(
    prompt: str,
    api_key: Optional[str] = None,
    aspect_ratio: str = "16:9",
    resolution: str = "2K"
) -> Tuple[Optional[bytes], Optional[str]]:
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key or GOOGLE_API_KEY)
        
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=resolution
                ),
            )
        )
        
        image_data = None
        text_response = ""
        
        for part in response.parts:
            if part.text is not None:
                text_response += part.text
            elif part.inline_data is not None:
                image_data = part.inline_data.data
        
        return image_data, text_response
        
    except ImportError:
        return None, "google-genai SDK not installed. Please install with: pip install google-genai"
    except Exception as e:
        return None, f"Error generating image: {str(e)}"

def generate_image_with_langchain(
    prompt: str,
    api_key: Optional[str] = None,
    aspect_ratio: str = "16:9",
    resolution: str = "2K"
) -> Tuple[Optional[bytes], Optional[str]]:
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage, SystemMessage
        
        llm = ChatGoogleGenerativeAI(
            model=IMAGE_MODEL,
            google_api_key=api_key or GOOGLE_API_KEY,
        )
        
        messages = [
            SystemMessage(content="You are an expert image generator. Create high-quality images based on the user's description."),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        
        image_data = None
        text_response = ""
        
        if hasattr(response, 'content'):
            content = response.content
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, str):
                        text_response += part
                    elif isinstance(part, dict):
                        if 'text' in part:
                            text_response += part['text']
                        elif 'inline_data' in part:
                            image_data = part['inline_data'].get('data')
            elif isinstance(content, str):
                text_response = content
        
        return image_data, text_response
        
    except Exception as e:
        return None, f"Error with LangChain: {str(e)}"

def generate_image(
    event_description: str,
    analysis_data: Dict,
    style: str = "infographic",
    api_key: Optional[str] = None
) -> Tuple[Optional[bytes], Optional[str]]:
    summary_parts = []
    if analysis_data.get('user_perspective'):
        summary_parts.append(f"User Perspective: {analysis_data['user_perspective'][:200]}")
    if analysis_data.get('product_perspective'):
        summary_parts.append(f"Product Insight: {analysis_data['product_perspective'][:200]}")
    if analysis_data.get('final_conclusion'):
        summary_parts.append(f"Conclusion: {analysis_data['final_conclusion'][:300]}")
    
    analysis_summary = "\n".join(summary_parts)
    
    prompt = get_image_prompt(event_description, analysis_summary, style)
    
    return generate_image_with_google_genai(prompt, api_key)

def save_image(image_data: bytes, output_dir: str, prefix: str = "generated") -> str:
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(image_data)
    
    return filename

def image_to_base64(image_data: bytes) -> str:
    return base64.b64encode(image_data).decode('utf-8')

if __name__ == "__main__":
    test_event = "AI technology is causing large-scale layoffs across multiple industries"
    test_analysis = {
        'user_perspective': "Workers feel anxious about job security and skill obsolescence",
        'product_perspective': "There's a gap in AI transition support and skill retraining",
        'final_conclusion': "AI represents a paradigm shift requiring adaptive strategies"
    }
    
    print("Testing image generation...")
    image_data, text = generate_image(test_event, test_analysis, style="infographic")
    
    if image_data:
        print(f"Image generated successfully! Size: {len(image_data)} bytes")
        filename = save_image(image_data, "./reports", "test_image")
        print(f"Image saved as: {filename}")
    else:
        print(f"Image generation failed: {text}")
