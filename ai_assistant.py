import os
import streamlit as st
from dotenv import load_dotenv
from zai import ZhipuAiClient

# 页面基础配置（第一步先设置页面风格）
st.set_page_config(
    page_title="楚文化智能问答助手 | Chuscript",
    page_icon="🏺",  # 青铜礼器图标贴合楚文化
    layout="wide",  # 宽布局更适合展示内容
    initial_sidebar_state="expanded"  # 侧边栏默认展开
)

# 自定义CSS（核心：楚文化风格样式）
st.markdown("""
<style>
    /* 全局样式：楚文化配色（朱红、暗金、墨黑、石青） */
    :root {
        --chu-red: #9C2B1C;       /* 楚式朱红 */
        --chu-gold: #D4AF37;      /* 楚式暗金 */
        --chu-black: #1A1A1A;     /* 楚式墨黑 */
        --chu-blue: #1E3A5F;      /* 楚式石青 */
        --chu-bg: #F8F5F0;        /* 浅米底（仿竹简底色） */
    }

    /* 页面背景 */
    .stApp {
        background-color: var(--chu-bg);
        background-image: url("https://p11-flow-imagex-download-sign.byteimg.com/tos-cn-i-a9rns2rl98/ebf0bf5e169c4fbeb35952ca5133ad50.png~tplv-a9rns2rl98-24:720:720.png");
        background-size: cover;
        background-attachment: fixed;
        background-opacity: 0.1;
    }

    /* 标题样式：楚文化书法感 */
    h1 {
        color: var(--chu-red);
        font-family: "SimHei", "STHeiti", serif;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        border-bottom: 2px solid var(--chu-gold);
        padding-bottom: 10px;
    }

    /* 聊天框样式优化 */
    .stChatMessage {
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        backdrop-filter: blur(5px);
    }

    /* 用户消息框 */
    [data-testid="stChatMessageUser"] {
        background-color: rgba(30, 58, 95, 0.1);
        border-left: 4px solid var(--chu-blue);
    }

    /* 助手消息框 */
    [data-testid="stChatMessageAssistant"] {
        background-color: rgba(156, 43, 28, 0.05);
        border-left: 4px solid var(--chu-red);
    }

    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background-color: rgba(26, 26, 26, 0.9);
        color: var(--chu-gold);
    }

    /* 按钮样式 */
    .stButton>button {
        background-color: var(--chu-red);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-family: "SimHei", serif;
    }

    .stButton>button:hover {
        background-color: #7A2014;
    }

    /* 输入框样式 */
    [data-testid="stChatInput"]>div>textarea {
        border: 1px solid var(--chu-gold);
        border-radius: 8px;
        background-color: rgba(255, 255, 255, 0.8);
    }

    /* 展开面板样式 */
    .stExpander {
        border: 1px solid var(--chu-gold);
        border-radius: 6px;
    }

    /* 提示文字样式 */
    .caption {
        color: var(--chu-blue);
    }
</style>
""", unsafe_allow_html=True)

# 加载.env文件变量
load_dotenv()

# ----------------- 配置区域 -----------------
api_key = os.getenv("ZHIPUAI_API_KEY")
knowledge_base_id = os.getenv("KNOWLEDGE_BASE_ID")

# 检查配置是否读取成功
if not api_key:
    st.error("❌ 未找到 ZHIPUAI_API_KEY，请检查 .env 文件！")
    st.stop()
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
的答案，找到答案就使用文档回答问题并结合实际搜索回答使内容更切合问题，说明该数据来自收录知识库，找不到答案就用自身知识回答并且告诉用户该信息不是来自已收录被证实过的数据，来自网络。""",
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
# 主标题和副标题
st.title("🏺 楚文化智能问答助手")
st.markdown("""
<div style="color: var(--chu-blue); font-size: 16px; font-style: italic; margin-bottom: 20px;">
基于智谱AI知识库 + GLM | 深耕楚系文字·考古·文物研究
</div>
""", unsafe_allow_html=True)

# 侧边栏：楚文化风格的配置和调试信息
with st.sidebar:
    st.markdown("### 📜 楚简档案库")
    st.markdown(f"""
        楚简出土情况汇总、楚墓编年总录、楚文化研究...
    
     """)
    # st.markdown("### 🔍 调试信息")
    # st.markdown(f"""
    # <div style="color: #D4AF37; font-size: 12px;">
    #     API Key前8位: {api_key[:8]}...
    # </div>
    # """, unsafe_allow_html=True)

    # 楚文化小贴士（增加文化氛围）
    st.markdown("### 📖 楚韵小识")
    st.markdown("""
    <div style="font-size: 13px; color: #E0E0E0; line-height: 1.6;">
        • 楚系文字又称"鸟虫书"，是金文的一种特殊形态<br>
        • 楚国青铜器以失蜡法铸造，纹饰繁复瑰丽<br>
        • 郭店楚简出土于湖北荆门，记载了早期儒道思想
    </div>
    """, unsafe_allow_html=True)

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """您好！我是楚文化智能问答助手，专注于解答楚系文字、楚式文物、楚地考古相关问题。例如：
- 郭店楚简出土于哪一年？
- 楚式青铜器的纹饰有哪些特点？
- 鸟虫书的艺术特征是什么？

❗还可以对知识挑战的问题进行详细解答噢！"""
        }
    ]

# 显示历史聊天记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 处理用户输入
if prompt := st.chat_input("请输入关于楚文化的问题，探寻荆楚文明的千年奥秘..."):
    # 保存并显示用户问题
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 调用知识库问答并显示结果
    with st.chat_message("assistant"):
        with st.spinner("🕯️ 正在检索楚简帛书，梳理荆楚文脉..."):
            answer, citations = query_knowledge_base(prompt)
            st.write(answer)

            # 显示检索到的参考内容（验证是否真的调用了知识库）
            if citations:
                with st.expander("📜 出土文献参考", expanded=False):
                    st.markdown("### 🔍 知识库引证内容：")
                    for idx, cite in enumerate(citations, 1):
                        # 提取引用内容（兼容zai库的返回格式）
                        cite_content = getattr(cite, 'content', '无')
                        st.markdown(f"""
                        <div style="padding: 8px; margin: 5px 0; border-left: 3px solid var(--chu-gold);">
                            <strong>参考{idx}：</strong> {cite_content[:300]}...
                        </div>
                        """, unsafe_allow_html=True)

    # 保存AI回答
    st.session_state.messages.append({"role": "assistant", "content": answer})