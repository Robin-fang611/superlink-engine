import requests
import json
import os
from core.config import SERPER_API_KEY

class Searcher:
    def __init__(self):
        self.api_key = SERPER_API_KEY
        self.base_url = "https://google.serper.dev/search"
        self.headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

    def _execute_search(self, query, num_results=20, page=1):
        """
        Internal method to execute search against Serper API.
        Explicitly uses environment proxy settings.
        Supports pagination.
        """
        payload = json.dumps({
            "q": query,
            "num": num_results,
            "page": page
        })
        
        # Ensure proxies are picked up from env (redundant but safe)
        proxies = {
            "http": os.environ.get("HTTP_PROXY"),
            "https": os.environ.get("HTTPS_PROXY")
        }
        
        try:
            # Explicitly pass proxies to requests, though it usually auto-detects from env
            response = requests.post(
                self.base_url, 
                headers=self.headers, 
                data=payload,
                proxies=proxies
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[Error] Search failed: {e}")
            return {}

    def search_deep_contacts(self, domain, contact_keywords=None):
        """
        使用高级搜索指令挖掘特定域名的深度联系方式。
        """
        contact_keywords = contact_keywords or ["buyer", "procurement", "manager", "logistics"]
        queries = [
            f"site:{domain} \"@\"",
            f"\"@{domain}\" {' OR '.join(contact_keywords)}",
            f"site:{domain} contact us email",
            f"\"{domain}\" filetype:pdf contact"
        ]
        
        all_organic = []
        for q in queries:
            print(f"[DeepSearch] Targeting domain: {domain} with query: {q}")
            res = self._execute_search(q, num_results=10)
            if res and "organic" in res:
                all_organic.extend(res["organic"])
        
        return {"organic": all_organic}

    def expand_keywords(self, base_keyword, module_type):
        """
        Generate a list of specific queries to maximize coverage (Batch Mode).
        Uses geographic and category modifiers to split one broad keyword into many specific searches.
        """
        queries = []
        
        # Geographic modifiers for Western markets
        geo_locations = ["New York", "Los Angeles", "Chicago", "Houston", "Miami", "London", "Hamburg", "Rotterdam", "Toronto", "Dubai"]
        
        # Geographic modifiers for China
        china_locations = ["Shenzhen", "Shanghai", "Ningbo", "Qingdao", "Guangzhou", "Xiamen", "Tianjin", "Beijing"]

        if module_type == '1': # Logistics USA/Europe
            # Split by major logistics hubs and specific service types
            modifiers = geo_locations + ["Air Freight", "Ocean Freight", "Customs Broker", "Warehousing", "Supply Chain"]
            for mod in modifiers:
                queries.append(f"{base_keyword} International Freight Forwarder {mod} contact email -China")
                
        elif module_type == '2': # Importer USA/Europe
            # Split by major consumption hubs and business roles
            modifiers = geo_locations + ["Distributor", "Wholesaler", "Dealer", "Supplier", "Buyer"]
            for mod in modifiers:
                queries.append(f"{base_keyword} {mod} USA Europe contact email")
                
        elif module_type == '3': # China Forwarder
            # Split by major Chinese ports and service types
            modifiers = china_locations + ["Air Cargo", "Sea Shipping", "FBA", "Rail Freight"]
            for mod in modifiers:
                queries.append(f"{base_keyword} International Freight Forwarder {mod} Logistics Agent")
                
        elif module_type == '4': # China Exporter
            # Split by major manufacturing hubs and factory types
            modifiers = china_locations + ["OEM Factory", "Manufacturer", "Supplier", "Exporter"]
            for mod in modifiers:
                queries.append(f"{base_keyword} {mod} China contact email")
        
        return queries

    def search_logistics_usa_europe(self, keyword, page=1):
        """ Module 1: Logistics Provider (USA/Europe) """
        query = f"{keyword} International Freight Forwarder Logistics Company USA Europe contact email -China"
        print(f"[Search] Executing Module 1 (Page {page}): {query}")
        return self._execute_search(query, page=page)

    def search_importer_usa_europe(self, keyword, page=1):
        """ Module 2: Importer (USA/Europe) """
        query = f"{keyword} Importer Distributor Wholesaler USA Europe contact email"
        print(f"[Search] Executing Module 2 (Page {page}): {query}")
        return self._execute_search(query, page=page)

    def search_china_forwarder(self, keyword, page=1):
        """ Module 3: China Freight Forwarder """
        query = f"{keyword} International Freight Forwarder China Logistics Agent contact email"
        print(f"[Search] Executing Module 3 (Page {page}): {query}")
        return self._execute_search(query, page=page)

    def search_china_exporter(self, keyword, page=1):
        """ Module 4: China Exporter """
        query = f"{keyword} Manufacturer Exporter Factory China contact email"
        print(f"[Search] Executing Module 4 (Page {page}): {query}")
        return self._execute_search(query, page=page)
