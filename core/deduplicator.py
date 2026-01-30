import os
import json

class Deduplicator:
    def __init__(self, history_file="output/history_log.json"):
        self.history_file = history_file
        self.seen_urls = set()
        self.seen_companies = set()
        self.seen_emails = set()
        self.seen_phones = set()
        self._load_history()

    def _load_history(self):
        """Load existing history to prevent duplicates across runs."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.seen_urls = set(data.get("urls", []))
                    self.seen_companies = set(data.get("companies", []))
                    self.seen_emails = set(data.get("emails", []))
                    self.seen_phones = set(data.get("phones", []))
                print(f"[System] Loaded history: {len(self.seen_companies)} companies, {len(self.seen_emails)} emails.")
            except Exception as e:
                print(f"[Warning] Failed to load history: {e}")
        else:
            print("[System] No history log found. Starting fresh deduplication.")

    def is_duplicate(self, item):
        """
        Check if item exists in history.
        Logic Update: 
        - If we have seen the URL or Company Name, it's a duplicate.
        - If we have seen the Public Email or Phone, it's also a duplicate (avoid spamming same contact).
        """
        # Safe string conversion to avoid NoneType error
        url = str(item.get("来源URL") or "").strip().lower()
        name = str(item.get("公司名称") or "").strip().lower()
        email = str(item.get("公开邮箱") or "").strip().lower()
        phone = str(item.get("公开电话") or "").strip().lower()
        
        # Check basic identity
        if url and url in self.seen_urls:
            return True
        if name and name in self.seen_companies:
            return True
            
        # Check contact info uniqueness
        # We only check if the email/phone is valid (not "n/a" or empty)
        if email and email not in ["n/a", "none", ""] and email in self.seen_emails:
            return True
        if phone and phone not in ["n/a", "none", ""] and phone in self.seen_phones:
            return True
            
        return False

    def filter_unique(self, data_list):
        """
        Helper method to filter a list of items and return only unique ones.
        Updates the internal state with new items.
        """
        unique_data = []
        for item in data_list:
            if not self.is_duplicate(item):
                unique_data.append(item)
                self.add(item)
        
        if unique_data:
            self.save()
        return unique_data

    def add(self, item):
        """Add new item to history memory."""
        # Safe string conversion
        url = str(item.get("来源URL") or "").strip().lower()
        name = str(item.get("公司名称") or "").strip().lower()
        email = str(item.get("公开邮箱") or "").strip().lower()
        phone = str(item.get("公开电话") or "").strip().lower()
        
        if url:
            self.seen_urls.add(url)
        if name:
            self.seen_companies.add(name)
        if email and email not in ["n/a", "none", ""]:
            self.seen_emails.add(email)
        if phone and phone not in ["n/a", "none", ""]:
            self.seen_phones.add(phone)

    def save(self):
        """Persist history to disk."""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "urls": list(self.seen_urls),
                    "companies": list(self.seen_companies),
                    "emails": list(self.seen_emails),
                    "phones": list(self.seen_phones)
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Error] Failed to save history: {e}")
