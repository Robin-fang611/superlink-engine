import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# ==============================================================================
# 1. CRITICAL INITIALIZATION SECTION (Proxy & Env)
# ==============================================================================
# Must be executed BEFORE any other imports that might use network connections.
load_dotenv()

PROXY_URL = "http://127.0.0.1:7897"
# Set proxies in environment variables
os.environ['HTTP_PROXY'] = PROXY_URL
os.environ['HTTPS_PROXY'] = PROXY_URL
os.environ['http_proxy'] = PROXY_URL
os.environ['https_proxy'] = PROXY_URL

print(f"[System] Environment initialized. Proxy set to {PROXY_URL}")

# ==============================================================================
# 2. MODULE IMPORTS
# ==============================================================================
from core.searcher import Searcher
from core.processor import Processor
from core.automation import AutomationManager

def get_output_filename():
    """
    Generate a unique filename with timestamp.
    Format: output/superlink_leads_YYYY.MM.DD.HH.MM.csv
    """
    now = datetime.now()
    # Format: 2026.01.18.13.49 (using dots as requested, but avoiding colon for Windows compatibility)
    timestamp = now.strftime("%Y.%m.%d.%H.%M") 
    return f"output/superlink_leads_{timestamp}.csv"

def run_batch_mode(module_choice, base_keyword, output_file):
    """
    Execute batch search with keyword expansion to get more results.
    """
    searcher = Searcher()
    processor = Processor()
    
    # Generate expanded queries
    queries = searcher.expand_keywords(base_keyword, module_choice)
    total_queries = len(queries)
    
    print(f"\n[Batch Mode] Generated {total_queries} expanded queries for '{base_keyword}'.")
    print(f"[Config] Results will be saved to: {output_file}")
    print("Estimated yield: ~200-300 raw results (before filtering).")
    print("==================================================")
    
    for i, query in enumerate(queries, 1):
        print(f"\n[Progress {i}/{total_queries}] Searching: {query}")
        
        # Execute search (default page 1)
        results = searcher._execute_search(query, num_results=20)
        
        if results and "organic" in results:
            count = len(results["organic"])
            print(f"  -> Found {count} raw results. Processing...")
            processor.process_and_save(results, output_file=output_file)
        else:
            print("  -> No results found or error occurred.")
            
        # Respect API limits
        if i < total_queries:
            print("  -> Cooling down (2s)...")
            time.sleep(2)
            
    print("\n==================================================")
    print("[Batch Mode] All tasks completed.")
    print(f"Check {output_file} for results.")
    print("==================================================")

def main():
    print("==================================================")
    print("       SuperLink Data Engine (Advanced Mode)")
    print("==================================================")
    print("Select a Search Module:")
    print("1. Logistics Provider (USA/Europe)")
    print("2. Importer (USA/Europe)")
    print("3. China Freight Forwarder")
    print("4. China Exporter")
    print("5. [NEW] Auto-Batch Mode (200+ leads/day)")
    print("0. Exit")
    
    choice = input("Enter choice (0-5): ").strip()
    
    if choice == '0':
        sys.exit()
    
    keyword = input("Enter product/industry keyword (e.g., 'furniture'): ").strip()
    
    # Generate timestamped filename for this run
    output_file = get_output_filename()

    if choice == '6':
        print("\n[Factory Config] Select target module for default keywords:")
        print("1. Logistics | 2. Importer | 3. CN Forwarder | 4. CN Exporter")
        sub_choice = input("Select module type (1-4) [Default 1]: ").strip() or '1'
        
        manager = AutomationManager(output_file)
        manager.run_campaign(keyword, sub_choice)
        return
    
    if choice == '5':
        # In batch mode, we need to know which module type to simulate
        print("\n[Batch Config] Which module logic to apply?")
        print("1. Logistics | 2. Importer | 3. CN Forwarder | 4. CN Exporter")
        sub_choice = input("Select module type (1-4): ").strip()
        
        if sub_choice not in ['1', '2', '3', '4']:
            print("Invalid sub-choice.")
            return
            
        run_batch_mode(sub_choice, keyword, output_file)
        return

    # Normal Single Mode
    try:
        searcher = Searcher()
        processor = Processor()
    except Exception as e:
        print(f"[Error] Initialization failed: {e}")
        return
    
    results = {}
    print(f"\n[Status] Starting Search (Target: {output_file})...")
    
    if choice == '1':
        results = searcher.search_logistics_usa_europe(keyword)
    elif choice == '2':
        results = searcher.search_importer_usa_europe(keyword)
    elif choice == '3':
        results = searcher.search_china_forwarder(keyword)
    elif choice == '4':
        results = searcher.search_china_exporter(keyword)
    else:
        print("Invalid selection.")
        return

    if not results:
        print("==================================================")
        print("[Status] Search returned no results.")
        print("建议操作：")
        print("1. 检查您的网络代理是否正常连接 (http://127.0.0.1:7897)。")
        print("2. 尝试更换更宽泛的关键词。")
        print("==================================================")
        return
        
    print("[Status] Search complete. Processing with AI...")
    processor.process_and_save(results, output_file=output_file)
    print(f"[Status] Process finished. Check {output_file}")

if __name__ == "__main__":
    main()
