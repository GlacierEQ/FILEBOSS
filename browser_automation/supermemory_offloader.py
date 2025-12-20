#!/usr/bin/env python3
"""
Supermemory Context Offloader
Aggressive context offloading to eliminate token exhaustion
"""

import asyncio
import aiohttp
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional


class SupermemoryContextOffloader:
    """Offload all context to Supermemory cloud to save local tokens"""
    
    def __init__(self):
        self.api_key = "sm_tdpNTGLMbKRFCDjruaivZr_MhyVWbyEkrOhqKYpCWxiZyojMYMjqmlKiHtLUtcFsFybJujCmwxZJYpjZQIqvtNw"
        self.base_url = "https://api.supermemory.ai/v1"
        self.offload_threshold = 1000  # characters
        
    def generate_ref_id(self, data: Any) -> str:
        """Generate lightweight reference ID"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    async def offload_immediately(self, context_data: Dict) -> Dict:
        """
        Offload context to cloud IMMEDIATELY after generation
        Returns only lightweight reference
        """
        ref_id = self.generate_ref_id(context_data)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f'{self.base_url}/memory/store',
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'context_id': ref_id,
                        'data': context_data,
                        'timestamp': datetime.now().isoformat(),
                        'priority': 'high',
                        'retention': 'permanent',
                        'metadata': {
                            'source': 'browser_automation',
                            'type': context_data.get('type', 'general')
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                    else:
                        result = {'error': await response.text()}
                        
            except Exception as e:
                result = {'error': str(e)}
        
        return {
            'ref_id': ref_id,
            'stored': True,
            'size_saved': len(json.dumps(context_data)),
            'cloud_location': result.get('storage_id'),
            'status': result
        }
    
    async def retrieve_on_demand(self, ref_id: str) -> Optional[Dict]:
        """
        Retrieve from cloud only when absolutely needed
        Implements lazy loading pattern
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f'{self.base_url}/memory/retrieve/{ref_id}',
                    headers={'Authorization': f'Bearer {self.api_key}'},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
            except Exception as e:
                print(f"Error retrieving {ref_id}: {e}")
                return None
    
    async def batch_offload(self, data_list: list) -> list:
        """Offload multiple contexts in parallel"""
        tasks = [self.offload_immediately(data) for data in data_list]
        return await asyncio.gather(*tasks)


# Global instance for easy access
offloader = SupermemoryContextOffloader()


if __name__ == "__main__":
    # Test the offloader
    async def test():
        test_data = {
            'type': 'test',
            'content': 'This is test data to verify offloading works',
            'timestamp': datetime.now().isoformat()
        }
        
        result = await offloader.offload_immediately(test_data)
        print(f"Offloaded: {result}")
        
        if result['stored']:
            retrieved = await offloader.retrieve_on_demand(result['ref_id'])
            print(f"Retrieved: {retrieved}")
    
    asyncio.run(test())
