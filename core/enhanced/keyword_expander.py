class KeywordExpander:
    """智能关键词扩展算法，提升搜索覆盖面"""
    
    def __init__(self):
        self.industry_modifiers = {
            '1': ['freight forwarder', 'shipping agent', 'cargo services', 'logistics provider', 'customs broker'],
            '2': ['wholesaler', 'distributor', 'import company', 'trading company', 'buyer'],
            '3': ['国际货运代理', '物流公司', '货代', '海运', '空运'],
            '4': ['manufacturer', 'factory', 'supplier', 'export company', '工厂', '出口商']
        }
        
        self.geographic_modifiers = {
            'usa': ['United States', 'USA', 'America', 'US', 'New York', 'Los Angeles', 'Chicago', 'Houston'],
            'europe': ['Germany', 'France', 'UK', 'Italy', 'Spain', 'Netherlands', 'Belgium'],
            'china': ['China', 'Shenzhen', 'Guangzhou', 'Shanghai', 'Ningbo', 'Qingdao', 'Tianjin']
        }
    
    def expand(self, base_keyword, module_id, region=None):
        """
        根据基础关键词、模块ID和地域扩展搜索词列表
        """
        expanded = set()
        base_keyword = base_keyword.strip()
        
        # 1. 基础关键词本身
        expanded.add(base_keyword)
        
        # 2. 结合行业修饰符
        modifiers = self.industry_modifiers.get(module_id, [])
        for mod in modifiers:
            expanded.add(f"{base_keyword} {mod}")
            expanded.add(f"{mod} {base_keyword}")
            
        # 3. 结合地理修饰符（如果提供）
        if region and region.lower() in self.geographic_modifiers:
            geos = self.geographic_modifiers[region.lower()]
            current_list = list(expanded)
            for item in current_list:
                for geo in geos:
                    expanded.add(f"{item} in {geo}")
                    expanded.add(f"{geo} {item}")
        
        return list(expanded)
