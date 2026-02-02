import smtplib
import dns.resolver
from email_validator import validate_email, EmailNotValidError
import requests
from bs4 import BeautifulSoup
import os

class EmailVerifier:
    @staticmethod
    def verify(email: str):
        """
        三阶段邮箱验证：格式 -> MX记录 -> SMTP握手
        """
        # 1. 格式验证
        try:
            v = validate_email(email, check_deliverability=False)
            email = v.normalized
        except EmailNotValidError as e:
            return False, f"格式错误: {str(e)}"
        
        # 2. MX 记录验证
        domain = email.split('@')[1]
        try:
            records = dns.resolver.resolve(domain, 'MX')
            mx_record = str(records[0].exchange)
        except Exception:
            return False, "找不到有效MX记录"
        
        # 3. SMTP 握手验证 (模拟发送)
        try:
            # 注意：某些ISP可能会屏蔽25端口
            server = smtplib.SMTP(host=mx_record, port=25, timeout=10)
            server.helo()
            server.mail('verify@superlink.com')
            code, message = server.rcpt(email)
            server.quit()
            
            if code == 250:
                return True, "验证通过"
            else:
                return False, f"SMTP拒绝: {code}"
        except Exception as e:
            return False, f"SMTP连接失败: {str(e)}"

class CompanyVerifier:
    def __init__(self):
        self.tianyancha_key = os.getenv("TIANYANCHA_API_KEY")

    def verify_via_api(self, company_name: str):
        """调用天眼查API获取工商信息"""
        if not self.tianyancha_key:
            return None, "未配置天眼查API密钥"
            
        url = "https://api.tianyancha.com/services/open/company/search"
        params = {"keyword": company_name, "key": self.tianyancha_key}
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("data", {}).get("items"):
                    return data["data"]["items"][0], "查询成功"
            return None, f"状态码: {response.status_code}"
        except Exception as e:
            return None, str(e)

    def verify_website(self, url: str):
        """抓取官网验证业务"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            # 简单清洗
            clean_text = " ".join(text.split())
            return clean_text[:1000], "抓取成功"
        except Exception as e:
            return None, str(e)
