import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import base64
import codecs

class EmailExtractor:
    """官网邮箱静态提取器，支持多页面扫描与编码解码"""
    
    def __init__(self):
        # 邮箱正则表达式
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        # 高概率包含邮箱的页面路径
        self.target_paths = [
            "/contact", "/about", "/team", "/management", "/contact-us", 
            "/about-us", "/our-team", "/legal", "/privacy-policy"
        ]

    def extract_from_website(self, base_url):
        """
        抓取目标网站及其核心子页面并提取邮箱。
        """
        if not base_url or not base_url.startswith("http"):
            return []
            
        emails = set()
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
        
        # 1. 抓取首页
        print(f"[Extractor] Scanning homepage: {base_url}")
        emails.update(self._scrape_page(base_url))
        
        # 2. 抓取核心子页面 (最多并发抓取，此处为简化采用顺序抓取)
        for path in self.target_paths:
            full_url = urljoin(base_domain, path)
            print(f"[Extractor] Scanning sub-page: {full_url}")
            emails.update(self._scrape_page(full_url))
            
        return list(emails)

    def _scrape_page(self, url):
        found = set()
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            # 使用现有代理设置（如有）
            proxies = {
                "http": requests.utils.get_environ_proxies(url).get("http"),
                "https": requests.utils.get_environ_proxies(url).get("https")
            }
            
            response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
            if response.status_code == 200:
                # A. 提取明文邮箱
                found.update(self.email_pattern.findall(response.text))
                
                # B. 提取 Base64 编码的邮箱 (常见于混淆)
                b64_matches = re.findall(r'base64,([a-zA-Z0-9+/=]{10,})', response.text)
                for b64 in b64_matches:
                    try:
                        decoded = base64.b64decode(b64).decode('utf-8')
                        if self.email_pattern.search(decoded):
                            found.add(self.email_pattern.search(decoded).group())
                    except:
                        pass
                
                # C. 提取 ROT13 编码的邮箱
                # 寻找形如 rot13("...") 的字符串或类似模式
                rot13_matches = re.findall(r'rot13\s*\(\s*["\'](.*?)["\']\s*\)', response.text)
                for r13 in rot13_matches:
                    try:
                        decoded = codecs.decode(r13, 'rot_13')
                        if self.email_pattern.search(decoded):
                            found.add(self.email_pattern.search(decoded).group())
                    except:
                        pass
        except Exception as e:
            # print(f"[Extractor Debug] Failed to scrape {url}: {e}")
            pass
        return found
