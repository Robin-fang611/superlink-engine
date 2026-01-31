class KeywordExpander:
    """智能关键词扩展算法，提升搜索覆盖面 (Ultra Edition)"""
    
    def __init__(self):
        # 行业修饰符：针对不同业务角色深度裂变
        self.industry_modifiers = {
            '1': ['freight forwarder', 'shipping agent', 'cargo services', 'logistics provider', 'customs broker', '3PL provider', 'warehouse storage', 'ocean freight', 'air cargo'],
            '2': ['wholesaler', 'distributor', 'import company', 'trading company', 'buyer', 'retailer', 'online shop', 'e-commerce seller'],
            '3': ['国际货运代理', '物流公司', '货代', '海运', '空运', '清关', '专线', '双清包税'],
            '4': ['manufacturer', 'factory', 'supplier', 'export company', '工厂', '出口商', 'OEM factory', 'industrial park']
        }
        
        # 全球核心及二线商贸城市库：覆盖高密度 SME 区域
        self.geographic_modifiers = {
            'usa': [
                'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 
                'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville', 
                'Seattle', 'Denver', 'Miami', 'Atlanta', 'Boston', 'San Francisco', 'Detroit'
            ],
            'europe': [
                'Hamburg', 'Rotterdam', 'Antwerp', 'Lyon', 'Marseille', 'Milan', 'Naples', 
                'Madrid', 'Barcelona', 'Birmingham', 'Manchester', 'Warsaw', 'Prague', 
                'Munich', 'Frankfurt', 'Düsseldorf', 'Paris', 'London', 'Berlin'
            ],
            'china': [
                'Shenzhen', 'Guangzhou', 'Shanghai', 'Ningbo', 'Qingdao', 'Tianjin', 
                'Xiamen', 'Dongguan', 'Foshan', 'Zhongshan', 'Yiwu', 'Hangzhou', 'Suzhou'
            ]
        }
    
    def expand(self, base_keyword, module_id, region=None):
        """
        根据基础关键词、模块ID和地域扩展搜索词列表
        """
        expanded = set()
        base_keyword = base_keyword.strip()
        
        # 1. 基础关键词 + 行业修饰符
        modifiers = self.industry_modifiers.get(module_id, [])
        for mod in modifiers:
            expanded.add(f"{base_keyword} {mod}")
            expanded.add(f"{mod} {base_keyword}")
            
        # 2. 如果指定了地域，进行地域交叉裂变
        if region and region.lower() in self.geographic_modifiers:
            geos = self.geographic_modifiers[region.lower()]
            current_list = list(expanded)
            for item in current_list:
                for geo in geos:
                    expanded.add(f"{item} in {geo}")
        else:
            # 默认进行全地域（美/欧）轻量级裂变，以保证覆盖面
            all_geos = self.geographic_modifiers['usa'][:5] + self.geographic_modifiers['europe'][:5]
            current_list = list(expanded)
            for item in current_list:
                for geo in all_geos:
                    expanded.add(f"{item} in {geo}")
        
        # 返回列表，并限制最大扩展数量以防 API 压力过大
        return list(expanded)
