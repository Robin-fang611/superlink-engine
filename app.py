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
            background-color: #f8f9fa;
        }
        
        /* Card-like containers */
        div.stButton > button:first-child {
            background-color: #007bff;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            border: none;
            transition: all 0.3s ease;
        }
        
        div.stButton > button:hover {
            background-color: #0056b3;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Sidebar styling */
        .sidebar .sidebar-content {
            background-image: linear-gradient(#2e7bcf,#2e7bcf);
            color: white;
        }
        
        /* Metric styling */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            color: #007bff;
        }
        
        /* Custom Header */
        .header-container {
            padding: 1.5rem;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
            text-align: center;
        }
        
        /* Dataframe styling */
        .stDataFrame {
            border: 1px solid #e9ecef;
            border-radius: 8px;
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
        st.markdown('<div class="header-container"><h1>🔒 Access Restricted</h1><p>Please enter the engine password to continue.</p></div>', unsafe_allow_html=True)
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    return True

# Page Config
st.set_page_config(
    page_title="SuperLink Data Engine",
    page_icon="🚀",
    layout="wide"
)

apply_custom_styles()

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

def get_output_filename(task_name):
    now = datetime.now()
    timestamp = now.strftime("%Y.%m.%d.%H.%M")
    safe_task_name = "".join([c for c in task_name if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
    if not safe_task_name:
        safe_task_name = "task"
    return f"output/{safe_task_name}_{timestamp}.csv"

def show_preview(file_path):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            st.success(f"✅ Data Loaded: `{os.path.basename(file_path)}`")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                with open(file_path, "rb") as f:
                    st.download_button(
                        label="📥 Download CSV",
                        data=f,
                        file_name=os.path.basename(file_path),
                        mime="text/csv",
                    )
            with col2:
                st.caption(f"Total Rows Found: **{len(df)}**")
            
            st.dataframe(df.head(100), use_container_width=True)
        except Exception as e:
            st.warning(f"Preview Error: {e}")
    else:
        st.info("No data file available.")

def list_history_files():
    files = glob.glob("output/*.csv")
    files.sort(key=os.path.getmtime, reverse=True)
    return files

# ==============================================================================
# 3. DASHBOARD COMPONENTS
# ==============================================================================

async def run_enhanced_task(module_idx, keyword, output_file):
    """Execute task using the new Enhanced engine (Async + AI Batching)."""
    expander = KeywordExpander()
    searcher = AsyncSearcher(concurrency=3) # Safe for cheap proxy
    processor = EnhancedProcessor()
    
    st.info("🔍 Expanding keywords for maximum coverage...")
    module_id = str(module_idx + 1)
    # Expand for major regions
    expanded_queries = expander.expand(keyword, module_id)
    # Limit for performance mode demo (can be increased)
    target_queries = expanded_queries[:5] 
    
    st.info(f"🚀 Launching Parallel Search for {len(target_queries)} queries...")
    raw_results = await searcher.search_batch(target_queries, pages_per_query=2)
    
    if not raw_results:
        st.warning("No results found in enhanced mode.")
        return False
        
    st.info(f"🧠 AI Processing {len(raw_results)} results in batches...")
    all_leads = processor.process_batch_enhanced(raw_results, batch_size=10)
    
    if all_leads:
        # Save results
        from core.deduplicator import Deduplicator
        dedup = Deduplicator()
        unique_leads = dedup.filter_unique(all_leads)
        
        # Save to CSV using the existing logic
        df = pd.DataFrame(unique_leads)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        st.success(f"✨ Enhanced Task Complete! Found {len(unique_leads)} unique leads.")
        return True
    return False

def show_api_status_dashboard():
    with st.sidebar:
        st.markdown("### 📊 System Dashboard")
        status = st.session_state.get('api_status', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Serper API**")
            st.markdown("🟢 OK" if status.get("serper") else "🔴 Missing")
        with col2:
            st.markdown(f"**Zhipu AI**")
            st.markdown("🟢 OK" if status.get("zhipu") else "🔴 Missing")
            
        st.markdown("---")
        st.markdown("### 🛠️ Runtime Info")
        st.caption(f"Working Dir: `{os.getcwd()}`")
        st.caption(f"Server Port: `3000` (Mapped)")

# ==============================================================================
# 4. CORE LOGIC ADAPTERS
# ==============================================================================

def run_single_search(choice_idx, keyword, output_file):
    searcher = Searcher()
    processor = Processor()
    
    status_container = st.container()
    with status_container:
        st.info("🚀 Starting Search Engine...")
        
    try:
        if choice_idx == 0: results = searcher.search_logistics_usa_europe(keyword)
        elif choice_idx == 1: results = searcher.search_importer_usa_europe(keyword)
        elif choice_idx == 2: results = searcher.search_china_forwarder(keyword)
        elif choice_idx == 3: results = searcher.search_china_exporter(keyword)
        else: results = {}
            
        if not results:
            st.warning("⚠️ No results found. Check keywords or proxy settings.")
            return False

        st.info("🧠 AI Analysis in progress...")
        processor.process_and_save(results, output_file=output_file)
        st.success("✨ Task Completed Successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Execution Error: {str(e)}")
        return False

def run_batch_mode(module_choice, base_keyword, output_file, progress_bar):
    searcher = Searcher()
    processor = Processor()
    module_id = str(module_choice + 1)
    
    st.info(f"Expanding queries for module {module_id}...")
    queries = searcher.expand_keywords(base_keyword, module_id)
    total = len(queries)
    
    for i, query in enumerate(queries):
        progress = (i + 1) / total
        progress_bar.progress(progress, text=f"Query {i+1}/{total}: {query}")
        try:
            results = searcher._execute_search(query, num_results=20)
            if results and "organic" in results:
                processor.process_and_save(results, output_file=output_file)
            if i < total - 1: time.sleep(2)
        except Exception as e:
            st.error(f"Batch Error on '{query}': {e}")
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
        <h1 style='color: #007bff; margin-bottom: 0;'>🕸️ SuperLink Data Engine</h1>
        <p style='color: #6c757d; font-size: 1.1rem;'>Professional B2B Lead Generation Factory</p>
    </div>
""", unsafe_allow_html=True)

show_api_status_dashboard()

tab_run, tab_history, tab_settings = st.tabs(["🚀 Launch Engine", "📂 Lead Repository", "⚙️ System Settings"])

# --- TAB 1: LAUNCH ENGINE ---
with tab_run:
    col_input, col_status = st.columns([1, 2])
    
    with col_input:
        st.markdown("### 🛠️ Task Configuration")
        task_name = st.text_input("Task Identifier", value="search_leads", help="Used for file naming")
        module_options = [
            "1. Logistics (USA/EU)",
            "2. Importers (USA/EU)",
            "3. CN Forwarders",
            "4. CN Exporters",
            "5. Batch (Multi-Query)",
            "6. Factory (Full Auto)"
        ]
        selected_option = st.selectbox("Select Strategy", module_options)
        choice_idx = module_options.index(selected_option)
        
        keyword = st.text_input("Target Keyword", placeholder="e.g. furniture, electronics")
        
        st.markdown("---")
        st.markdown("**🚀 Performance Mode**")
        use_enhanced = st.checkbox("Enable Enhanced Search", value=False, help="Uses async searching and intelligent keyword expansion to find 5x more leads.")
        
        batch_module_idx = 0
        if choice_idx >= 4:
            st.markdown("---")
            sub_options = ["Logistics", "Importers", "CN Forwarders", "CN Exporters"]
            batch_sub_choice = st.selectbox("Base Logic for Batch/Factory", sub_options)
            batch_module_idx = sub_options.index(batch_sub_choice)

        st.markdown("<br>", unsafe_allow_html=True)
        start_btn = st.button("🚀 Start Engine", type="primary", use_container_width=True)

    with col_status:
        st.markdown("### 📈 Live Execution Status")
        if 'job_status' not in st.session_state: st.session_state['job_status'] = 'idle'

        if st.session_state['job_status'] == 'running':
            st.info("🔄 Engine is running in background city-by-city...")
            progress_data = load_progress_log()
            completed = progress_data.get("completed_cities", [])
            
            m1, m2 = st.columns(2)
            m1.metric("Cities Completed", len(completed))
            m2.metric("Last Found", completed[-1] if completed else "None")
            
            if st.button("🛑 STOP ENGINE", type="secondary"):
                if st.session_state.get('stop_event'): st.session_state['stop_event'].set()
                st.warning("Stopping sequence initiated...")
                if st.session_state.get('automation_thread'): st.session_state['automation_thread'].join(timeout=5)
                st.session_state['job_status'] = 'idle'
                st.rerun()
            
            time.sleep(3)
            st.rerun()

        elif st.session_state['job_status'] == 'done':
            st.success("🏁 Factory Mode Task Finished!")
            if st.button("Reset Status"):
                st.session_state['job_status'] = 'idle'
                st.rerun()
        
        elif st.session_state['job_status'] == 'idle':
            if start_btn:
                if not keyword:
                    st.error("Missing target keyword.")
                else:
                    try:
                        output_file = get_output_filename(task_name)
                        st.session_state['current_output_file'] = output_file
                        
                        success = False
                        if use_enhanced:
                            import asyncio
                            success = asyncio.run(run_enhanced_task(choice_idx, keyword, output_file))
                        elif choice_idx < 4:
                            success = run_single_search(choice_idx, keyword, output_file)
                        elif choice_idx == 4:
                            progress_bar = st.progress(0, text="Initializing Batch...")
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
                        st.error(f"System Error: {e}")
            else:
                st.caption("Waiting for mission parameters...")

# --- TAB 2: LEAD REPOSITORY ---
with tab_history:
    st.header("📂 Lead Repository")
    history_files = list_history_files()
    if not history_files:
        st.info("No leads collected yet. Start a task to generate CSV files.")
    else:
        selected_file = st.selectbox("Browse History", history_files, 
                                     format_func=lambda x: f"📁 {os.path.basename(x)} | {datetime.fromtimestamp(os.path.getmtime(x)).strftime('%Y-%m-%d %H:%M')}")
        if selected_file:
            st.markdown("---")
            show_preview(selected_file)
            if st.button("🗑️ Delete Selected File"):
                os.remove(selected_file)
                st.success("File deleted.")
                st.rerun()

# --- TAB 3: SYSTEM SETTINGS ---
with tab_settings:
    st.header("⚙️ Configuration Management")
    st.write("Current Environment Configuration:")
    
    with st.expander("🔑 API Credentials"):
        st.info("These keys are loaded from your `.env` file.")
        st.text_input("Serper API Key", value=os.getenv("SERPER_API_KEY", "Not Set"), type="password", disabled=True)
        st.text_input("Zhipu AI Key", value=os.getenv("ZHIPUAI_API_KEY", "Not Set"), type="password", disabled=True)
        
    with st.expander("🌐 Proxy Settings"):
        st.write(f"Proxy Enabled: `{os.getenv('USE_PROXY', 'True')}`")
        st.write(f"Proxy URL: `{os.getenv('HTTP_PROXY', 'Not Set')}`")
        
    st.markdown("---")
    st.caption("v1.2.0 | SuperLink Data Engine | Robin")
