import os
import json
from dashscope import Generation
import dashscope
from fastapi import HTTPException
from ..models.novel import GenerationMode

# 配置 DashScope API
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

def edit_text(text: str, instruction: str) -> str:
    """
    General purpose text editing/rewriting function.
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return "Error: API Key not found"

    system_prompt = "你是一个专业的文字编辑助手。请根据用户的指令修改提供的文本。只返回修改后的文本，不要包含任何解释。"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"【原文】\n{text}\n\n【指令】\n{instruction}"}
    ]
    
    try:
        response = Generation.call(
            api_key=api_key,
            model="qwen-max",
            messages=messages,
            result_format="message",
        )
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            # Remove any markdown code blocks if present
            content = content.replace("```html", "").replace("```", "")
            return content.strip()
        else:
            return f"Error: {response.message}"
    except Exception as e:
        return f"Error: {str(e)}"

        return f"Error: {str(e)}"

def generate_wiki_entry(name: str, role: str, basic_info: str, context: str = "") -> str:
    """
    Generate a detailed wiki/encyclopedia entry for a character or scene.
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return "Error: API Key not found"

    system_prompt = """你是一个世界观架构师和百科词条编写者。请根据提供的基本信息，为小说中的角色或场景撰写一个详细的百科词条。
词条应包含以下部分（如果是角色）：
1. **基本信息**（姓名、别名、种族、职业等）
2. **外貌描写**（详细的视觉特征）
3. **性格特征**（核心性格、优缺点、行事风格）
4. **背景故事**（过往经历、重要事件）
5. **能力/技能**（如有）
6. **人际关系**（与其他角色的关系）

如果是场景，请包含：地理位置、环境描写、历史背景、重要设施等。

请使用 Markdown 格式输出，内容要详实丰富，符合小说设定的世界观风格。"""

    user_content = f"【名称】: {name}\n【角色/定位】: {role}\n【已知信息】: {basic_info}\n"
    if context:
        user_content += f"\n【世界观/大纲背景】: {context}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    try:
        response = Generation.call(
            api_key=api_key,
            model="qwen-max",
            messages=messages,
            result_format="message",
        )
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            return f"Error: {response.message}"
    except Exception as e:
        return f"Error: {str(e)}"

def _generate_via_api(prompt: str, context: str = "") -> str:
    """
    Generate content using DashScope API (Qwen-Max).
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        # Fallback for development if env var is missing, though user said it's configured
        # Ideally, we should log a warning or raise an error.
        print("Warning: DASHSCOPE_API_KEY not found in environment variables.")
        return "[Error] API Key not configured."

    # 构建丰富的系统提示词
    system_prompt = """你是一位笔触细腻、擅长营造氛围的畅销书作家。你的任务是根据用户提供的信息创作小说章节。

【写作要求】
1. **沉浸式描写**：坚持"Show, Don't Tell"原则。通过感官描写（视觉、听觉、嗅觉等）来展现场景和情绪，而不是直接告诉读者。
2. **拒绝流水账与总结**：严禁使用概括性、总结性的语言（如"经过一番激战..."、"最终..."）。必须将过程拆解为具体的动作、对话和心理活动。
3. **自然流畅**：避免生硬的转折或突然的"升华"。情感和剧情的推进要有铺垫，逻辑要严密。
4. **角色鲜活**：对话要符合人物性格，避免脸谱化。

【格式要求】
1. **HTML格式**：为了确保排版美观，请直接使用 HTML 的 `<p>` 标签来包裹每一个段落。
   - 例如：`<p>这是第一段内容。</p><p>这是第二段内容。</p>`
2. **段落分明**：段落之间不要有过长的空白，但要通过 `<p>` 标签自然分隔。
3. **不要解释**：直接输出小说正文，不要包含任何"好的"、"这是为您生成的章节"等前缀或后缀。"""

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    if context:
        messages.append({"role": "user", "content": f"【上下文信息】\n{context}\n\n【本次写作任务】\n{prompt}"})
    else:
        messages.append({"role": "user", "content": prompt})

    try:
        response = Generation.call(
            api_key=api_key,
            model="qwen-max",
            messages=messages,
            result_format="message",
        )

        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            return f"[Error] Generation failed: {response.code} - {response.message}"
    except Exception as e:
        return f"[Error] Exception during generation: {str(e)}"

def generate_outline(novel_type: str) -> str:
    """
    Generate a novel outline based on type/genre.
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return "API Key not configured."

    system_prompt = """你是一个专业的小说大纲策划师。请根据用户提供的小说类型，创作一份详细的小说大纲。
大纲应包含：
1. **故事背景**：世界观、时代背景。
2. **核心冲突**：主要矛盾点。
3. **主要角色**：主角及关键配角简述。
4. **剧情走向**：起承转合的粗略规划（分章节或阶段）。
请使用 Markdown 格式清晰输出。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请为一部【{novel_type}】类型的小说生成一份详细大纲。"}
    ]

    try:
        response = Generation.call(
            api_key=api_key,
            model="qwen-max",
            messages=messages,
            result_format="message",
        )
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            return f"大纲生成失败: {response.code}"
    except Exception as e:
        return f"大纲生成出错: {str(e)}"

def generate_plot_choices(context: str) -> list:
    """
    Generate 3 plot direction choices based on context.
    Returns a list of strings.
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return ["API Key missing"]

    system_prompt = """你是一个小说剧情顾问。请根据当前的小说上下文，提供 3 个不同的后续剧情发展方向供作者选择。
每个选项应简洁明了（50字以内），涵盖不同的冲突或情节转折。
请严格按照以下 JSON 格式输出列表：
["选项1内容", "选项2内容", "选项3内容"]
不要输出任何 Markdown 代码块标记或其他文字，只输出纯 JSON 数组。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"【当前剧情上下文】\n{context}\n\n请提供3个后续剧情走向选项。"}
    ]

    try:
        response = Generation.call(
            api_key=api_key,
            model="qwen-max",
            messages=messages,
            result_format="message",
        )
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            # Clean potential markdown code blocks if AI ignores instruction
            content = content.replace("```json", "").replace("```", "").strip()
            try:
                return json.loads(content)
            except:
                # Fallback if JSON parsing fails
                return [content]
        else:
            return [f"Error: {response.code}"]
    except Exception as e:
        return [f"Exception: {str(e)}"]

def _generate_via_rpa(prompt: str, context: str = "") -> str:

    """
    [Deprecated] RPA mode is currently a placeholder.
    """
    return "[RPA Mode] This feature is currently under maintenance. Please use API mode."

def generate_chapter_text(prompt: str, mode: GenerationMode = GenerationMode.API, context: str = "") -> str:
    # 优先使用 API 模式，因为用户指定了使用 DashScope
    # 即使传入 RPA 模式，如果未实现，也可以回退或提示
    if mode == GenerationMode.RPA:
         return _generate_via_rpa(prompt, context)
    else:
        return _generate_via_api(prompt, context)

def generate_illustration_prompt(segment_text: str) -> str:
    """
    Generate an image prompt based on a text segment.
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return "Novel scene, detailed, high quality"

    system_prompt = """你是一个AI绘画提示词专家。请阅读以下小说片段，提取核心画面元素（环境、人物、动作、氛围），并生成一个简洁的英文绘画提示词（Prompt）。
    格式要求：
    1. 只输出英文提示词。
    2. 包含风格描述（如：Anime style, detailed, cinematic lighting）。
    3. 不需要任何解释性文字。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"【小说片段】\n{segment_text}"}
    ]

    try:
        response = Generation.call(
            api_key=api_key,
            model="qwen-max",
            messages=messages,
            result_format="message",
        )
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            return "Novel scene, detailed"
    except Exception:
        return "Novel scene, detailed"

def refresh_single_asset(name: str, context_text: str, current_info: dict) -> dict:
    """
    Refresh details for a single asset based on provided context.
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return {}

    system_prompt = f"""你是一个小说角色/设定分析师。请阅读提供的小说文本，专门分析并更新角色/场景“{name}”的信息。
    
    【现有信息】
    {json.dumps(current_info, ensure_ascii=False)}
    
    【任务】
    请根据文本内容，补充或修正该角色的详细设定。
    如果文本中没有关于该角色的新信息，请返回原信息。
    
    【输出格式】
    JSON 对象（不是列表），包含：
    {{
        "role": "更新后的详细角色/场景描述",
        "tags": ["标签1", "标签2"]
    }}
    只返回 JSON，不要 Markdown。
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"【小说文本片段】\n{context_text[:4000]}"}
    ]

    try:
        response = Generation.call(
            api_key=api_key,
            model="qwen-max",
            messages=messages,
            result_format="message",
        )
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        else:
            return {}
    except Exception as e:
        print(f"Asset refresh failed: {e}")
        return {}

def extract_assets_from_text(text: str, current_assets: list, outline: str = "") -> list:
    """
    Extract characters and locations from text and update asset list.
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return []

    # Simplified current assets for context
    asset_summary = [{"name": a["name"], "type": a["type"], "role": a.get("role", "")} for a in current_assets]
    
    system_prompt = f"""你是一个严谨的小说设定整理助手。请根据提供的小说文本，提取其中的重要角色和场景信息。

【上下文信息】
小说大纲/背景：
{outline if outline else "未提供，请仅依据文本判断"}

现有资产列表（作为参考，不要重复创建已存在的角色）：
{json.dumps(asset_summary, ensure_ascii=False)}

【任务目标】
请输出一个 JSON 列表，包含检测到的新资产或需要更新的资产。

【严格约束 - 必须遵守】
1. **实事求是**：只提取文本中**明确出现**或**明确描写**的角色/场景。绝对不要根据名字猜测身份（例如：不要因为某人叫“亚瑟”就将其定义为“国王”，除非文中明确提到）。
2. **拒绝过度联想**：如果文本中只提到某人"拿了一把剑"，不要直接定义为"剑客"，除非文中明确提到他的职业。
3. **一致性检查**：如果提取的角色与“小说大纲”或“现有资产”中的描述严重冲突（如身份完全不同），请优先采信“小说大纲”或标记为疑似新角色。
3. **避免幻觉**：如果文中信息不足以判断角色身份，请将其 role 留空或填“未知”，不要编造。
4. **去重**：如果文中出现的角色 clearly 对应现有资产（哪怕名字略有不同，如“小王”对应“王大力”），请使用 action: "update" 并沿用现有资产的标准名称。

【输出格式】
JSON 列表，示例：
[
    {{
        "name": "张三",
        "type": "character", 
        "role": "主角，性格...",
        "tags": ["勇敢", "剑客"],
        "action": "create" (或 "update")
    }}
]
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"【小说文本片段】\n{text[:4000]}"} # Increased limit slightly
    ]

    try:
        response = Generation.call(
            api_key=api_key,
            model="qwen-max",
            messages=messages,
            result_format="message",
        )
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            # Clean up code blocks if present
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        else:
            return []
    except Exception as e:
        print(f"Asset extraction failed: {e}")
        return []

def generate_relationship_graph(text: str) -> dict:
    """
    Analyze text to extract character relationships for a graph.
    Returns { "nodes": [...], "links": [...] }
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return {"nodes": [], "links": []}

    system_prompt = """你是一个文学作品关系分析师。请阅读小说文本，提取人物关系图谱。
    
    请输出 JSON 格式，包含：
    1. nodes: 角色列表，格式 [{"name": "角色名", "category": 0, "symbolSize": 30}]
       - category: 0=主角, 1=配角, 2=反派/其他
       - symbolSize: 主角建议 50, 配角 30, 其他 20
    2. links: 关系列表，格式 [{"source": "角色A", "target": "角色B", "value": "关系描述"}]
    
    请确保 JSON 格式合法。只返回 JSON，不要 Markdown。"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"【小说文本】\n{text[:4000]}"}
    ]

    try:
        response = Generation.call(
            api_key=api_key,
            model="qwen-max",
            messages=messages,
            result_format="message",
        )
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            try:
                data = json.loads(content)
                # Ensure structure
                if "nodes" not in data: data["nodes"] = []
                if "links" not in data: data["links"] = []
                return data
            except:
                print(f"JSON Parse Error for Graph: {content}")
                return {"nodes": [], "links": []}
        else:
            print(f"API Error: {response.code}")
            return {"nodes": [], "links": []}
    except Exception as e:
        print(f"Exception: {e}")
        return {"nodes": [], "links": []}


