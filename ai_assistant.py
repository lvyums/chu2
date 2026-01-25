import os
import streamlit as st
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_community.document_loaders import TextLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

# 这一行会自动寻找并加载 .env 文件里的变量
load_dotenv()
# ----------------- 配置区域 -----------------
# 这里填入你的 API KEY
# 如果用 OpenAI: OS.environ["OPENAI_API_KEY"] = "sk-..."
# 如果用 智谱GLM (推荐):
os.environ["ZHIPUAI_API_KEY"] = "ZHIPUAI_API_KEY"

# 配置 LLM 和 Embedding
# 智谱的兼容接口地址是 https://open.bigmodel.cn/api/paas/v4/
# 模型使用 GLM-4-Flash (速度快免费/便宜) 或 GLM-4
llm = ChatOpenAI(
    temperature=0.3,
    model="glm-4-flash",
    openai_api_base="https://open.bigmodel.cn/api/paas/v4/",
    openai_api_key=os.environ["ZHIPUAI_API_KEY"]
)


# 智谱的 Embedding 目前 LangChain 兼容性稍差，这里用通用的或者 OpenAI 格式
# 如果为了简单，这里我们可以临时用 huggingface 的开源模型，或者直接用 OpenAI 的接口格式调用智谱 embedding
# 为了演示最简便的方法，我们假设你用的是智谱的标准 embedding (需要安装 zhipuai 库)
# 但为降低门槛，这里演示使用 OpenAI 兼容模式（或者如果你有 OpenAI Key 直接用即可）
# 下面展示标准 LangChain 流程
# -------------------------------------------

@st.cache_resource
def init_knowledge_base():
    """
    初始化知识库：读取txt -> 切分 -> 向量化 -> 存入向量数据库
    使用 @st.cache_resource 保证只有第一次运行时加载，之后直接读取缓存
    """
    # 1. 加载数据
    if not os.path.exists("chu_knowledge.txt"):
        return None

    loader = TextLoader("chu_knowledge.txt", encoding="utf-8")
    docs = loader.load()

    # 2. 切分文本 (Chunks)
    # 把长文章切成小块，方便检索
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)

    # 3. 向量化 (Embeddings)
    # 注意：如果没有 OpenAI 额度，可以使用 'sentence-transformers' (免费本地模型)
    # 这里演示使用 ZhipuAI 的 Embedding (需自定义或使用兼容层)，
    # 为简化代码，此处假设你使用 OpenAI 或 智谱兼容的 Embedding 接口
    embeddings = OpenAIEmbeddings(
        model="embedding-2",  # 智谱的 embedding 模型名
        openai_api_base="https://open.bigmodel.cn/api/paas/v4/",
        openai_api_key=os.environ["ZHIPUAI_API_KEY"]
    )

    # 4. 存入 Chroma 向量数据库 (内存模式)
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)

    return vectorstore


# 初始化界面
st.title("🛡️ 楚文化智能问答助手")
st.markdown("基于 **LangChain + GLM** | 专注于楚系文字与考古知识")

# 侧边栏
with st.sidebar:
    st.write("📖 **知识库状态**")
    if os.path.exists("chu_knowledge.txt"):
        st.success("知识库文件已检测到")
        if st.button("🔄 重建/更新知识库"):
            st.cache_resource.clear()
            st.rerun()
    else:
        st.error("请在根目录创建 chu_knowledge.txt 并放入资料")

# 加载知识库
vectorstore = init_knowledge_base()

if vectorstore:
    # 1. 定义提示词模板（这一步可以让 AI 扮演特定角色）
    prompt_template = ChatPromptTemplate.from_template("""
        你是一个考古学专家，请用通俗易懂但严谨的语言回答用户的问题。你专门研究楚系文化（包括青铜器、简帛文字、漆木器及战国历史）。
        
        你的任务是基于提供的【已知信息】（Context）来回答用户的提问。请遵循以下准则：
        
        1.  **角色设定**：你就像一位知识渊博的博物馆金牌讲解员。面对专业术语（如“鸟虫书”、“失蜡法”、“悬山顶”），尽量用现代生活中的类比或通俗语言进行解释，但必须保持历史事实的准确性。
        2.  **依据事实**：请严格基于【已知信息】回答。如果信息中包含具体的出土年代、地点或尺寸数据，请务必引用以增加可信度。
        3.  **诚实原则**：如果【已知信息】中没有包含回答问题所需的知识，请直接告知用户：“抱歉，目前的考古资料库中暂无此记录”，严禁臆测或编造历史事实。
        4.  **回答结构**：
            *   先直接给出核心结论。
            *   再展开详细描述（文物的形制、纹饰、历史背景）。
            *   最后（如果相关）可以延伸一两句该文物在楚文化中的独特地位或审美价值。
        5.  **语气风格**：客观、典雅、引人入胜。不要使用过于僵硬的机器翻译腔，也不要使用轻浮的网络用语。
        
        【已知信息】：
        {context}
        
        用户问题：
        {question}
       """)

    # 2. 创建文档处理链（Stuff链：把检索到的文档塞进 prompt）
    document_chain = create_stuff_documents_chain(llm, prompt_template)

    # 3. 创建检索链（把 检索器 和 文档链 连起来）
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    qa_chain = create_retrieval_chain(retriever, document_chain)

    # 聊天界面
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 显示历史记录
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 处理用户输入
    if prompt := st.chat_input("请输入关于楚文化的问题，例如：什么是鸟虫书？"):
        # 1. 显示用户问题
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # 2. 调用 AI 回答
        with st.chat_message("assistant"):
            with st.spinner("🔍 正在检索考古资料库..."):
                response = qa_chain.invoke({"query": prompt})
                answer = response["result"]
                source_docs = response["source_documents"]

                st.write(answer)

                # (可选) 显示参考来源，增强可信度
                with st.expander("📚 参考资料来源"):
                    for doc in source_docs:
                        st.caption(f"...{doc.page_content}...")

        # 3. 保存 AI 回答
        st.session_state.messages.append({"role": "assistant", "content": answer})

else:
    st.info("👈 请先在侧边栏确认知识库文件已就绪。")