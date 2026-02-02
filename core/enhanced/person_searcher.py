from core.searcher import Searcher
import re

class PersonSearcher:
    """利用 Google 侧向搜索挖掘 LinkedIn 关键决策人 (Ultra Engine)"""
    
    def __init__(self):
        self.searcher = Searcher()

    def find_decision_makers(self, company_name, target_positions=None):
        """
        根据公司名和目标职位，通过搜索引擎侧向定位 LinkedIn 上的关键人信息。
        """
        if not company_name:
            return []
            
        target_positions = target_positions or ["Purchasing", "Procurement", "Supply Chain", "Logistics", "CEO", "Founder"]
        
        # 1. 构造高级搜索指令
        # 示例：site:linkedin.com/in "Walmart" ("Purchasing" OR "Procurement")
        pos_query = " OR ".join([f'"{p}"' for p in target_positions])
        query = f'site:linkedin.com/in "{company_name}" ({pos_query})'
        
        print(f"[PersonSearcher] Hunting for leaders at {company_name}...")
        res = self.searcher._execute_search(query, num_results=10)
        
        decision_makers = []
        if res and "organic" in res:
            for item in res["organic"]:
                title = item.get("title", "")
                # 尝试从 LinkedIn 标题中提取姓名和职位
                # 常见格式: "Name - Position - Company | LinkedIn"
                parts = title.split(" - ")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    position = parts[1].strip()
                    
                    # 简单清洗姓名（去掉 LinkedIn 等后缀）
                    name = re.sub(r' \|.*$', '', name).strip()
                    
                    decision_makers.append({
                        "name": name,
                        "position": position,
                        "linkedin_url": item.get("link"),
                        "snippet": item.get("snippet")
                    })
        
        return decision_makers
