根据您的反馈，由于无法注册 Hunter.io，我将执行以下系统清理和 API 盘点任务：

## **1. 剩余需要 API 的平台盘点**
目前系统中仍保留且需要 API 支持的平台如下：
- **核心平台（已配置）**：
    - **Serper.dev**：提供 Google 搜索支持，是系统运行的基础。
    - **智谱 AI (GLM-4)**：负责线索提取与意向分析，是系统的“大脑”。
- **增强平台（待配置/可选）**：
    - **Apollo.io**：备选 B2B 数据库，用于更深度的企业信息挖掘。
    - **Snov.io**：备选领英挖掘工具，用于定向获取领英上的联系方式。

## **2. 执行清理任务**
- **代码清理**：
    - 从 [third_party.py](file:///d:/business%20bot/%E9%A1%B9%E7%9B%AE/superlink%E6%95%B0%E6%8D%AE/core/enhanced/third_party.py) 中彻底删除 `HunterIO` 类及其相关逻辑。
    - 检查并确保其他核心模块（如 `app.py`）不含有任何 Hunter 的冗余引用。
- **文档更新**：
    - 修改 [API_Acquisition_Guide.md](file:///d:/business%20bot/%E9%A1%B9%E7%9B%AE/superlink%E6%95%B0%E6%8D%AE/MD/API_Acquisition_Guide.md)，移除关于 Hunter.io 的注册引导。
    - 在 [个人邮箱线索获取增强计划.md](file:///d:/business%20bot/%E9%A1%B9%E7%9B%AE/superlink%E6%95%B0%E6%8D%AE/MD/SuperLink%20Data%20Engine%20%E4%B8%AA%E4%BA%BA%E9%82%AE%E7%AE%B1%E7%BA%BF%E7%B4%A2%E8%8E%B7%E5%8F%96%E5%A2%9E%E5%BC%BA%E8%AE%A1%E5%88%92.md) 中剔除 Hunter 相关描述，转向以 Apollo 和 Snov.io 为主的增强方案。
- **环境配置**：
    - 从 `.env` 模板或说明中移除 `HUNTER_API_KEY`。

如果您确认此清理方案，我将立即开始执行。