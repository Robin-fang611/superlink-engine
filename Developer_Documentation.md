# SuperLink Data Engine 研发文档 (Developer Documentation)

## 1. 系统架构概述 (System Architecture)
SuperLink Data Engine 采用典型的**解耦式层级架构**，旨在实现搜索、处理、持久化与展示的完全分离。

### 1.1 核心组件
- **UI 层 (Presentation)**: 基于 Streamlit 驱动的 Web 控制台 ([app.py](file:///d:/business%20bot/%E9%A1%B9%E7%9B%AE/superlink%E6%95%B0%E6%8D%AE/app.py))。
- **调度层 (Orchestration)**: 负责任务管理、多线程调度及进度跟踪 ([automation.py](file:///d:/business%20bot/%E9%A1%B9%E7%9B%AE/superlink%E6%95%B0%E6%8D%AE/core/automation.py))。
- **逻辑层 (Business Logic)**:
    - **Searcher**: 封装 Serper API，负责原始数据的检索 ([searcher.py](file:///d:/business%20bot/%E9%A1%B9%E7%9B%AE/superlink%E6%95%B0%E6%8D%AE/core/searcher.py))。
    - **Processor**: 集成 ZhipuAI (GLM-4)，执行数据审计、清洗与提取 ([processor.py](file:///d:/business%20bot/%E9%A1%B9%E7%9B%AE/superlink%E6%95%B0%E6%8D%AE/core/processor.py))。
    - **Deduplicator**: 基于指纹哈希的去重引擎 ([deduplicator.py](file:///d:/business%20bot/%E9%A1%B9%E7%9B%AE/superlink%E6%95%B0%E6%8D%AE/core/deduplicator.py))。
- **配置层 (Configuration)**: 全局环境变量与代理控制 ([config.py](file:///d:/business%20bot/%E9%A1%B9%E7%9B%AE/superlink%E6%95%B0%E6%8D%AE/core/config.py))。

---

## 2. 核心模块详解 (Module Deep Dive)

### 2.1 Searcher 模块
- **技术选型**: RESTful API (Serper.dev)。
- **核心逻辑**: 
    - 针对不同角色（Logistics, Importer, Exporter）构建特定的高级搜索指令。
    - `expand_keywords` 方法利用地理位置和行业修饰符实现关键词的“裂变”，增加覆盖面。
    - 支持分页采集（Page 1-3）。

### 2.2 Processor 模块
- **技术选型**: ZhipuAI SDK, GLM-4 模型。
- **数据流**: 
    1. 接收 Searcher 返回的原始 JSON。
    2. 将 `Title`, `Snippet`, `Link` 拼接为 AI 上下文。
    3. **AI 审计**: 严格执行 SME 过滤逻辑（剔除年营收 > $100M 的巨头）。
    4. **结构化提取**: 强制输出为统一的 JSON 列表格式。
    5. **鲁棒性处理**: `_clean_json` 方法自动处理 AI 输出中的 Markdown 杂质。

### 2.3 Deduplicator 模块
- **存储介质**: `output/history_log.json`。
- **去重维度**: URL (来源链接)、Company Name (公司名)、Email (邮箱)、Phone (电话)。
- **持久化**: 采用原子写入模式，确保在多线程环境下不损坏历史记录。

---

## 3. 自动化与线程管理 (Automation & Concurrency)

### 3.1 工厂模式逻辑
- **多线程实现**: 使用 `threading.Thread` 在后台执行长期运行的采集任务，防止 Streamlit 主线程阻塞。
- **状态同步**: 通过 `threading.Event` 实现任务的安全停止。
- **断点续传**: 实时维护 `progress_log.json`，每次搜索前检查已完成城市列表。

---

## 4. 技术栈 (Tech Stack)
- **语言**: Python 3.10+
- **Web 框架**: Streamlit
- **数据处理**: Pandas
- **异步/网络**: Requests, HTTPX
- **版本控制**: Git (GitHub 托管)
- **云端部署**: Streamlit Cloud

---

## 5. 扩展性设计与预留接口 (Extensibility)

### 5.1 待升级方向
1.  **多模型支持**: `Processor` 类中预留了 `provider` 字段，可轻松扩展至 OpenAI 或其他 LLM。
2.  **异步 IO 升级**: 计划将 `requests` 迁移至 `httpx` 或 `aiohttp` 以支持并发搜索（目前为线性搜索）。
3.  **数据库存储**: 预留了从 `history_log.json` 迁移至 `SQLite` 或 `PostgreSQL` 的接口，以应对百万级数据的去重。
4.  **邮件自动营销**: `output/` 下的 CSV 可作为后续“自动发信模块”的输入源。

---

## 6. 环境安全与部署策略 (Deployment)
- **Secrets 管理**: 本地依赖 `.env`，云端强制依赖 Streamlit Secrets 映射。
- **CI/CD**: 通过 GitHub Push 触发 Streamlit Cloud 的自动构建镜像。
- **隔离性**: 强制将虚拟环境 (`.venv`) 和临时数据写入 `.gitignore`。

---
**Robin (SuperLink Dev Team)**
**Date**: 2026-01-30
