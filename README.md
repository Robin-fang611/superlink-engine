# SuperLink Data Engine

**专业的 B2B 商业线索挖掘与自动化营销工厂**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io/)

## �� 项目简介

SuperLink Data Engine 是一款强大的 B2B 商业线索挖掘与自动化营销工具，集成了智能搜索、AI 数据处理、邮箱验证、自动化邮件营销和客户意向分析功能。

### 核心能力

- 🎯 **智能搜索**：基于 Serper API 和 Google 搜索，支持多种搜索策略
- 🤖 **AI 处理**：使用智谱 AI (GLM-4) 进行数据提取和结构化
- ✉️ **邮箱验证**：三阶段邮箱验证（格式、MX 记录、SMTP 握手）
- �� **自动营销**：HTML 模板批量群发，支持 Jinja2 模板渲染
- 📊 **意向分析**：AI 自动识别客户回复意向
- 💾 **数据持久化**：SQLite 数据库存储

## 🚀 快速开始

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/YOUR_USERNAME/superlink-data.git
cd superlink-data
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**

创建 `.env` 文件并填写配置：
```ini
# 基础 API 配置
SERPER_API_KEY=your_serper_api_key
ZHIPUAI_API_KEY=your_zhipuai_api_key

# 邮箱系统配置
SENDER_EMAIL=your_email@example.com
SENDER_PASSWORD=your_email_password
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
IMAP_SERVER=imap.example.com
IMAP_PORT=993

# 系统配置
USE_PROXY=False
```

4. **启动应用**
```bash
streamlit run app.py
```

5. **访问界面**

在浏览器中打开 `http://localhost:8501`

## 📦 项目结构

```
superlink-data/
├── app.py                      # Streamlit 主应用
├── main.py                     # 命令行模式入口
├── requirements.txt            # 依赖列表
├── core/                       # 核心功能模块
│   ├── automation.py          # 自动化流程
│   ├── config.py              # 配置加载
│   ├── database.py            # 数据库操作
│   ├── email_sender.py        # 邮件发送
│   ├── feedback_processor.py  # 反馈处理
│   ├── processor.py           # AI 数据处理
│   ├── searcher.py            # 搜索执行
│   ├── verifier.py            # 邮箱验证
│   └── enhanced/              # 增强功能模块
├── templates/                  # HTML 邮件模板
└── output/                     # 输出文件目录
```

## 🎯 功能模块

### 1. 智能挖掘模块

支持四种搜索策略：
- 欧美物流商
- 欧美进口商
- 中国货代同行
- 中国出口工厂

**增强功能**：
- Ultra 模式：自动裂变 50+ 城市关键词
- Deep Dive：深度挖掘 LinkedIn 关键决策人
- 高级过滤：AI 自动识别中小企业

### 2. 营销触达模块

- 批量群发 HTML 邮件
- Jinja2 模板渲染
- 发送频率限制

### 3. 反馈看板模块

- 自动监测邮件回复
- AI 意向分类（高意向/咨询/无意向/投诉）
- 可视化统计图表

## ⚙️ API 配置

| 服务 | 用途 | 获取地址 |
|------|------|----------|
| Serper API | Google 搜索 | https://serper.dev |
| 智谱 AI | 数据提取 | https://open.bigmodel.cn |

## 📊 使用示例

### 命令行模式
```bash
python main.py
```

### Streamlit 模式
```bash
streamlit run app.py
```

## 🗄️ 数据库

使用 SQLite 数据库 (`output/superlink.db`)：
- verified_leads：验证后的线索
- email_send_records：邮件发送记录
- feedback_records：客户回复记录

## 🔧 高级功能

### 邮箱验证三阶段
1. 格式验证
2. MX 记录验证
3. SMTP 握手验证

### 联系人深度挖掘
- 搜索 LinkedIn 关键决策人
- 智能猜测企业邮箱

## 📝 许可证

MIT License

---

**SuperLink Data Engine v2.0**

Made with ❤️ by SuperLink Development Team
