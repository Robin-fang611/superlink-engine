import re
import json
import os
from typing import List, Dict
from core.processor import Processor

class EnhancedProcessor(Processor):
    """增强版处理器：正则预提取 + 小批量 AI 验证"""
    
    def __init__(self):
        super().__init__()
        # 正则表达式预提取
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'\+?[0-9\s\-\(\)]{8,}')

    def _pre_extract(self, text: str) -> Dict:
        """使用正则快速提取可能的邮箱和电话"""
        emails = self.email_pattern.findall(text)
        phones = self.phone_pattern.findall(text)
        return {
            "emails": list(set(emails)),
            "phones": list(set(phones))
        }

    def process_batch_enhanced(self, raw_results: List[Dict], batch_size: int = 15) -> List[Dict]:
        """
        分批处理原始搜索结果，每批次由 AI 进行结构化提取
        """
        all_leads = []
        total = len(raw_results)
        
        # 1. 预处理：先用正则提取简单信息
        for item in raw_results:
            combined_text = f"{item.get('title', '')} {item.get('snippet', '')}"
            item['regex_data'] = self._pre_extract(combined_text)

        # 2. 分批送入 AI 审计和精细提取
        for i in range(0, total, batch_size):
            batch = raw_results[i : i + batch_size]
            print(f"[EnhancedProcessor] AI processing batch {i//batch_size + 1} ({len(batch)} items)...")
            
            # 构造批量 Prompt，告知 AI 参考正则提取的结果
            batch_data_str = ""
            for idx, item in enumerate(batch):
                batch_data_str += f"ID: {idx}\nTitle: {item.get('title')}\nSnippet: {item.get('snippet')}\nURL: {item.get('link')}\nRegex_Found: {item['regex_data']}\n---\n"

            prompt = f"""Analyze the following search results for B2B business leads (SMEs).
YOUR GOAL: Extract as many valid SME leads as possible. 

RULES:
1. FOCUS: Small/Medium businesses only. Reject giant global brands (DHL, Amazon, etc.).
2. FLEXIBILITY: If a lead looks like a high-quality SME, extract it even if some fields (like contact person) are missing.
3. VALIDATION: Check 'Regex_Found' for emails/phones already spotted by regex. 
4. REJECTION: Ignore news, job boards, and general directories.

Search Results:
{batch_data_str}

Output MUST be a JSON list of objects. Each object MUST have these keys (EXACTLY AS WRITTEN):
"公司名称", "注册国家/城市", "业务负责人", "公开邮箱", "公开电话", "业务范围", "来源URL"
"""
            try:
                # 调用父类的 AI 接口
                response = self.client.chat.completions.create(
                    model="glm-4",
                    messages=[{"role": "user", "content": prompt}]
                )
                text_result = response.choices[0].message.content
                processed_batch = self._clean_json(text_result)
                
                if isinstance(processed_batch, list):
                    all_leads.extend(processed_batch)
            except Exception as e:
                print(f"[EnhancedProcessor] AI Batch Error: {str(e)}")

        return all_leads
