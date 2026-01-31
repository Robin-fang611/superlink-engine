import streamlit as st
import os
import sys
import time
import pandas as pd
import glob
import json
import threading
from datetime import datetime
from dotenv import load_dotenv

# Ensure core modules can be imported
sys.path.append(os.getcwd())

from core.searcher import Searcher
from core.processor import Processor
from core.automation import AutomationManager

# Import Enhanced Modules
from core.enhanced.keyword_expander import KeywordExpander
from core.enhanced.async_searcher import AsyncSearcher
from core.enhanced.enhanced_processor import EnhancedProcessor

# ==============================================================================
# 0. GLOBAL SESSION MANAGEMENT
# ==============================================================================

class SessionManager:
    """全局会话管理器，用于限制并发访问人数"""
    _instance = None
    _lock = threading.Lock()
    _active_sessions = {} # session_id -> last_seen_timestamp
    MAX_USERS = 3
    TIMEOUT_SECONDS = 300 # 5分钟无操作自动释放名额

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SessionManager, cls).__new__(cls)
            return cls._instance

    def update_session(self, session_id):
        with self._lock:
            current_time = time.time()
            # 清理过期会话
            self._active_sessions = {
                sid: ts for sid, ts in self._active_sessions.items() 
                if current_time - ts < self.TIMEOUT_SECONDS
            }
            # 更新当前会话
            self._active_sessions[session_id] = current_time

    def get_active_count(self):
        with self._lock:
            current_time = time.time()
            return len([ts for ts in self._active_sessions.values() if current_time - ts < self.TIMEOUT_SECONDS])

    def can_access(self, session_id):
        with self._lock:
            current_time = time.time()
            # 清理过期会话
            self._active_sessions = {
                sid: ts for sid, ts in self._active_sessions.items() 
                if current_time - ts < self.TIMEOUT_SECONDS
            }
            # 如果已经在活跃列表中，允许访问
            if session_id in self._active_sessions:
                return True
            # 如果名额未满，允许访问
            return len(self._active_sessions) < self.MAX_USERS

# ==============================================================================
# 1. INITIALIZATION & UI STYLING
# ==============================================================================

def safe_get_secret(key, default=None):
    """Safely get a secret from Streamlit secrets or return default."""
    try:
        # st.secrets behaves like a dict but can raise exceptions if file is missing
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default

def apply_custom_styles():
    st.markdown("""
        <style>
        /* Main Container Styling */
        .main {
            background-color: #001f3f; /* 深蓝色背景 */
            color: #FFD700; /* 金色文字 */
        }
        
        /* 全局文字颜色调整 */
        .main p, .main span, .main label, .main h1, .main h2, .main h3, .main div {
            color: #FFD700 !important;
        }

        /* 针对输入框的文字颜色微调 */
        input {
            color: #000 !important; /* 输入内容保持黑色以便阅读 */
        }

        /* Card-like containers */
        div.stButton > button:first-child {
            background-color: #FFD700; /* 金色按钮 */
            color: #001f3f; /* 深蓝色文字 */
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            border: none;
            transition: all 0.3s ease;
        }
        
        div.stButton > button:hover {
            background-color: #e6c200;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #001529;
        }
        
        /* Metric styling */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            color: #FFD700 !important;
        }
        
        /* Custom Header */
        .header-container {
            padding: 1.5rem;
            background: #001529;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            margin-bottom: 2rem;
            text-align: center;
            border: 1px solid #FFD700;
        }
        
        .header-container h1, .header-container p {
            color: #FFD700 !important;
        }
        
        /* Dataframe styling */
        .stDataFrame {
            border: 1px solid #FFD700;
            border-radius: 8px;
            background-color: #001f3f;
        }
        </style>
    """, unsafe_allow_html=True)

def init_environment():
    """Initialize environment variables and directories."""
    load_dotenv()
    os.makedirs("output", exist_ok=True)
    
    # Check for .env file or Streamlit Secrets
    serper_key = os.getenv("SERPER_API_KEY") or safe_get_secret("SERPER_API_KEY")
    zhipu_key = os.getenv("ZHIPUAI_API_KEY") or safe_get_secret("ZHIPUAI_API_KEY")
    
    status = {
        "serper": bool(serper_key),
        "zhipu": bool(zhipu_key),
        "output_dir": os.path.exists("output")
    }
    return status

def check_password():
    """Returns True if the user had the correct password."""
    password_env = os.getenv("APP_PASSWORD") or safe_get_secret("APP_PASSWORD", "admin123")
    
    if not password_env:
        return True # No password required

    def password_entered():
        if st.session_state["password"] == password_env:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown('<div class="header-container"><h1>欢迎来到superlink数据库</h1><p>请输入引擎访问密码以继续。</p></div>', unsafe_allow_html=True)
        st.text_input("密码", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("密码", type="password", on_change=password_entered, key="password")
        st.error("😕 密码错误")
        return False
    return True

# Page Config
st.set_page_config(
    page_title="SuperLink 数据引擎",
    page_icon="🚀",
    layout="wide"
)

apply_custom_styles()

# --- Session Limiter ---
from streamlit.runtime.scriptrunner import get_script_run_ctx
ctx = get_script_run_ctx()
session_id = ctx.session_id if ctx else "default"

manager = SessionManager()
if not manager.can_access(session_id):
    st.error("🚦 系统繁忙 / System Busy")
    st.warning(f"当前已有 {manager.get_active_count()} 位用户正在使用。为了保证搜索性能，请排队等待名额释放。")
    st.info("💡 提示：当有其他用户关闭页面或超过 5 分钟未操作后，名额将自动释放。")
    if st.button("刷新重试"):
        st.rerun()
    st.stop()

# 正常访问则更新活跃状态
manager.update_session(session_id)
# -----------------------

# Global State Initialization
if 'init_done' not in st.session_state:
    st.session_state['api_status'] = init_environment()
    st.session_state['init_done'] = True

# Authentication
if not check_password():
    st.stop()

# ==============================================================================
# 2. HELPER FUNCTIONS
# ==============================================================================

def get_output_filename(task_name, keyword, module_name):
    """Generate a unique filename with task name, keyword, module and timestamp."""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M")
    
    # Sanitize inputs
    def sanitize(s):
        return "".join([c for c in s if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
    
    safe_task = sanitize(task_name) or "task"
    safe_keyword = sanitize(keyword) or "none"
    # Get short module name (e.g., "Logistics" from "1. Logistics (USA/EU)")
    safe_module = sanitize(module_name.split('.')[1].split('(')[0]) if '.' in module_name else sanitize(module_name)
    
    return f"output/{safe_task}_{safe_module}_{safe_keyword}_{timestamp}.csv"

def show_preview(file_path):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            st.success(f"✅ 数据已加载: `{os.path.basename(file_path)}`")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                with open(file_path, "rb") as f:
                    st.download_button(
                        label="📥 下载 CSV",
                        data=f,
                        file_name=os.path.basename(file_path),
                        mime="text/csv",
                    )
            with col2:
                st.caption(f"共找到线索: **{len(df) - 1}** 条 (首行元数据除外)")
            
            st.dataframe(df.head(100), use_container_width=True)
        except Exception as e:
            st.warning(f"预览错误: {e}")
    else:
        st.info("暂无可用数据文件。")

def list_history_files():
    files = glob.glob("output/*.csv")
    files.sort(key=os.path.getmtime, reverse=True)
    return files

# ==============================================================================
# 3. DASHBOARD COMPONENTS
# ==============================================================================

async def run_enhanced_task(module_idx, keyword, module_name, output_file):
    """Execute task using the new Enhanced engine (Async + AI Batching)."""
    expander = KeywordExpander()
    searcher = AsyncSearcher(concurrency=3) # Safe for cheap proxy
    processor = EnhancedProcessor()
    
    st.info("🔍 正在智能扩展关键词以实现最大覆盖...")
    module_id = str(module_idx + 1)
    # Expand for major regions
    expanded_queries = expander.expand(keyword, module_id)
    # Target more queries for maximum coverage
    target_queries = expanded_queries[:20] 
    
    st.info(f"🚀 正在启动 {len(target_queries)} 个子查询的并行搜索 (深度: 5页)...")
    raw_results = await searcher.search_batch(target_queries, pages_per_query=5)
    
    if not raw_results:
        st.warning("增强模式下未找到任何结果。")
        return False
        
    st.info(f"🧠 AI 正在分批处理 {len(raw_results)} 条原始数据...")
    all_leads = processor.process_batch_enhanced(raw_results, batch_size=15)
    
    if all_leads:
        # Save results
        from core.deduplicator import Deduplicator
        dedup = Deduplicator()
        unique_leads = dedup.filter_unique(all_leads)
        
        # Save to CSV with Metadata header
        df = pd.DataFrame(unique_leads)
        
        # Create metadata row
        metadata = pd.DataFrame([{
            "公司名称": f"任务模块: {module_name}",
            "注册国家/城市": f"核心关键词: {keyword}",
            "业务负责人": f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "公开邮箱": "---",
            "公开电话": "---",
            "业务范围": "---",
            "来源URL": "---"
        }])
        
        # Combine metadata with data
        final_df = pd.concat([metadata, df], ignore_index=True)
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        st.success(f"✨ 增强任务完成！共捕获 {len(unique_leads)} 条唯一线索。")
        return True
    return False

def show_api_status_dashboard():
    with st.sidebar:
        st.markdown("### 📊 系统仪表盘")
        status = st.session_state.get('api_status', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Serper 搜索**")
            st.markdown("🟢 正常" if status.get("serper") else "🔴 缺失")
        with col2:
            st.markdown(f"**智谱 AI**")
            st.markdown("🟢 正常" if status.get("zhipu") else "🔴 缺失")
            
        st.markdown("---")
        st.markdown("### 🛠️ 运行信息")
        st.caption(f"当前目录: `{os.getcwd()}`")
        st.caption(f"服务器端口: `3000` (映射中)")

# ==============================================================================
# 4. CORE LOGIC ADAPTERS
# ==============================================================================

def run_single_search(choice_idx, keyword, module_name, output_file):
    """Execute standard single-query search (Options 1-4)."""
    searcher = Searcher()
    processor = Processor()
    
    status_container = st.container()
    with status_container:
        st.info("🚀 正在启动搜索引擎...")
    
    try:
        if choice_idx == 0: results = searcher.search_logistics_usa_europe(keyword)
        elif choice_idx == 1: results = searcher.search_importer_usa_europe(keyword)
        elif choice_idx == 2: results = searcher.search_china_forwarder(keyword)
        elif choice_idx == 3: results = searcher.search_china_exporter(keyword)
        else: results = {}
            
        if not results:
            st.warning("⚠️ 未找到任何结果。请检查关键词或代理设置。")
            return False

        st.info("🧠 智谱 AI 正在分析并提取线索...")
        
        # We need to manually save here to include metadata if needed, 
        # but let's first get the data from processor.
        # Note: process_and_save normally handles saving. 
        # To maintain consistency, we'll let it save and then we can prepend metadata if we want,
        # or better, we modify process_and_save to handle it.
        # For now, let's just use the existing one and I will update processor.py later.
        processor.process_and_save(results, output_file=output_file)
        
        # After saving, let's prepend the metadata line
        if os.path.exists(output_file):
            df = pd.read_csv(output_file)
            metadata = pd.DataFrame([{
                "公司名称": f"任务模块: {module_name}",
                "注册国家/城市": f"核心关键词: {keyword}",
                "业务负责人": f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "公开邮箱": "---",
                "公开电话": "---",
                "业务范围": "---",
                "来源URL": "---"
            }])
            final_df = pd.concat([metadata, df], ignore_index=True)
            final_df.to_csv(output_file, index=False, encoding='utf-8-sig')

        st.success("✨ 任务成功完成！")
        return True
    except Exception as e:
        st.error(f"❌ 运行出错: {str(e)}")
        return False

def run_batch_mode(module_choice, base_keyword, output_file, progress_bar):
    searcher = Searcher()
    processor = Processor()
    module_id = str(module_choice + 1)
    
    st.info(f"正在为模块 {module_id} 扩展查询关键词...")
    queries = searcher.expand_keywords(base_keyword, module_id)
    total = len(queries)
    
    for i, query in enumerate(queries):
        progress = (i + 1) / total
        progress_bar.progress(progress, text=f"进度 {i+1}/{total}: {query}")
        try:
            results = searcher._execute_search(query, num_results=20)
            if results and "organic" in results:
                processor.process_and_save(results, output_file=output_file)
            if i < total - 1: time.sleep(2)
        except Exception as e:
            st.error(f"批量模式错误 '{query}': {e}")
    return True

def load_progress_log():
    log_file = "progress_log.json"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def start_automation_thread(keyword, module_choice, output_file):
    module_id = str(module_choice + 1)
    manager = AutomationManager(output_file)
    stop_event = threading.Event()
    
    def target():
        try:
            manager.run_campaign(keyword, module_id, stop_event)
        except Exception as e:
            print(f"Thread Error: {e}")
        finally:
            st.session_state['job_status'] = 'done'
            
    t = threading.Thread(target=target)
    t.start()
    return t, stop_event

# ==============================================================================
# 5. MAIN UI LAYOUT
# ==============================================================================

# Header
st.markdown("""
    <div class="header-container">
        <h1 style='color: #FFD700; margin-bottom: 0;'>欢迎来到superlink数据库</h1>
        <p style='color: #FFD700; font-size: 1.1rem;'>专业的 B2B 商业线索挖掘工厂</p>
    </div>
""", unsafe_allow_html=True)

show_api_status_dashboard()

tab_run, tab_history, tab_settings = st.tabs(["🚀 启动引擎", "📂 线索库", "⚙️ 系统设置"])

# --- TAB 1: LAUNCH ENGINE ---
with tab_run:
    col_input, col_status = st.columns([1, 2])
    
    with col_input:
        st.markdown("### 🛠️ 任务配置")
        task_name = st.text_input("任务标识", value="search_leads", help="用于生成导出的文件名")
        module_options = [
            "1. 欧美物流商 (Logistics)",
            "2. 欧美进口商 (Importers)",
            "3. 中国货代同行 (CN Forwarders)",
            "4. 中国出口工厂 (CN Exporters)",
            "5. 批量模式 (多查询)",
            "6. 工厂模式 (全自动)"
        ]
        selected_option = st.selectbox("选择搜索策略", module_options)
        choice_idx = module_options.index(selected_option)
        
        keyword = st.text_input("目标关键词", placeholder="例如：家具, 电子产品, 纺织品")
        
        st.markdown("---")
        st.markdown("**🚀 性能增强模式**")
        use_enhanced = st.checkbox("开启增强搜索", value=False, help="使用异步搜索和智能关键词裂变，可挖掘出 5-10 倍以上的线索量。")
        
        batch_module_idx = 0
        if choice_idx >= 4:
            st.markdown("---")
            sub_options = ["物流商", "进口商", "货代同行", "出口工厂"]
            batch_sub_choice = st.selectbox("批量/工厂模式的基础逻辑", sub_options)
            batch_module_idx = sub_options.index(batch_sub_choice)

        st.markdown("<br>", unsafe_allow_html=True)
        start_btn = st.button("🚀 开始执行", type="primary", use_container_width=True)

    with col_status:
        st.markdown("### 📈 实时执行状态")
        if 'job_status' not in st.session_state: st.session_state['job_status'] = 'idle'

        if st.session_state['job_status'] == 'running':
            st.info("🔄 引擎正在后台按城市轮询执行...")
            progress_data = load_progress_log()
            completed = progress_data.get("completed_cities", [])
            
            m1, m2 = st.columns(2)
            m1.metric("已完成城市", len(completed))
            m2.metric("最后搜索城市", completed[-1] if completed else "无")
            
            if st.button("🛑 停止引擎", type="secondary"):
                if st.session_state.get('stop_event'): st.session_state['stop_event'].set()
                st.warning("正在初始化停止程序...")
                if st.session_state.get('automation_thread'): st.session_state['automation_thread'].join(timeout=5)
                st.session_state['job_status'] = 'idle'
                st.rerun()
            
            time.sleep(3)
            st.rerun()

        elif st.session_state['job_status'] == 'done':
            st.success("🏁 工厂模式任务已执行完毕！")
            if st.button("重置状态"):
                st.session_state['job_status'] = 'idle'
                st.rerun()
        
        elif st.session_state['job_status'] == 'idle':
            if start_btn:
                if not keyword:
                    st.error("请输入目标关键词。")
                else:
                    try:
                        output_file = get_output_filename(task_name, keyword, selected_option)
                        st.session_state['current_output_file'] = output_file
                        
                        success = False
                        if use_enhanced:
                            import asyncio
                            success = asyncio.run(run_enhanced_task(choice_idx, keyword, selected_option, output_file))
                        elif choice_idx < 4:
                            success = run_single_search(choice_idx, keyword, selected_option, output_file)
                        elif choice_idx == 4:
                            progress_bar = st.progress(0, text="正在初始化批量任务...")
                            success = run_batch_mode(batch_module_idx, keyword, output_file, progress_bar)
                            progress_bar.empty()
                        elif choice_idx == 5:
                            t, stop_event = start_automation_thread(keyword, batch_module_idx, output_file)
                            st.session_state['automation_thread'] = t
                            st.session_state['stop_event'] = stop_event
                            st.session_state['job_status'] = 'running'
                            st.rerun()
                            
                        if success:
                            st.balloons()
                            show_preview(output_file)
                    except Exception as e:
                        st.error(f"系统运行出错: {e}")
            else:
                st.caption("等待任务参数输入...")

# --- TAB 2: LEAD REPOSITORY ---
with tab_history:
    st.header("📂 线索库")
    history_files = list_history_files()
    if not history_files:
        st.info("目前还没有采集到任何线索。启动一个任务来生成 CSV 文件吧。")
    else:
        selected_file = st.selectbox("浏览历史记录", history_files, 
                                     format_func=lambda x: f"📁 {os.path.basename(x)} | {datetime.fromtimestamp(os.path.getmtime(x)).strftime('%Y-%m-%d %H:%M')}")
        if selected_file:
            st.markdown("---")
            show_preview(selected_file)
            if st.button("🗑️ 删除选中文件"):
                os.remove(selected_file)
                st.success("文件已成功删除。")
                st.rerun()

# --- TAB 3: SYSTEM SETTINGS ---
with tab_settings:
    st.header("⚙️ 配置管理")
    st.write("当前运行环境配置：")
    
    with st.expander("🔑 API 凭证"):
        st.info("这些密钥是从您的 .env 文件或云端配置中加载的。")
        st.text_input("Serper 搜索密钥", value=os.getenv("SERPER_API_KEY", "未设置"), type="password", disabled=True)
        st.text_input("智谱 AI 密钥", value=os.getenv("ZHIPUAI_API_KEY", "未设置"), type="password", disabled=True)
        
    with st.expander("🌐 代理设置"):
        st.write(f"是否启用代理: `{os.getenv('USE_PROXY', 'True')}`")
        st.write(f"代理地址: `{os.getenv('HTTP_PROXY', '未设置')}`")
        
    st.markdown("---")
    st.caption("v1.2.0 | SuperLink 数据引擎 | Robin (SuperLink 研发团队)")
