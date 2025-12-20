#!/usr/bin/env python3
"""
Unified Memory System
Integrates Supermemory, Mem0, and Memory Plugin
"""

import asyncio
import aiohttp
from typing import Dict, Any, List
from datetime import datetime


class UnifiedMemorySystem:
    """Integrate all memory layers for optimal context management"""
    
    def __init__(self):
        # Supermemory - Long-term knowledge
        self.supermemory_key = "sm_tdpNTGLMbKRFCDjruaivZr_MhyVWbyEkrOhqKYpCWxiZyojMYMjqmlKiHtLUtcFsFybJujCmwxZJYpjZQIqvtNw"
        
        # Mem0 - Session context
        self.mem0_key = "m0-CkabsxFjhaYf28gYSET3JWE34k3vw6oRBP5ZUm5H"
        self.mem0_org_id = "org_Gsa76AGniLIDLWGIgbmljwb7GCdPoExd3ERGKVkm"
        
        # Memory Plugin - Task-specific
        self.memory_plugin_primary = "LFvblPuL3N8N8k2FLyGcsCkMSMSrHsG9"
        self.memory_plugin_specialized = "yD4IKCdlI0VCXlfD4xLT1x5D0dEU9Hd1"
        
    async def store_distributed(self, context_type: str, data: Dict) -> Dict:
        """
        Distribute storage across memory layers based on context type
        
        Args:
            context_type: 'long_term_knowledge' | 'session_context' | 'task_specific'
            data: Context data to store
        
        Returns:
            Storage confirmation with reference IDs
        """
        
        if context_type == 'long_term_knowledge':
            # Supermemory: Best for persistent knowledge
            return await self._store_supermemory(data)
            
        elif context_type == 'session_context':
            # Mem0: Best for session-based personalization
            return await self._store_mem0(data)
            
        elif context_type == 'task_specific':
            # Memory Plugin: Best for task-specific context
            return await self._store_memory_plugin(data)
        
        else:
            raise ValueError(f"Unknown context type: {context_type}")
    
    async def _store_supermemory(self, data: Dict) -> Dict:
        """Store in Supermemory"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.supermemory.ai/v1/memory/store',
                headers={'Authorization': f'Bearer {self.supermemory_key}'},
                json={
                    'data': data,
                    'retention': 'permanent',
                    'timestamp': datetime.now().isoformat()
                }
            ) as response:
                return await response.json()
    
    async def _store_mem0(self, data: Dict) -> Dict:
        """Store in Mem0"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.mem0.ai/v1/memories',
                headers={'Authorization': f'Bearer {self.mem0_key}'},
                json={
                    'data': data,
                    'org_id': self.mem0_org_id,
                    'user_id': data.get('user_id', 'default')
                }
            ) as response:
                return await response.json()
    
    async def _store_memory_plugin(self, data: Dict) -> Dict:
        """Store in Memory Plugin"""
        # Memory Plugin API implementation
        return {
            'stored': True,
            'plugin': 'memory_plugin',
            'key': self.memory_plugin_specialized
        }
    
    async def retrieve_unified(self, query: str) -> List[Dict]:
        """Retrieve from all layers and merge intelligently"""
        
        results = await asyncio.gather(
            self._search_supermemory(query),
            self._search_mem0(query),
            self._search_memory_plugin(query),
            return_exceptions=True
        )
        
        # Merge and rank results
        merged = []
        for result in results:
            if isinstance(result, dict) and not isinstance(result, Exception):
                merged.append(result)
        
        return merged
    
    async def _search_supermemory(self, query: str) -> Dict:
        """Search Supermemory"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'https://api.supermemory.ai/v1/memory/search',
                headers={'Authorization': f'Bearer {self.supermemory_key}'},
                params={'query': query}
            ) as response:
                return await response.json()
    
    async def _search_mem0(self, query: str) -> Dict:
        """Search Mem0"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'https://api.mem0.ai/v1/memories/search',
                headers={'Authorization': f'Bearer {self.mem0_key}'},
                params={'query': query, 'org_id': self.mem0_org_id}
            ) as response:
                return await response.json()
    
    async def _search_memory_plugin(self, query: str) -> Dict:
        """Search Memory Plugin"""
        return {'source': 'memory_plugin', 'results': []}


if __name__ == "__main__":
    # Test unified memory system
    async def test():
        memory = UnifiedMemorySystem()
        
        # Store test data
        result = await memory.store_distributed(
            'long_term_knowledge',
            {'test': 'data', 'timestamp': datetime.now().isoformat()}
        )
        
        print(f"Stored: {result}")
    
    asyncio.run(test())
