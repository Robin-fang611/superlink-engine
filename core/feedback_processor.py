import imaplib
import email
from email.header import decode_header
try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None
import os
import json

class FeedbackProcessor:
    def __init__(self):
        self.imap_server = os.getenv("IMAP_SERVER")
        self.imap_port = int(os.getenv("IMAP_PORT", 993))
        self.email_account = os.getenv("SENDER_EMAIL")
        self.email_password = os.getenv("SENDER_PASSWORD")
        self.api_key = os.getenv("ZHIPUAI_API_KEY")
        
        if self.api_key and ZhipuAI:
            self.client = ZhipuAI(api_key=self.api_key)
        else:
            self.client = None

    def fetch_latest_replies(self, limit=10):
        """通过 IMAP 获取最近的未读邮件"""
        if not self.email_account or not self.email_password:
            return [], "未配置邮箱账号"
            
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_account, self.email_password)
            mail.select("INBOX")
            
            # 搜索未读邮件
            status, messages = mail.search(None, 'UNSEEN')
            if status != 'OK':
                return [], "搜索失败"
                
            email_ids = messages[0].split()
            replies = []
            
            # 只取最近的 limit 封
            for e_id in email_ids[-limit:]:
                res, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = self._decode_header(msg["Subject"])
                        from_ = msg.get("From")
                        body = self._get_email_body(msg)
                        
                        replies.append({
                            "from": from_,
                            "subject": subject,
                            "body": body
                        })
            
            mail.logout()
            return replies, "获取成功"
        except Exception as e:
            return [], str(e)

    def analyze_intent(self, email_body):
        """使用 GLM-4 分析回复意向"""
        if not self.client:
            return {"category": "unknown", "analysis": "AI 未配置"}
            
        prompt = f"""分析以下 B2B 开发信的客户回复内容，并将其分类为以下四类之一：
1. high_interest (高意向：询问价格、要求通话、要求报价)
2. consulting (咨询：询问更多信息、背景调查)
3. no_interest (无意向：拒绝、退订、已有供应商)
4. complaint (投诉：骚扰举报)

回复内容：
\"\"\"
{email_body}
\"\"\"

请仅返回 JSON 格式，包含字段 'category' (分类) 和 'reason' (简短分析原因)。
"""
        try:
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=[{"role": "user", "content": prompt}]
            )
            result_text = response.choices[0].message.content
            # 清洗 JSON
            clean_json = result_text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception as e:
            return {"category": "error", "analysis": str(e)}

    def _decode_header(self, header):
        decoded = decode_header(header)
        parts = []
        for content, encoding in decoded:
            if isinstance(content, bytes):
                parts.append(content.decode(encoding or 'utf-8', errors='ignore'))
            else:
                parts.append(content)
        return "".join(parts)

    def _get_email_body(self, msg):
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode(errors='ignore')
        else:
            return msg.get_payload(decode=True).decode(errors='ignore')
        return ""
