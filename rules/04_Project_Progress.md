# 项目进度 (Project Progress)

> **AI 行为指令**：在执行完每一项任务后，你必须更新此文件，将对应的 `[ ]` 修改为 `[x]`，并在下方“Bug 与问题记录”区追加你在开发中遇到的问题及解决方案。

## 阶段 1：工程初始化与基建
- [x] 1.1 初始化 Python 虚拟环境，生成初始 `requirements.txt`。
- [x] 1.2 搭建基础目录结构（`src/ingest/`, `src/server/`）。
- [x] 1.3 配置 `.env` 文件模板及环境变量读取模块。
- [x] 1.4 配置全局日志模块。

## 阶段 2：向量入库管线开发 (Ingestion)
- [x] 2.1 编写目录遍历逻辑，过滤无关文件/Archived 目录，正确提取相对路径作为 Metadata。
- [x] 2.2 集成 `MarkdownHeaderTextSplitter` 进行文本分块。
- [x] 2.3 集成本地 SentenceTransformers 模型并完成 ChromaDB 数据持久化写入。
- [x] 2.4 编写独立的 `ingest_main.py` 跑通测试数据。

## 阶段 3：FastMCP 服务端开发
- [x] 3.1 编写 `server_main.py` 初始化 FastMCP 实例。
- [x] 3.2 实现 ChromaDB 的读取与查询包装函数。
- [x] 3.3 暴露 `list_knowledge_categories` 工具。
- [x] 3.4 暴露 `search_harmony_docs` 工具，并支持 category 过滤。
- [ ] 3.5 完成本地 stdio 模式的运行测试（待入库数据后执行）。

---

## 🐛 Bug 与问题记录 (Bug & Issue Tracker)

### #1 — macOS 系统 Python 版本不兼容
- **环境**：macOS 自带 Python 3.9.6
- **问题**：`mcp` 包要求 Python ≥ 3.10，pip 安装时报 `No matching distribution found`
- **解决**：通过 `brew install python@3.12` 安装 Python 3.12，使用 `/opt/homebrew/bin/python3.12 -m venv .venv` 重建虚拟环境
- **状态**：已解决
