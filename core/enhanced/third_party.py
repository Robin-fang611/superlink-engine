import requests
import os

class ApolloIO:
    """Apollo.io API 集成，用于获取公司决策人信息"""
    
    def __init__(self):
        self.api_key = os.getenv("APOLLO_API_KEY")
        self.base_url = "https://api.apollo.io/v1/people/search"
        
    def search_decision_makers(self, company_name, titles=None):
        """搜索公司的关键决策人"""
        if not self.api_key:
            return []
            
        if titles is None:
            titles = ["CEO", "Founder", "Purchasing Manager", "Procurement Manager", "Owner"]
            
        payload = {
            "api_key": self.api_key,
            "q_organization_name": company_name,
            "person_titles": titles,
            "page": 1,
            "display_mode": "regular"
        }
        
        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                people = data.get("people", [])
                results = []
                for p in people:
                    results.append({
                        "name": p.get("name"),
                        "position": p.get("title"),
                        "email": p.get("email"),
                        "linkedin": p.get("linkedin_url")
                    })
                return results
        except Exception as e:
            print(f"[ApolloIO Error] {e}")
        return []

class SnovIO:
    """Snov.io API 集成，用于领英邮箱挖掘"""
    
    def __init__(self):
        self.user_id = os.getenv("SNOVIO_USER_ID")
        self.api_secret = os.getenv("SNOVIO_API_SECRET")
        self.token = None

    def _get_token(self):
        """获取 OAuth2 Token"""
        if self.token:
            return self.token
            
        if not self.user_id or not self.api_secret:
            return None
            
        url = "https://api.snov.io/v1/get-user-api-token"
        payload = {
            "client_id": self.user_id,
            "client_secret": self.api_secret
        }
        try:
            # Snov.io API v1 token endpoint uses POST
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                return self.token
        except Exception as e:
            print(f"[SnovIO Token Error] {e}")
        return None

    def get_emails_by_domain(self, domain):
        """根据域名获取邮箱"""
        token = self._get_token()
        if not token:
            return []
            
        url = "https://api.snov.io/v2/domain-emails-with-info"
        params = {
            "access_token": token,
            "domain": domain,
            "type": "all",
            "limit": 10
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                emails_info = data.get("emails", [])
                return [e.get("email") for e in emails_info]
        except Exception as e:
            print(f"[SnovIO Error] {e}")
        return []
