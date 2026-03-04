# 核心目标
构建一个纯内网环境下的 RAG 检索服务，将上游产出的鸿蒙文档转化为本地大模型可用的 MCP 工具，解决跨端开发时大模型对最新 ArkTS API 的幻觉问题。

# 整体架构
1. **环境与配置层**
   - 通过 `.env` 文件读取环境变量（上游文档源路径 `DOCS_SOURCE_PATH`、本地向量库存储路径 `CHROMA_STORAGE_PATH` 等）。
2. **数据入库脚本 (Ingestion Engine)**
   - 独立脚本，按需手动执行。遍历 `DOCS_SOURCE_PATH`。
   - 核心逻辑：读取 `.md`，提取所在目录名为 Metadata，使用 LangChain 按 Markdown 标题切块，通过本地 SentenceTransformers 模型存入 ChromaDB。
3. **MCP 服务端 (MCP Server)**
   - 常驻进程，通过 `stdio` 与客户端（Cline）通信。
   - 暴露工具：`list_categories` (列出知识库分类) 和 `search_harmony_docs` (带 Metadata 过滤的向量检索)。

# 验收标准
1. **纯离线运行**：断网状态下（无法连接外部 API），从文本切分到向量检索全部正常运行。
2. **边界清晰**：完全独立于爬虫工程，只通过绝对路径读取上游的最终产物。
3. **鲁棒性**：MCP 服务在检索不到内容或遇到异常参数时，返回友好的错误提示字符串给大模型，进程绝不能崩溃。
