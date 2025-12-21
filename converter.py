import os
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatTongyi
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 定义输出结构
class ArticleAnalysis(BaseModel):
    category: str = Field(description="The hierarchical category of the article using hyphens (e.g., Technology-Java-Concurrency)")
    markdown_content: str = Field(description="The converted markdown content with images preserved")

def get_llm_config():
    """
    根据 LLM_PROVIDER 获取对应的配置 (API Key, Base URL, Model)
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    # 默认使用 OpenAI 配置
    prefix = "OPENAI"
    
    if provider == "deepseek":
        prefix = "DEEPSEEK"
    elif provider == "kimi":
        prefix = "KIMI"
    elif provider == "qwen":
        prefix = "QWEN"
    elif provider == "doubao":
        prefix = "DOUBAO"
    elif provider == "custom":
        prefix = "CUSTOM"
    
    api_key = os.getenv(f"{prefix}_API_KEY")
    base_url = os.getenv(f"{prefix}_BASE_URL")
    model = os.getenv(f"{prefix}_MODEL")
    
    # Fallback logic
    if not api_key and prefix != "OPENAI":
        if os.getenv("OPENAI_API_KEY"):
            return os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_BASE_URL"), os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            
    if not api_key:
        raise ValueError(f"API Key not found for provider '{provider}'. Please check {prefix}_API_KEY in your .env file.")
        
    return provider, api_key, base_url, model

def get_llm_model():
    """
    初始化 LangChain Chat Model
    """
    provider, api_key, base_url, model_name = get_llm_config()
    
    if not model_name and provider == "openai":
        model_name = "gpt-4o-mini"
        
    print(f"Using LLM Provider: {provider}, Model: {model_name}")
    
    if provider == "qwen":
        # 使用 DashScope 官方集成
        # 注意: ChatTongyi 默认读取 DASHSCOPE_API_KEY，这里我们显式传入
        # Qwen 的 model 参数通常是 'qwen-plus', 'qwen-turbo' 等
        return ChatTongyi(
            model=model_name,
            dashscope_api_key=api_key,
            temperature=0.3,
            max_tokens=8192 # 尝试请求更长的输出
        )

    if provider == "deepseek":
        # 使用 DeepSeek 官方集成
        return ChatDeepSeek(
            model=model_name,
            api_key=api_key,
            temperature=0.3,
            max_tokens=8192 # DeepSeek V3 支持 8k output
            # 注意: langchain-deepseek 默认使用 DeepSeek 官方 API 地址
            # 如果需要自定义 base_url，可以传递 api_base 参数 (取决于具体版本，通常不需要)
        )
        
    # 对于 Doubao，虽然有 ChatVolcEngineMaas，但配置相对复杂且经常变动 (Endpoint ID vs Model Name)
    # 且 LangChain Community 中的豆包集成可能不如 OpenAI 兼容接口稳定
    # 这里我们暂时保留 OpenAI 兼容模式用于 Doubao，除非用户明确要求强制使用 SDK
    # 如果要用 SDK: from langchain_community.chat_models import ChatVolcEngineMaas
    
    # 其他厂商 (Deepseek, Kimi, Doubao, OpenAI, Custom) 继续使用 OpenAI 兼容接口
    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base=base_url,
        temperature=0.3,
        max_tokens=16384 # OpenAI gpt-4o-mini 支持 16k output
    )
    
    return llm

def convert_to_markdown(text, title=""):
    """
    使用 LangChain 将文本转换为 Markdown 并提取分类
    返回字典: {'category': str, 'markdown_content': str}
    """
    llm = get_llm_model()
    
    parser = JsonOutputParser(pydantic_object=ArticleAnalysis)
    
    system_prompt = """
    You are a professional content editor. Your task is to process the provided HTML/text content from a web page.
    
    You need to:
    1. Convert the content into a clean, well-structured Markdown document.
    2. Determine the best category for this article using the Dewey Decimal Classification (DDC) system.
    
    The root category MUST be one of the following 10 classes (use the format 'Code-Name'):
    - 000-Generalities (includes Computer Science, Information, Systems)
    - 100-Philosophy_Psychology
    - 200-Religion
    - 300-Social_Sciences
    - 400-Language
    - 500-Natural_Sciences (Mathematics, Physics, Chemistry, Biology)
    - 600-Applied_Sciences (Technology, Engineering, Medicine, Agriculture)
    - 700-Arts_Recreation
    - 800-Literature
    - 900-History_Geography

    Then add sub-categories to create a hierarchical path.
    Format: `Code-RootCategory-SubCategory-Topic`
    
    Examples:
    - For a Java programming tutorial: "000-Generalities-Computer_Science-Java" (Note: DDC places CS in 000) OR "600-Applied_Sciences-Software_Engineering-Java" (If it fits better as applied tech). Use your best judgment for modern context.
    - For a travel guide: "900-History_Geography-Travel-Asia"
    - For a stock analysis: "300-Social_Sciences-Economics-Finance"

    Rules for Markdown Conversion:
    1. Identify the main content and ignore navigation menus, ads, footer links, and unrelated text.
    2. Use appropriate Markdown headers (#, ##, ###) to structure the content.
    3. Preserve code blocks if any, and specify the language.
    4. Maintain lists, quotes, and bold/italic formatting where appropriate.
    5. **CRITICAL**: Preserve all images found in the content. Use standard Markdown image syntax: `![alt text](src_url)`. Do not change the source URL.
    6. If the input is messy, rephrase slightly for readability but keep the meaning.

    {format_instructions}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Title: {title}\n\nContent:\n{content}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        # 截断输入以防止超出 Token 限制
        # 大幅增加限制，适配 128k context 窗口
        # HTML 内容可能非常冗长，500k 字符通常足够容纳大多数长文
        safe_content = text[:500000]
        
        return chain.invoke({
            "title": title,
            "content": safe_content,
            "format_instructions": parser.get_format_instructions()
        })
    except Exception as e:
        # 如果解析失败，尝试回退到简单的文本模式 (虽然这可能会丢失分类)
        # 或者直接抛出异常让上层处理
        raise Exception(f"Error calling LLM chain: {str(e)}")
