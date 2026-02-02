from core.verifier import EmailVerifier
import re

class EmailGuesser:
    """基于姓名和域名猜测候选邮箱并进行验证"""
    
    def __init__(self):
        # 常见企业邮箱格式模板
        self.formats = [
            "{first}.{last}@{domain}",      # john.smith@abc.com
            "{f}{last}@{domain}",           # jsmith@abc.com
            "{first}@{domain}",             # john@abc.com
            "{first}{last}@{domain}",       # johnsmith@abc.com
            "{first}_{last}@{domain}",      # john_smith@abc.com
            "{f}.{last}@{domain}"           # j.smith@abc.com
        ]

    def guess_and_verify(self, full_name, domain):
        """
        根据姓名和域名生成并验证邮箱。
        """
        if not full_name or not domain:
            return []
            
        # 1. 提取 First Name 和 Last Name
        name_parts = full_name.lower().split()
        if len(name_parts) < 2:
            first = name_parts[0]
            last = ""
        else:
            first = name_parts[0]
            last = name_parts[-1]
            
        # 2. 清洗域名
        domain = domain.replace("www.", "").lower()
        
        # 3. 生成候选名单
        candidates = []
        for fmt in self.formats:
            email = fmt.format(
                first=first,
                last=last,
                f=first[0] if first else "",
                domain=domain
            )
            # 简单校验格式
            if re.match(r'[^@]+@[^@]+\.[^@]+', email):
                candidates.append(email)
        
        # 4. 逐一验证（找到第一个有效的即停止，防止探测过于频繁）
        valid_emails = []
        for email in list(set(candidates)):
            print(f"[Guesser] Verifying candidate: {email}")
            is_valid, _ = EmailVerifier.verify(email)
            if is_valid:
                print(f"[Guesser] Found valid email! -> {email}")
                valid_emails.append(email)
                break
                
        return valid_emails
