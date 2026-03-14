import smtplib
import socket
import dns.resolver
from email_validator import validate_email, EmailNotValidError
import requests
from bs4 import BeautifulSoup
import os
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.getenv('LOG_FILE', 'output/superlink.log')
)
logger = logging.getLogger('EmailVerifier')

class EmailVerifier:
    @staticmethod
    def verify(email: str):
        """
        三阶段邮箱验证：格式 -> MX记录 -> SMTP握手
        """
        # 获取配置
        timeout = int(os.getenv('VERIFICATION_TIMEOUT', 10))
        retries = int(os.getenv('VERIFICATION_RETRIES', 2))
        
        # 1. 格式验证
        try:
            v = validate_email(email, check_deliverability=False)
            email = v.normalized
            logger.info(f"邮箱格式验证通过: {email}")
        except EmailNotValidError as e:
            error_msg = f"格式错误: {str(e)}"
            logger.warning(f"邮箱格式验证失败: {email} - {error_msg}")
            return False, error_msg
        
        # 2. MX 记录验证
        domain = email.split('@')[1]
        mx_record = None
        
        for attempt in range(retries + 1):
            try:
                records = dns.resolver.resolve(domain, 'MX')
                mx_record = str(records[0].exchange)
                logger.info(f"MX记录验证通过: {domain} -> {mx_record}")
                break
            except dns.resolver.NXDOMAIN:
                error_msg = f"域名不存在: {domain}"
                logger.warning(f"MX记录验证失败: {email} - {error_msg}")
                return False, error_msg
            except dns.resolver.NoAnswer:
                error_msg = f"域名无MX记录: {domain}"
                logger.warning(f"MX记录验证失败: {email} - {error_msg}")
                return False, error_msg
            except Exception as e:
                error_msg = f"MX记录查询失败: {str(e)}"
                logger.warning(f"MX记录验证尝试 {attempt+1} 失败: {email} - {error_msg}")
                if attempt < retries:
                    time.sleep(1)
                    continue
                else:
                    return False, f"找不到有效MX记录: {str(e)}"
        
        if not mx_record:
            return False, "找不到有效MX记录"
        
        # 3. SMTP 握手验证 (模拟发送)
        for attempt in range(retries + 1):
            try:
                # 注意：某些ISP可能会屏蔽25端口，尝试使用587端口
                try:
                    server = smtplib.SMTP(host=mx_record, port=25, timeout=timeout)
                except:
                    server = smtplib.SMTP(host=mx_record, port=587, timeout=timeout)
                
                server.set_debuglevel(0)
                server.helo('superlink.com')
                server.mail('verify@superlink.com')
                code, message = server.rcpt(email)
                server.quit()
                
                if code == 250:
                    logger.info(f"SMTP验证通过: {email}")
                    return True, "验证通过"
                else:
                    error_msg = f"SMTP拒绝: {code} - {message.decode('utf-8', errors='ignore')}"
                    logger.warning(f"SMTP验证失败: {email} - {error_msg}")
                    return False, error_msg
            except smtplib.SMTPServerDisconnected:
                error_msg = "SMTP服务器断开连接"
                logger.warning(f"SMTP验证尝试 {attempt+1} 失败: {email} - {error_msg}")
            except smtplib.SMTPConnectError:
                error_msg = "SMTP连接失败"
                logger.warning(f"SMTP验证尝试 {attempt+1} 失败: {email} - {error_msg}")
            except (socket.timeout, TimeoutError):
                error_msg = "SMTP连接超时"
                logger.warning(f"SMTP验证尝试 {attempt+1} 失败: {email} - {error_msg}")
            except Exception as e:
                error_msg = f"SMTP验证失败: {str(e)}"
                logger.warning(f"SMTP验证尝试 {attempt+1} 失败: {email} - {error_msg}")
            
            if attempt < retries:
                time.sleep(2)
                continue
            else:
                return False, f"SMTP连接失败: {error_msg}"

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
                    logger.info(f"公司API验证通过: {company_name}")
                    return data["data"]["items"][0], "查询成功"
                else:
                    logger.warning(f"公司API验证无结果: {company_name}")
                    return None, "未找到公司信息"
            else:
                error_msg = f"状态码: {response.status_code}"
                logger.warning(f"公司API验证失败: {company_name} - {error_msg}")
                return None, error_msg
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"公司API验证异常: {company_name} - {error_msg}")
            return None, error_msg

    def verify_website(self, url: str):
        """抓取官网验证业务"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()  # 检查HTTP错误
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            # 简单清洗
            clean_text = " ".join(text.split())
            logger.info(f"网站验证通过: {url}")
            return clean_text[:1000], "抓取成功"
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.warning(f"网站验证失败: {url} - {error_msg}")
            return None, error_msg
        except Exception as e:
            error_msg = f"网站解析失败: {str(e)}"
            logger.warning(f"网站验证异常: {url} - {error_msg}")
            return None, error_msg
