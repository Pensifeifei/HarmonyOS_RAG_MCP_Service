# HarmonyOS RAG MCP Service

纯离线运行的鸿蒙文档 RAG 检索服务。将华为 HarmonyOS V5 官方文档向量化存入本地 ChromaDB，通过 [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) 向本地大模型 Agent（如 Cline）暴露检索工具，解决大模型对最新 ArkTS / HarmonyOS API 的幻觉问题。

## 功能

- **`list_knowledge_categories`** — 列出知识库中所有文档分类
- **`search_harmony_docs`** — 向量语义搜索，支持 category 过滤

## 技术栈

| 组件 | 选型 |
|------|------|
| Embedding 模型 | `BAAI/bge-large-zh-v1.5`（本地 SentenceTransformers） |
| 向量数据库 | ChromaDB（本地持久化，HNSW + cosine） |
| 文本切分 | LangChain `MarkdownHeaderTextSplitter` |
| MCP 框架 | FastMCP（stdio 传输） |
| Python | >= 3.12 |

## 目录结构

```
HarmonyOS_RAG_MCP_Service/
├── server_main.py           # MCP 服务端入口
├── ingest_main.py           # 文档入库脚本
├── requirements.txt
├── .env                     # 环境变量配置
├── .env.example             # 配置模板
├── chroma_data/             # ChromaDB 持久化目录（git ignored）
├── src/
│   ├── config.py            # 配置读取
│   ├── logger.py            # 日志模块
│   ├── ingest/              # 入库管线
│   │   ├── file_scanner.py  # 目录扫描 + category 提取
│   │   ├── text_splitter.py # Markdown 标题切分
│   │   └── vector_store.py  # Embedding + ChromaDB 写入
│   └── server/
│       └── query_engine.py  # 向量搜索封装
└── rules/                   # 项目规则与进度追踪
```

---

## 快速开始（联网环境）

### 1. 环境准备

```bash
# 需要 Python 3.12+
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置

复制 `.env.example` 为 `.env`，修改文档路径：

```bash
cp .env.example .env
```

```dotenv
# [必填] 上游清洗好的 Markdown 文档目录
DOCS_SOURCE_PATH=/path/to/your/harmonyos/docs

# [可选] ChromaDB 存储路径，默认 ./chroma_data
CHROMA_STORAGE_PATH=./chroma_data

# [可选] Embedding 模型，默认 BAAI/bge-large-zh-v1.5
EMBEDDING_MODEL_NAME=BAAI/bge-large-zh-v1.5
```

### 3. 文档入库

```bash
# 首次入库（模型会自动从 HuggingFace 下载约 1.3GB）
python ingest_main.py

# 强制重建（清空后重新入库）
python ingest_main.py --force
```

### 4. 启动 MCP Server

```bash
python server_main.py
```

Server 以 stdio 模式运行，等待 MCP 客户端连接。

---

## 离线部署（内网环境）

适用场景：在联网机器上打包，部署到无法访问外网的内网 macOS 机器。

### 在联网机器上打包

```bash
cd /path/to/HarmonyOS_RAG_MCP_Service

# 1. 下载 pip 离线包
.venv/bin/pip download -r requirements.txt -d ./offline_packages

# 2. 打包 Embedding 模型缓存
tar -czf bge-model.tar.gz \
    -C ~/.cache/huggingface/hub \
    models--BAAI--bge-large-zh-v1.5

# 3. 打包整个项目（含向量库 + 离线包）
cd ..
tar -czf mcp_deploy.tar.gz \
    --exclude='.venv' \
    --exclude='__pycache__' \
    HarmonyOS_RAG_MCP_Service/
```

需要传输到内网的文件：

| 文件 | 大小（约） | 内容 |
|------|-----------|------|
| `mcp_deploy.tar.gz` | ~数百 MB | 项目代码 + `chroma_data/` + 离线 pip 包 |
| `bge-model.tar.gz` | ~1.3 GB | Embedding 模型 |

### 在内网机器上部署

```bash
# 1. 安装 Python 3.12（如果内网有 Homebrew）
brew install python@3.12

# 2. 解压项目
tar -xzf mcp_deploy.tar.gz
cd HarmonyOS_RAG_MCP_Service

# 3. 创建虚拟环境
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate

# 4. 离线安装依赖（不访问网络）
pip install --no-index --find-links=./offline_packages -r requirements.txt

# 5. 恢复 Embedding 模型
mkdir -p ~/.cache/huggingface/hub
tar -xzf ../bge-model.tar.gz -C ~/.cache/huggingface/hub/

# 6. 配置 .env（DOCS_SOURCE_PATH 可指向任意空目录，搜索不依赖原文件）
vim .env

# 7. 验证（应输出入库的 chunk 数量，如 13264）
python -c "from src.server.query_engine import QueryEngine; e = QueryEngine(); print(e._collection.count())"
```

> **注意**：`DOCS_SOURCE_PATH` 仅在运行 `ingest_main.py` 重新入库时需要有效路径。如果只是使用搜索功能，可以指向一个空目录以避免启动时的警告。

---

## 配置 MCP 客户端

配置格式对所有客户端通用，只是配置文件位置不同。

**核心配置**（将路径替换为你的实际路径）：

```json
{
  "mcpServers": {
    "harmonyos-docs": {
      "command": "/your/project/path/.venv/bin/python",
      "args": ["/your/project/path/server_main.py"],
      "cwd": "/your/project/path"
    }
  }
}
```

> ⚠️ `command` 必须使用虚拟环境 Python 的**绝对路径**，不可使用 `python` 或 `python3`。

### Cline（VSCode 插件）

1. 打开 Cline 面板 → 点击 🔌 MCP Servers → **Configure MCP Servers**
2. 在打开的 `cline_mcp_settings.json` 中添加上述配置
3. 保存后 Cline 自动启动 server，面板中 `harmonyos-docs` 显示为绿色即成功

配置文件路径：
```
~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

### Cursor

项目级配置（推荐）：创建 `.cursor/mcp.json`，内容同上。

全局配置：`~/.cursor/mcp.json`

### Claude Desktop

配置文件路径：
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

---

## 使用示例

配置好 MCP 客户端后，在对话中直接提问即可：

- *"帮我查一下 ArkTS 中如何实现页面路由跳转"*
- *"HarmonyOS 中 AbilityStage 的生命周期是什么"*
- *"ohpm 包管理工具怎么安装三方库"*

LLM Agent 会自动调用 `search_harmony_docs` 工具检索相关文档，基于检索结果生成回答。

---

## License

Internal use only.
