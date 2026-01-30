import json
import time
import random
import os
from datetime import datetime
from core.searcher import Searcher
from core.processor import Processor

class AutomationManager:
    def __init__(self, output_file):
        self.output_file = output_file
        self.log_file = "progress_log.json"
        self.searcher = Searcher()
        self.processor = Processor()
        
        # 50+ Major Cities (USA & Europe)
        self.cities = [
            # USA
            "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", 
            "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville", 
            "Fort Worth", "Columbus", "San Francisco", "Charlotte", "Indianapolis", "Seattle", 
            "Denver", "Washington", "Boston", "El Paso", "Nashville", "Detroit", "Portland", 
            "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee", "Albuquerque", 
            "Tucson", "Fresno", "Sacramento", "Atlanta", "Kansas City", "Miami", "Raleigh",
            # Europe
            "London", "Berlin", "Madrid", "Rome", "Paris", "Hamburg", "Vienna", "Warsaw", 
            "Bucharest", "Budapest", "Barcelona", "Munich", "Milan", "Prague", "Sofia", 
            "Brussels", "Amsterdam", "Rotterdam", "Antwerp", "Felixstowe", "Le Havre", 
            "Valencia", "Genoa", "Piraeus"
        ]

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
