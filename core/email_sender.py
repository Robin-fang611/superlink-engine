import yagmail
import jinja2
import time
import os
import logging
from queue import Queue
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.getenv('LOG_FILE', 'output/superlink.log')
)
logger = logging.getLogger('EmailSender')

class EmailSender:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.send_interval = int(os.getenv("EMAIL_SEND_INTERVAL", 3))
        self.batch_limit = int(os.getenv("BATCH_SEND_LIMIT", 50))
        
        self.yag = None
        self.initialized = False
        self.init_error = None
        
        self._initialize()
            
        # 初始化模板引擎
        template_dir = os.path.join(os.getcwd(), 'templates')
        os.makedirs(template_dir, exist_ok=True)
        self.template_loader = jinja2.FileSystemLoader(searchpath=template_dir)
        self.template_env = jinja2.Environment(loader=self.template_loader)

    def _initialize(self):
        """初始化SMTP连接"""
        try:
            if not self.sender_email:
                self.init_error = "未配置发件人邮箱"
                logger.error(self.init_error)
                return
            
            if not self.sender_password:
                self.init_error = "未配置发件人密码"
                logger.error(self.init_error)
                return
            
            if not self.smtp_server:
                self.init_error = "未配置SMTP服务器"
                logger.error(self.init_error)
                return
            
            self.yag = yagmail.SMTP(
                user=self.sender_email,
                password=self.sender_password,
                host=self.smtp_server,
                port=self.smtp_port,
                smtp_starttls=True,
                smtp_ssl=False
            )
            
            # 测试连接
            self.yag.connect()
            self.initialized = True
            logger.info("SMTP服务初始化成功")
        except Exception as e:
            self.init_error = f"SMTP初始化失败: {str(e)}"
            logger.error(self.init_error)

    def send_email(self, to_email, subject, template_name, context):
        """发送单封邮件"""
        if not self.initialized:
            return False, self.init_error or "SMTP服务未初始化"
            
        if not to_email:
            error_msg = "收件人邮箱为空"
            logger.warning(error_msg)
            return False, error_msg
            
        try:
            # 验证模板是否存在
            if not os.path.exists(os.path.join('templates', template_name)):
                error_msg = f"邮件模板不存在: {template_name}"
                logger.warning(error_msg)
                return False, error_msg
            
            template = self.template_env.get_template(template_name)
            html_content = template.render(context)
            
            # 添加邮件头部，减少被判定为垃圾邮件的概率
            headers = {
                'From': f'SuperLink Team <{self.sender_email}>',
                'Reply-To': self.sender_email,
                'X-Mailer': 'SuperLink Data Engine',
                'Content-Type': 'text/html; charset=utf-8'
            }
            
            self.yag.send(
                to=to_email,
                subject=subject,
                contents=html_content,
                headers=headers
            )
            
            logger.info(f"邮件发送成功: {to_email} - {subject}")
            return True, "发送成功"
        except yagmail.SMTPAuthenticationError:
            error_msg = "SMTP认证失败，请检查邮箱密码"
            logger.error(error_msg)
            return False, error_msg
        except yagmail.SMTPRecipientsRefused:
            error_msg = "收件人邮箱被拒绝"
            logger.warning(f"邮件发送失败: {to_email} - {error_msg}")
            return False, error_msg
        except yagmail.SMTPConnectError:
            error_msg = "SMTP连接失败，请检查服务器设置"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"发送失败: {str(e)}"
            logger.warning(f"邮件发送失败: {to_email} - {error_msg}")
            return False, error_msg

    def send_bulk(self, leads, template_name, subject_template, rate_limit=None):
        """批量发送邮件，带频率限制"""
        if not self.initialized:
            return [{"error": self.init_error or "SMTP服务未初始化"}]
        
        if rate_limit is None:
            rate_limit = self.send_interval
        
        results = []
        success_count = 0
        fail_count = 0
        
        # 限制批量发送数量
        if len(leads) > self.batch_limit:
            leads = leads[:self.batch_limit]
            logger.info(f"批量发送数量超过限制，已截断为 {self.batch_limit} 条")
        
        logger.info(f"开始批量发送邮件，共 {len(leads)} 条，间隔 {rate_limit} 秒")
        
        for i, lead in enumerate(leads):
            email = lead.get("email")
            if not email:
                results.append({"email": None, "success": False, "message": "邮箱为空"})
                fail_count += 1
                continue
            
            context = {
                "company_name": lead.get("company_name", ""),
                "contact_person": lead.get("contact_person") or "Partner",
                "business_scope": lead.get("business_scope", "")
            }
            
            try:
                # 渲染动态标题
                subject = subject_template.format(**context)
            except Exception as e:
                error_msg = f"标题渲染失败: {str(e)}"
                results.append({"email": email, "success": False, "message": error_msg})
                fail_count += 1
                logger.warning(f"邮件 {i+1}/{len(leads)} 失败: {email} - {error_msg}")
                continue
            
            success, msg = self.send_email(email, subject, template_name, context)
            results.append({"email": email, "success": success, "message": msg})
            
            if success:
                success_count += 1
                logger.info(f"邮件 {i+1}/{len(leads)} 成功: {email}")
            else:
                fail_count += 1
                logger.warning(f"邮件 {i+1}/{len(leads)} 失败: {email} - {msg}")
            
            # 频率限制，最后一封邮件不需要等待
            if i < len(leads) - 1:
                logger.info(f"等待 {rate_limit} 秒后发送下一封邮件")
                time.sleep(rate_limit)
        
        logger.info(f"批量发送完成，成功: {success_count}, 失败: {fail_count}")
        return results

    def test_connection(self):
        """测试SMTP连接"""
        try:
            if not self.yag:
                self._initialize()
            
            if self.initialized:
                self.yag.connect()
                return True, "连接成功"
            else:
                return False, self.init_error
        except Exception as e:
            error_msg = f"连接测试失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def close(self):
        """关闭SMTP连接"""
        try:
            if self.yag:
                self.yag.close()
                logger.info("SMTP连接已关闭")
        except Exception as e:
            logger.warning(f"关闭SMTP连接时出错: {str(e)}")
