import json
import csv
import os
import traceback
from core.deduplicator import Deduplicator

try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

class Processor:
    def __init__(self):
        self.models_config = self._load_models_config()
        # Default to glm47
        self.default_model_key = self.models_config.get("default_model", "glm47")
        
        self.active_config = self.models_config.get(self.default_model_key, {})
        self.provider = self.active_config.get("provider", "zhipuai")
        self.model_name = self.active_config.get("model_name", "glm-4")
        
        self.api_key = None
        self.client = None
        
        # Initialize Deduplicator
        self.deduplicator = Deduplicator()
        
        # Configure client
        self._configure_client()

    def _load_models_config(self):
        try:
            with open(".models.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Error] Loading .models.json failed: {e}")
            return {}

    def _configure_client(self):
        # Support both standard env and streamlit secrets
        api_key_env = self.active_config.get("api_key_env", "ZHIPUAI_API_KEY")
        self.api_key = os.getenv(api_key_env)
        
        # Fallback to Streamlit secrets if available
        if not self.api_key:
            try:
                import streamlit as st
                self.api_key = st.secrets.get(api_key_env)
            except:
                pass
        
        if not self.api_key:
            print(f"[Warning] {api_key_env} not found. Please provide it in .env or Secrets.")
            return

        if self.provider == "zhipuai":
            if ZhipuAI is None:
                print("[Error] 'zhipuai' library not installed. Please run: pip install zhipuai")
                return
            try:
                # STRATEGY: Temporarily unset proxy environment variables during ZhipuAI initialization
                proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
                saved_proxies = {}
                
                # 1. Save and Unset
                for var in proxy_vars:
                    if var in os.environ:
                        saved_proxies[var] = os.environ[var]
                        del os.environ[var]
                
                # 2. Initialize ZhipuAI (Clean, no extra args)
                self.client = ZhipuAI(api_key=self.api_key)
                print(f"[Processor] Initialized ZhipuAI ({self.model_name}) - Direct Connection (Env Proxy Disabled)")
                
                # 3. Restore
                for var, value in saved_proxies.items():
                    os.environ[var] = value
                    
            except Exception as e:
                print(f"[Error] ZhipuAI initialization failed: {e}")
                for var, value in saved_proxies.items():
                    os.environ[var] = value
        else:
            print(f"[Warning] Unknown provider '{self.provider}' (Only 'zhipuai' is supported in this version)")

    def process_and_save(self, search_results, output_file=None, task_name="default"):
        """
        Process search results with AI and save to CSV.
        If output_file is not provided, it generates one based on task_name and timestamp.
        """
        if not output_file:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y.%m.%d.%H.%M")
            # Sanitize task_name to be filename safe
            safe_task_name = "".join([c for c in task_name if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
            output_file = f"output/{safe_task_name}_{timestamp}.csv"

        self._ensure_csv_headers(output_file)

        if not search_results or "organic" not in search_results:
            print("[Info] No organic search results found.")
            return

        organic_results = search_results["organic"]
        if not organic_results:
            print("[Info] Organic results list is empty.")
            return
            
        print(f"DEBUG: Received {len(organic_results)} search results")

        # Prepare context
        context_text = ""
        for item in organic_results:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            context_text += f"Title: {title}\nLink: {link}\nDescription: {snippet}\n\n"

        # AI Processing
        extracted_data = self._ai_extract(context_text)
        
        if extracted_data:
            # DEDUPLICATION LOGIC
            unique_data = []
            duplicate_count = 0
            
            for item in extracted_data:
                # Sanitize item values to strings to prevent NoneType errors in later processing
                # Also ensures empty fields are handled as empty strings
                for k, v in item.items():
                    # Robust string conversion and stripping as requested
                    val = v if v is not None else ""
                    item[k] = str(val).strip()

                if self.deduplicator.is_duplicate(item):
                    duplicate_count += 1
                else:
                    unique_data.append(item)
                    self.deduplicator.add(item)
            
            # Save new history
            self.deduplicator.save()
            
            if duplicate_count > 0:
                print(f"[Deduplication] Filtered out {duplicate_count} duplicates.")
            
            if unique_data:
                self._save_to_csv(unique_data, output_file)
            else:
                print("[Info] All extracted leads were duplicates. No new data saved.")
        else:
            print("[Info] No valid data extracted (or all filtered out).")

    def _ai_extract(self, context_text):
        """
        Call AI to extract and filter data.
        """
        system_instruction = (
            "You are a Strict Data Auditor. Your goal is to extract high-quality SME business leads from search results.\n\n"
            "*** HARD FILTERING RULES (NON-NEGOTIABLE) ***\n"
            "1. REVENUE CAP: STRICTLY EXCLUDE any company with annual revenue > $100 Million USD.\n"
            "2. NO GIANTS: DIRECTLY REJECT large multinational corporations (e.g., DHL, FedEx, DB Schenker, Maersk, Amazon, Walmart, etc.). "
            "   If the description implies massive global scale (e.g., 'global leader', 'billions in assets'), DISCARD IT.\n"
            "3. NO IRRELEVANT SITES: Exclude news, government (.gov), wikipedia, directories (Yelp, YellowPages), or job boards.\n\n"
            "*** EXTRACTION SCHEMA ***\n"
            "For each valid SME, extract exactly these fields (use the Chinese keys provided):\n"
            "- 公司名称 (Company Name)\n"
            "- 注册国家/城市 (Registration Country/City)\n"
            "- 业务负责人 (Key Contact Person, if found)\n"
            "- 公开电话 (Public Phone)\n"
            "- 公开邮箱 (Public Email)\n"
            "- 业务范围 (Business Scope - specific products/services)\n"
            "- 来源URL (Source URL)\n\n"
            "Output Format: Return ONLY a valid JSON list of objects. No markdown, no explanations."
        )

        prompt = (
            f"{system_instruction}\n\n"
            "*** SEARCH RESULTS TO AUDIT ***\n"
            f"{context_text}\n\n"
            "*** JSON OUTPUT ***"
        )

        try:
            if self.provider == "zhipuai":
                return self._call_zhipuai(prompt)
            else:
                print("[Error] Only ZhipuAI is configured.")
                return []
        except Exception as e:
            print(f"[Error] AI Processing failed: {e}")
            traceback.print_exc()
            return []

    def _call_zhipuai(self, prompt):
        if not self.client:
            print("[Error] ZhipuAI client not initialized.")
            return []
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            return self._clean_json(response.choices[0].message.content)
        except Exception as e:
            print(f"[Error] ZhipuAI API Call Failed: {e}")
            print(f"[Debug] Raw Error Details: {str(e)}") 
            raise e

    def _clean_json(self, text_result):
        if not text_result:
            return []
        
        text_result = text_result.strip()
        
        # Remove Markdown code blocks if present
        if "```json" in text_result:
            text_result = text_result.split("```json")[1].split("```")[0].strip()
        elif "```" in text_result:
            text_result = text_result.split("```")[1].split("```")[0].strip()
        
        # Basic cleanup of AI chatter before/after JSON
        if not (text_result.startswith('[') or text_result.startswith('{')):
            # Try to find the first [ and last ]
            start_idx = text_result.find('[')
            end_idx = text_result.rfind(']')
            if start_idx != -1 and end_idx != -1:
                text_result = text_result[start_idx:end_idx+1]

        try:
            data = json.loads(text_result)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError as e:
            print(f"[Error] Failed to parse JSON response: {e}")
            # Fallback: simple regex or string manipulation could go here, 
            # but for now we'll just log and return empty
            print(f"Problematic Text: {text_result[:200]}...")
            return []

    def _get_headers(self):
        return ["公司名称", "注册国家/城市", "业务负责人", "公开电话", "公开邮箱", "业务范围", "来源URL"]

    def _ensure_csv_headers(self, filename):
        headers = self._get_headers()
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            if not os.path.isfile(filename):
                with open(filename, mode='w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                print(f"[Info] Created output file with headers: {filename}")
        except Exception as e:
            print(f"[Error] Failed to initialize CSV file: {e}")

    def _save_to_csv(self, data, filename):
        if not data:
            return

        headers = self._get_headers()
        try:
            file_exists = os.path.isfile(filename)
            with open(filename, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                if not file_exists:
                    writer.writeheader()
                
                for row in data:
                    clean_row = {k: row.get(k, "N/A") for k in headers}
                    writer.writerow(clean_row)
                
                # Force immediate write to disk
                f.flush()
                os.fsync(f.fileno())
            
            print(f"[Success] Appended {len(data)} leads to {filename}")
        except Exception as e:
            print(f"[Error] Saving CSV failed: {e}")
