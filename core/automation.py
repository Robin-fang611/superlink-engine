import json
import time
import random
import os
import threading
from datetime import datetime
from core.searcher import Searcher
from core.processor import Processor
from core.database import DatabaseHandler
from core.verifier import EmailVerifier
from core.email_sender import EmailSender

class AutomationManager:
    def __init__(self, output_file):
        self.output_file = output_file
        self.log_file = "progress_log.json"
        self.searcher = Searcher()
        self.processor = Processor()
        self.db = DatabaseHandler()
        self.email_sender = EmailSender()
        
        # 50+ Major Cities (USA & Europe)
        self.cities = [
            "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", 
            "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville", 
            "Seattle", "Denver", "Miami", "Atlanta", "Boston", "San Francisco", "Detroit",
            "London", "Berlin", "Madrid", "Rome", "Paris", "Hamburg", "Vienna", "Warsaw", 
            "Brussels", "Amsterdam", "Rotterdam", "Antwerp", "Felixstowe", "Le Havre"
        ]

    def run_full_pipeline(self, base_keyword, module_choice='1', auto_send=False, stop_event=None):
        """
        全流程自动化：搜索 -> AI处理 -> 验证 -> 自动发送
        """
        os.makedirs("output", exist_ok=True)
        print(f"\n[Ultra Pipeline] Starting for keyword: {base_keyword}")
        
        # 1. 搜索与初步提取 (使用现有的 run_campaign 逻辑，但进行拦截)
        self.run_campaign(base_keyword, module_choice, stop_event)
        
        # 2. 验证新提取的线索
        # 从刚刚生成的 CSV 中读取新数据
        import pandas as pd
        if os.path.exists(self.output_file):
            try:
                df = pd.read_csv(self.output_file)
                # 剔除元数据行
                if not df.empty and df.iloc[0]['公司名称'].startswith('任务模块'):
                    df = df.iloc[1:]
                
                new_leads = df.to_dict('records')
                print(f"[Pipeline] Validating {len(new_leads)} leads...")
                
                for lead in new_leads:
                    if stop_event and stop_event.is_set(): break
                    
                    email = lead.get('公开邮箱')
                    if email and email not in ["n/a", "none", ""]:
                        # 执行三阶段验证
                        is_valid, reason = EmailVerifier.verify(email)
                        lead['status'] = 'valid' if is_valid else 'invalid'
                        lead['details'] = reason
                        
                        # 存入数据库
                        self.db.add_verified_lead(lead)
                        
                        # 3. 自动发送邮件 (如果开启)
                        if auto_send and is_valid:
                            print(f"  -> Sending outreach to: {email}")
                            success, msg = self.email_sender.send_email(
                                to_email=email,
                                subject=f"Partnership Opportunity for {lead.get('公司名称')}",
                                template_name="b2b_outreach.html",
                                context={
                                    "company_name": lead.get("公司名称"),
                                    "contact_person": lead.get("业务负责人") or "Partner",
                                    "business_scope": lead.get("业务范围")
                                }
                            )
                            # 记录发送状态
                            self.db.log_email_sent(None, email, "Partnership", "b2b_outreach.html", 
                                                 'sent' if success else 'failed', msg)
                            time.sleep(random.uniform(2, 5))
            except Exception as e:
                print(f"[Pipeline Error] {e}")

    def _load_progress(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {"completed_cities": []}
        return {"completed_cities": []}

    def _save_progress(self, city):
        try:
            # Ensure directory exists just in case
            log_dir = os.path.dirname(self.log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
                
            data = self._load_progress()
            if city not in data["completed_cities"]:
                data["completed_cities"].append(city)
                # Use atomic write pattern to prevent corruption
                temp_file = self.log_file + ".tmp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(temp_file, self.log_file)
        except Exception as e:
            print(f"[Warning] Failed to save progress log: {e}")

    def run_campaign(self, base_keyword, module_choice='1', stop_event=None):
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        # 1. Default Keyword Logic
        if not base_keyword:
            defaults = {
                '1': "International Freight Forwarder", # Logistics
                '2': "Importer Distributor",            # Importer
                '3': "China Freight Forwarder",         # CN Forwarder
                '4': "China Manufacturer Exporter"      # CN Exporter
            }
            base_keyword = defaults.get(module_choice, "International Trade")
            print(f"[Auto-Fill] No keyword provided. Using default: '{base_keyword}'")

        print(f"\n[Factory Mode] Starting automation for keyword: {base_keyword}")
        print(f"[Target] {len(self.cities)} Cities | 3 Pages/City")
        print(f"[Output] {self.output_file}")
        
        progress = self._load_progress()
        completed_cities = set(progress.get("completed_cities", []))
        
        total_cities = len(self.cities)
        
        try:
            for i, city in enumerate(self.cities, 1):
                # Check for stop signal
                if stop_event and stop_event.is_set():
                    print("\n[System] 🛑 Task stopped by user request.")
                    break

                if city in completed_cities:
                    print(f"[Skip] City {city} already completed.")
                    continue
                    
                print(f"\n[Progress] Processing City {i}/{total_cities}: {city}")
                
                # Search Pages 1-3
                for page in range(1, 4):
                    # Check for stop signal inside page loop too
                    if stop_event and stop_event.is_set():
                        break

                    try:
                        # Construct Query based on module logic
                        # We can use Searcher's logic or just append city
                        # For simplicity and robustness in Factory Mode, we append City to base_keyword
                        # But better to respect module nuances if possible. 
                        # Let's keep it simple: Keyword + City + Contact intent
                        query = f"{base_keyword} {city} contact email"
                        
                        print(f"  -> Fetching Page {page}: {query}")
                        
                        # Execute Search
                        results = self.searcher._execute_search(query, num_results=20, page=page)
                        
                        # Process & Save Immediately
                        if results and "organic" in results:
                            count = len(results["organic"])
                            print(f"    -> Found {count} results. Extracting...")
                            self.processor.process_and_save(results, self.output_file)
                        else:
                            print(f"    -> No results on page {page}.")
                        
                        # Rate Limiting (Page Interval)
                        sleep_time = random.uniform(3, 5)
                        print(f"    -> Sleeping {sleep_time:.1f}s...")
                        time.sleep(sleep_time)
                        
                    except Exception as e:
                        print(f"[Error] Failed processing {city} Page {page}: {e}")
                        # Continue to next page/city, do not crash
                        continue
                
                # Mark City Complete
                if not (stop_event and stop_event.is_set()):
                    self._save_progress(city)
                    print(f"[Done] City {city} completed. Saved to log.")
                    
                    # Rate Limiting (City Interval)
                    sleep_time = random.uniform(10, 15)
                    print(f"[Cooldown] Waiting {sleep_time:.1f}s before next city...\n")
                    time.sleep(sleep_time)
                else:
                    break

        except KeyboardInterrupt:
            print("\n\n==================================================")
            print("[System] 🛑 用户手动停止任务 (Ctrl+C)")
            print(f"[System] 当前进度已保存至 {self.log_file}")
            print(f"[System] 数据已安全保存至 {self.output_file}")
            print("==================================================")
            return

        print("\n==================================================")
        if stop_event and stop_event.is_set():
            print("[Factory Mode] Task stopped by user.")
        else:
            print("[Factory Mode] All cities processed.")
        print("==================================================")
