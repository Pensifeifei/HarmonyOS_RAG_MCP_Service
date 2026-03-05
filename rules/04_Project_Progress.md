# 项目进度 (Project Progress)

> **AI 强制行为指令（最高优先级）**：
> 1. **何时更新**：完成任何编码、修复、验证或配置任务后，在向用户报告结果 **之前** 必须更新本文件。
> 2. **更新内容**：
>    - 将已完成的 `[ ]` 改为 `[x]`。
>    - 如产生新的子任务或阶段，追加到对应位置。
>    - 如遇到 Bug，在"Bug 与问题记录"区追加条目，使用下方模板。
>    - 如达成里程碑，在"里程碑记录"区追加条目。
> 3. **Bug 记录模板**：`### #N — 标题` -> 触发 / 根因 / 解决 / 验证 / 状态。
> 4. **禁止遗漏**：即使是小修复也必须记录，确保本文件始终反映项目真实状态。

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
- [ ] 3.5 完成本地 stdio 模式的运行测试。

---

## 里程碑记录 (Milestone Log)

### 入库管线首次完整运行 (2026-03-05)
- **源目录**：`/Users/keyser/AI/RAG/HarmonyOS`
- **结果**：3146 个 Markdown 文件 -> 13264 个 chunks -> 全部写入 ChromaDB
- **耗时**：1144.4s（约 19 分钟）
- **模型**：`BAAI/bge-large-zh-v1.5`（首次运行自动下载约 1.3GB）

---

## Bug 与问题记录 (Bug & Issue Tracker)

### #1 — macOS 系统 Python 版本不兼容
- **环境**：macOS 自带 Python 3.9.6
- **问题**：`mcp` 包要求 Python >= 3.10，pip 安装时报 `No matching distribution found`
- **解决**：通过 `brew install python@3.12` 安装 Python 3.12，使用 `/opt/homebrew/bin/python3.12 -m venv .venv` 重建虚拟环境
- **状态**：已解决

### #2 — ChromaDB DuplicateIDError
- **触发**：入库批次 2000-2200 时报 `DuplicateIDError`
- **根因**：`_chunk_id()` 仅用 `source_path + content` 生成哈希，同一文件内出现完全相同的文本片段时产生碰撞
- **解决**：在 `_chunk_id()` 中加入 `index` 参数，使用 `source_path + index + content[:200]` 生成唯一 ID
- **验证**：修复后 `--force` 重跑，13264 chunks 全部成功写入，零错误
- **状态**：已解决
