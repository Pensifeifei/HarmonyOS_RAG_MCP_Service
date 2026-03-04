# 技术栈强制要求
- **语言**：Python 3.10+。
- **配置管理**：`python-dotenv` (所有的外部路径和模型名称必须写在 `.env` 中)。
- **MCP 框架**：`mcp` (使用官方 `FastMCP` 模块)。
- **向量数据库**：`chromadb` (配置为 PersistentClient 本地持久化)。
- **文档处理**：`langchain_text_splitters` 的 `MarkdownHeaderTextSplitter`。
- **离线模型**：`sentence-transformers` (如 `BAAI/bge-m3` 或 `bge-large-zh-v1.5`)。严禁出现任何请求外部网络 API 的代码。

# 编码风格规范 ("Slow is Fast")
1. **类型安全**：所有函数必须有精确的 Python Type Hints，参数和返回值含义必须在 Docstring 中写明。
2. **防御性编程**：MCP 工具函数被大模型调用时输入参数不可控，必须做边界检查和 `try-except` 包裹。
3. **日志输出**：配置标准的 `logging` 模块，方便在 VS Code Output 面板排查 MCP stdio 通信时的错误。

# 关键架构决策
- **Metadata 过滤优先**：为了防止知识库检索污染，入库时必须把文件的相对路径（如 "应用配置文件(Stage模型)"）作为 Metadata 注入 ChromaDB。检索时强制优先利用这些 Metadata 缩小范围。
