# SuperLink Data Engine 实现指南

## 项目概述

这是一个基于 Streamlit + Tailwind CSS 的现代化 UI 界面，用于 B2B 国际贸易线索挖掘系统。

## 技术栈

- **后端框架**: Python + Streamlit

- **前端样式**: Tailwind CSS v3

- **图标库**: Font Awesome 6

- **数据处理**: Pandas, ZhipuAI SDK

## 快速开始

### 1. 环境准备

```bash

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install streamlit pandas requests python-dotenv zhipuai
```

### 2. 项目结构

```Plain Text

superlink/
├── app.py                 # 主应用文件
├── requirements.txt       # 依赖列表
├── .env                   # 环境变量
├── assets/                # 静态资源
│   └── custom.css         # 自定义样式
├── utils/                 # 工具函数
│   ├── search_engine.py   # 搜索引擎模块
│   ├── ai_processor.py    # AI 处理模块
│   └── data_manager.py    # 数据管理模块
└── data/                  # 数据存储
    └── results/           # 搜索结果
```

### 3. 核心文件创建

#### requirements.txt

```Plain Text

streamlit==1.32.0
pandas==2.2.1
requests==2.31.0
python-dotenv==1.0.1
zhipuai==2.0.1
```

#### .env 文件

```Plain Text

# API 密钥
ZHIPUAI_API_KEY=your_zhipuai_api_key
SERPER_API_KEY=your_serper_api_key

# 应用配置
APP_PASSWORD=your_password
DEBUG=True
```

#### [app.py](app.py) (主应用文件)

```python

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from utils.search_engine import SearchEngine
from utils.ai_processor import AIProcessor
from utils.data_manager import DataManager

# 加载环境变量
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="SuperLink Data Engine",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
with open('assets/custom.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# 身份验证
def authenticate():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        password = st.text_input("请输入访问密码", type="password")
        if st.button("登录"):
            if password == os.getenv("APP_PASSWORD"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密码错误，请重试")
        st.stop()

# 主应用
def main():
    authenticate()
    
    # 侧边栏
    with st.sidebar:
        st.title("🔗 SuperLink")
        st.subheader("任务配置")
        
        # 搜索类型选择
        search_type = st.radio(
            "搜索目标类型",
            ["欧美物流商", "欧美进口商", "中国货代同行", "中国出口工厂"]
        )
        
        # 关键词输入
        keywords = st.text_input("搜索关键词", placeholder="furniture, electronics")
        
        # 任务名称
        task_name = st.text_input("任务名称", placeholder="美国家具进口商搜索")
        
        # 执行模式
        mode = st.selectbox(
            "执行模式",
            ["单次搜索", "批量搜索", "工厂模式"]
        )
        
        # 执行按钮
        if st.button("开始搜索", type="primary"):
            if keywords and task_name:
                with st.spinner("正在搜索中..."):
                    # 执行搜索
                    search_engine = SearchEngine()
                    results = search_engine.search(search_type, keywords, mode)
                    
                    # AI 处理
                    ai_processor = AIProcessor()
                    processed_results = ai_processor.process(results)
                    
                    # 保存结果
                    data_manager = DataManager()
                    data_manager.save_results(processed_results, task_name)
                    
                    st.success("搜索完成！")
                    st.session_state.results = processed_results
            else:
                st.warning("请填写关键词和任务名称")
    
    # 主内容区
    st.title("数据引擎控制台")
    
    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("今日搜索次数", "128", "+12")
    with col2:
        st.metric("有效线索数", "2,456", "+42")
    with col3:
        st.metric("目标企业类型", "4")
    with col4:
        st.metric("覆盖国家/地区", "50+")
    
    # 结果展示
    st.subheader("搜索结果")
    
    if 'results' in st.session_state and st.session_state.results:
        df = pd.DataFrame(st.session_state.results)
        
        # 数据表格
        st.dataframe(
            df,
            column_config={
                "company_name": "公司名称",
                "location": "国家/城市",
                "contact_person": "联系人",
                "email": "邮箱",
                "phone": "电话",
                "business_scope": "业务范围",
                "source_url": st.column_config.LinkColumn("来源")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # 导出按钮
        col1, col2 = st.columns([1, 1])
        with col1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "导出为CSV",
                csv,
                "search_results.csv",
                "text/csv",
                key='download-csv'
            )
        with col2:
            excel_buffer = pd.ExcelWriter('search_results.xlsx', engine='xlsxwriter')
            df.to_excel(excel_buffer, index=False, sheet_name='Results')
            excel_buffer.close()
            with open('search_results.xlsx', 'rb') as f:
                st.download_button(
                    "导出为Excel",
                    f,
                    "search_results.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key='download-excel'
                )
    else:
        st.info("请在左侧配置任务并开始搜索")

if __name__ == "__main__":
    main()
```

#### assets/custom.css

```css

/* 自定义样式 */
.stApp {
    background-color: #f8fafc;
}

.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 0.5rem;
    padding: 0.5rem 1rem;
    font-weight: 500;
}

.stButton>button:hover {
    background-color: #1d4ed8;
}

.stTextInput>div>div>input {
    border-radius: 0.5rem;
    border: 1px solid #e2e8f0;
    padding: 0.5rem 0.75rem;
}

.stSidebar {
    background-color: white;
    border-right: 1px solid #e2e8f0;
}

.stMetric {
    background-color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}
```

### 4. 工具模块示例

#### utils/search\[_engine.py](_engine.py)

```python

import requests
import os
from dotenv import load_dotenv

load_dotenv()

class SearchEngine:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        self.base_url = "https://google.serper.dev/search"
    
    def search(self, search_type, keywords, mode):
        """执行搜索"""
        # 根据搜索类型构建查询
        query_templates = {
            "欧美物流商": "logistics provider in USA Europe {keywords}",
            "欧美进口商": "importer distributor in USA Europe {keywords}",
            "中国货代同行": "freight forwarder in China {keywords}",
            "中国出口工厂": "exporter factory in China {keywords}"
        }
        
        query = query_templates[search_type].format(keywords=keywords)
        
        # 调用搜索API
        payload = {
            "q": query,
            "num": 20,
            "gl": "us" if "欧美" in search_type else "cn"
        }
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(self.base_url, json=payload, headers=headers)
        return response.json()
```

#### utils/ai\[_processor.py](_processor.py)

```python

import zhipuai
import os
from dotenv import load_dotenv

load_dotenv()

class AIProcessor:
    def __init__(self):
        zhipuai.api_key = os.getenv("ZHIPUAI_API_KEY")
    
    def process(self, search_results):
        """处理搜索结果"""
        # 提取需要处理的内容
        contents = []
        for result in search_results.get('organic', []):
            contents.append({
                'title': result.get('title'),
                'snippet': result.get('snippet'),
                'link': result.get('link')
            })
        
        # 调用AI处理
        processed_results = []
        for content in contents:
            try:
                response = zhipuai.model_api.invoke(
                    model="glm-4",
                    prompt=f"""
                    请从以下网页内容中提取企业信息：
                    标题：{content['title']}
                    内容：{content['snippet']}
                    
                    请以JSON格式返回，包含以下字段：
                    - company_name: 公司名称
                    - location: 注册国家/城市
                    - contact_person: 业务负责人
                    - email: 公开邮箱
                    - phone: 公开电话
                    - business_scope: 业务范围
                    - source_url: 来源URL
                    """,
                    temperature=0.1
                )
                
                processed_results.append(response)
            except Exception as e:
                print(f"AI处理失败: {e}")
        
        return processed_results
```

### 5. 运行应用

```bash

# 启动应用
streamlit run app.py

# 访问地址
# http://localhost:8501
```

## 部署选项

### Streamlit Cloud 部署

1. 将代码推送到 GitHub

2. 访问 [share.streamlit.io](https://share.streamlit.io)

3. 连接 GitHub 仓库

4. 配置环境变量

5. 部署应用

### 本地服务器部署

```bash

# 安装生产环境依赖
pip install gunicorn

# 启动服务
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:server
```

## 功能扩展建议

1. **用户管理**：添加多用户支持和权限控制

2. **任务调度**：支持定时任务和任务队列

3. **数据可视化**：集成更丰富的图表展示

4. **API 接口**：提供 RESTful API 供其他系统调用

5. **缓存机制**：添加搜索结果缓存提升性能

## 技术支持

如需技术支持，请联系 SuperLink Dev Team。
> （注：文档部分内容可能由 AI 生成）