import asyncio
import aiohttp
import os
import json
from typing import List, Dict

class AsyncSearcher:
    """异步搜索器，提升搜索速度，适配低价代理"""
    
    def __init__(self, concurrency=3):
        # 针对低价代理，默认并发数设为较小的 3，避免连接被重置
        self.semaphore = asyncio.Semaphore(concurrency)
        self.api_url = "https://google.serper.dev/search"
        self.api_key = os.getenv("SERPER_API_KEY")
        
        # 代理设置
        self.proxy = os.getenv("HTTP_PROXY") if os.getenv("USE_PROXY", "True").lower() == "true" else None

    async def _fetch_single(self, session: aiohttp.ClientSession, query: str, page: int) -> Dict:
        """执行单个 POST 请求"""
        payload = json.dumps({
            "q": query,
            "num": 100,  # 每次请求获取 100 条结果，极大提升单次搜索量
            "page": page,
            "gl": "us",
            "hl": "en"
        })
        
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        async with self.semaphore:
            try:
                # 显式传入代理参数
                async with session.post(
                    self.api_url, 
                    headers=headers, 
                    data=payload, 
                    proxy=self.proxy,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"[AsyncSearch] Error {response.status} for query: {query}")
                        return None
            except Exception as e:
                print(f"[AsyncSearch] Exception for query {query}: {str(e)}")
                return None

    async def search_batch(self, queries: List[str], pages_per_query: int = 2) -> List[Dict]:
        """批量并行搜索"""
        if not self.api_key:
            print("[AsyncSearch] Error: SERPER_API_KEY not found.")
            return []

        async with aiohttp.ClientSession() as session:
            tasks = []
            for query in queries:
                for page in range(1, pages_per_query + 1):
                    tasks.append(self._fetch_single(session, query, page))
            
            print(f"[AsyncSearch] Launching {len(tasks)} parallel search requests...")
            results = await asyncio.gather(*tasks)
            
            # 过滤掉失败的结果并汇总
            valid_results = []
            for res in results:
                if res and "organic" in res:
                    valid_results.extend(res["organic"])
            
            print(f"[AsyncSearch] Total raw results collected: {len(valid_results)}")
            return valid_results
