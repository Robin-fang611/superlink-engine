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
            "{f}.{last}@{domain}",          # j.smith@abc.com
            "{last}.{first}@{domain}",      # smith.john@abc.com
            "{last}{f}@{domain}",           # smithj@abc.com
            "{first}{l}@{domain}",          # johns@abc.com
            "{first}-{last}@{domain}"       # john-smith@abc.com
        ]

    def guess_and_verify(self, full_name, domain):
        """
        根据姓名和域名生成并验证邮箱。
        """
        if not full_name or not domain:
            return []
            
        # 1. 清洗姓名和域名
        full_name = re.sub(r'[^a-zA-Z\s]', '', full_name).lower().strip()
        domain = domain.replace("www.", "").lower().strip()
        
        name_parts = full_name.split()
        if not name_parts:
            return []

        first = name_parts[0]
        last = name_parts[-1] if len(name_parts) > 1 else ""
        f = first[0] if first else ""
        l = last[0] if last else ""
        
        # 2. 生成候选名单
        candidates = []
        for fmt in self.formats:
            try:
                email = fmt.format(
                    first=first,
                    last=last,
                    f=f,
                    l=l,
                    domain=domain
                ).replace("..", ".").replace("--", "-") # 容错处理
                
                # 简单校验格式
                if re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', email):
                    candidates.append(email)
            except Exception:
                continue
        
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
