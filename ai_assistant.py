import os
import streamlit as st
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA

# ----------------- 配置区域 -----------------
# 这里填入你的 API KEY
# 如果用 OpenAI: OS.environ["OPENAI_API_KEY"] = "sk-..."
# 如果用 智谱GLM (推荐):
os.environ["ZHIPUAI_API_KEY"] = "你的_ZHIPU_API_KEY"

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
    # 创建检索链
    # k=3 表示每次找 3 条最相关的资料
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

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