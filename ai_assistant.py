import os
import streamlit as st
from dotenv import load_dotenv
from zai import ZhipuAiClient

# 加载.env文件变量
load_dotenv()

# ----------------- 配置区域 -----------------
api_key = os.getenv("ZHIPUAI_API_KEY")
knowledge_base_id = os.getenv("KNOWLEDGE_BASE_ID")

# 检查配置是否读取成功
if not api_key:
    st.error("❌ 未找到 ZHIPUAI_API_KEY，请检查 .env 文件！")
    st.stop()  # 用st.stop替代raise，避免程序崩溃，更友好
if not knowledge_base_id:
    st.error("❌ 未找到 KNOWLEDGE_BASE_ID，请检查 .env 文件！")
    st.stop()

# 初始化智谱AI客户端（增加超时配置）
client = ZhipuAiClient(
    api_key=api_key,
    timeout=30  # 增加超时时间，避免检索超时
)


def query_knowledge_base(question):
    """
    使用智谱AI知识库进行问答（修复检索逻辑+优化错误处理）
    """
    try:
        # 调用智谱API，强制触发知识库检索
        response = client.chat.completions.create(
            model="glm-4-flash",  # 推荐使用glm-4效果更好（需确保API Key有该模型权限）
            messages=[
                # 新增系统提示词，规范回答风格
                {
                    "role": "system",
                    "content": """        
                    1.  **角色设定**：你就像一位知识渊博的博物馆金牌讲解员。面对专业术语（如“鸟虫书”、“失蜡法”、“悬山顶”），尽量用现代生活中的类比或通俗语言进行解释，但必须保持历史事实的准确性。
                    2.  **依据事实**：请严格基于【已知信息】回答。如果信息中包含具体的出土年代、地点或尺寸数据，请务必引用以增加可信度。
                    3.  **诚实原则**：如果【已知信息】中没有包含回答问题所需的知识，请直接告知用户：“抱歉，目前的考古资料库中暂无此记录”，严禁臆测或编造历史事实。
                    4.  **回答结构**：
                        *   先直接给出核心结论。
                        *   再展开详细描述（文物的形制、纹饰、历史背景）。
                        *   最后（如果相关）可以延伸一两句该文物在楚文化中的独特地位或审美价值。
                    5.  **语气风格**：客观、典雅、引人入胜。"""
                },
                {"role": "user", "content": question}
            ],
            tools=[
                {
                    "type": "retrieval",
                    "retrieval": {
                        "knowledge_id": knowledge_base_id,  # 智谱zai库要求的正确参数名
                        # 修正：占位符用{{}}双大括号（智谱官方要求）
                        "prompt_template": """从文档
\"\"\"
{{knowledge}}
\"\"\"
中找问题
\"\"\"
{{question}}
\"\"\"
的答案，找到答案就仅使用文档语句回答问题并说明该数据来自已收录知识库，找不到答案就用自身知识回答并且告诉用户该信息不是来自已收录被证实过的数据，来自网络。""",
                        "top_k": 3,  # 检索最相关的3条内容
                        "enable_citation": True  # 开启引文标注，便于验证是否检索到内容
                    }
                }
            ],
            tool_choice={  # 强制触发检索工具（关键！避免模型跳过检索）
                "type": "retrieval"
            },
            temperature=0.2,  # 降低随机性，保证回答严谨
            stream=False
        )
        # 解析回答内容
        answer = response.choices[0].message.content
        # 提取引文（调试用，确认是否检索到知识库内容）
        citations = []
        if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                if tool_call.type == "retrieval" and hasattr(tool_call.retrieval, 'citations'):
                    citations = tool_call.retrieval.citations
        return answer, citations
    except Exception as e:
        # 输出详细错误信息，便于调试
        error_info = f"查询出错: {str(e)}"
        # 若有response对象，补充响应信息
        if 'response' in locals():
            error_info += f"\n响应详情: {str(response)}"
        return error_info, []


# ----------------- Streamlit界面 -----------------
st.title("🛡️ 楚文化智能问答助手")
st.markdown("基于 **智谱AI知识库 + GLM** | 专注于楚系文字与考古知识")

# 侧边栏：显示配置和调试信息
with st.sidebar:
    st.write("📖 **知识库配置**")
    st.success("✅ 智谱AI客户端已初始化")
    st.info(f"当前知识库ID: \n{knowledge_base_id}")
    st.write("🔍 调试信息")
    st.caption(f"API Key前8位: {api_key[:8]}..." if api_key else "未配置")

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史聊天记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 处理用户输入
if prompt := st.chat_input("请输入关于楚文化的问题，例如：郭店楚简出土于哪一年？"):
    # 保存并显示用户问题
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 调用知识库问答并显示结果
    with st.chat_message("assistant"):
        with st.spinner("🔍 正在检索楚文化考古资料库..."):
            answer, citations = query_knowledge_base(prompt)
            st.write(answer)

            # 显示检索到的参考内容（验证是否真的调用了知识库）
            if citations:
                with st.expander("📚 知识库参考内容", expanded=False):
                    for idx, cite in enumerate(citations, 1):
                        # 提取引用内容（兼容zai库的返回格式）
                        cite_content = getattr(cite, 'content', '无')
                        st.caption(f"参考{idx}: {cite_content[:200]}...")

    # 保存AI回答
    st.session_state.messages.append({"role": "assistant", "content": answer})