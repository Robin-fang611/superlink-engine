import yagmail
import jinja2
import time
import os
from queue import Queue
from datetime import datetime

class EmailSender:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        
        if self.sender_email and self.sender_password:
            self.yag = yagmail.SMTP(
                user=self.sender_email,
                password=self.sender_password,
                host=self.smtp_server,
                port=self.smtp_port
            )
        else:
            self.yag = None
            
        # 初始化模板引擎
        template_dir = os.path.join(os.getcwd(), 'templates')
        os.makedirs(template_dir, exist_ok=True)
        self.template_loader = jinja2.FileSystemLoader(searchpath=template_dir)
        self.template_env = jinja2.Environment(loader=self.template_loader)

    def send_email(self, to_email, subject, template_name, context):
        """发送单封邮件"""
        if not self.yag:
            return False, "未配置 SMTP 服务"
            
        try:
            template = self.template_env.get_template(template_name)
            html_content = template.render(context)
            
            self.yag.send(
                to=to_email,
                subject=subject,
                contents=html_content
            )
            return True, "发送成功"
        except Exception as e:
            return False, str(e)

    def send_bulk(self, leads, template_name, subject_template, rate_limit=3):
        """批量发送邮件，带频率限制"""
        results = []
        for lead in leads:
            context = {
                "company_name": lead.get("company_name"),
                "contact_person": lead.get("contact_person") or "Partner",
                "business_scope": lead.get("business_scope")
            }
            
            # 渲染动态标题
            subject = subject_template.format(**context)
            
            success, msg = self.send_email(lead.get("email"), subject, template_name, context)
            results.append({"email": lead.get("email"), "success": success, "message": msg})
            
            # 频率限制
            time.sleep(rate_limit)
            
        return results
