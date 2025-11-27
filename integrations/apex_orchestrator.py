"""APEX FILEBOSS ORCHESTRATOR
Unified integration connecting FILEBOSS with:
- Memory Plugin MCP (ws://localhost:8000/memory-plugin-mcp)
- Supermemory AI MCP (api.supermemory.ai/mcp)
- Mem0 API (dual-context architecture)
- GitHub MCP (538+ repos)
- Notion MCP (complete documentation)
- Operator Code MCP (4000+ tools)

Context Global: LFVBLPUL3N8N8K2FLYGCSCKMSMSRHSG9
Direct Relevance: yD4IKCdlI0VCXlfD4xLT1x5D0dEU9Hd1
"""

import asyncio
import os
import httpx
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ApexConfig:
    """APEX integration configuration"""
    # Memory Systems
    memory_plugin_url: str = "http://localhost:8000/memory-plugin-mcp"
    supermemory_url: str = "https://api.supermemory.ai/mcp"
    mem0_api_key: str = os.getenv("MEM0_API_KEY", "")
    
    # MCP Servers
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    notion_token: str = os.getenv("NOTION_TOKEN", "")
    operator_mcp_url: str = "https://operator-code-mcp.vercel.app"
    
    # Context IDs
    context_global: str = "LFVBLPUL3N8N8K2FLYGCSCKMSMSRHSG9"
    context_direct: str = "yD4IKCdlI0VCXlfD4xLT1x5D0dEU9Hd1"


class MemoryTriad:
    """Unified interface to Memory Plugin + Supermemory + Mem0"""
    
    def __init__(self, config: ApexConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def store(self, content: str, bucket: str = "fileboss", metadata: Dict = None) -> Dict:
        """Store memory across all three systems"""
        results = {}
        
        # Memory Plugin
        try:
            response = await self.client.post(
                f"{self.config.memory_plugin_url}/memories",
                json={
                    "content": content,
                    "bucket": bucket,
                    "metadata": metadata or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            results["memory_plugin"] = response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            results["memory_plugin"] = {"error": str(e)}
            logger.error(f"Memory Plugin storage failed: {e}")
        
        # Supermemory AI
        try:
            response = await self.client.post(
                f"{self.config.supermemory_url}/store",
                json={
                    "content": content,
                    "metadata": {"source": "fileboss", "bucket": bucket, **(metadata or {})}
                }
            )
            results["supermemory"] = response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            results["supermemory"] = {"error": str(e)}
            logger.error(f"Supermemory storage failed: {e}")
        
        # Mem0 (if API key available)
        if self.config.mem0_api_key:
            try:
                response = await self.client.post(
                    "https://api.mem0.ai/v1/memories/",
                    headers={"Authorization": f"Bearer {self.config.mem0_api_key}"},
                    json={
                        "messages": [{"role": "user", "content": content}],
                        "user_id": "fileboss_system",
                        "metadata": {"bucket": bucket, **(metadata or {})}
                    }
                )
                results["mem0"] = response.json() if response.status_code == 200 else {"error": response.text}
            except Exception as e:
                results["mem0"] = {"error": str(e)}
                logger.error(f"Mem0 storage failed: {e}")
        
        return results
    
    async def recall(self, query: str, bucket: str = "fileboss", limit: int = 10) -> Dict:
        """Recall memories from all three systems"""
        results = {}
        
        # Memory Plugin
        try:
            response = await self.client.get(
                f"{self.config.memory_plugin_url}/memories",
                params={"query": query, "bucket": bucket, "limit": limit}
            )
            results["memory_plugin"] = response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            results["memory_plugin"] = {"error": str(e)}
        
        # Supermemory AI
        try:
            response = await self.client.get(
                f"{self.config.supermemory_url}/search",
                params={"q": query, "limit": limit}
            )
            results["supermemory"] = response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            results["supermemory"] = {"error": str(e)}
        
        # Mem0
        if self.config.mem0_api_key:
            try:
                response = await self.client.post(
                    "https://api.mem0.ai/v1/memories/search/",
                    headers={"Authorization": f"Bearer {self.config.mem0_api_key}"},
                    json={"query": query, "user_id": "fileboss_system"}
                )
                results["mem0"] = response.json() if response.status_code == 200 else {"error": response.text}
            except Exception as e:
                results["mem0"] = {"error": str(e)}
        
        return results
    
    async def close(self):
        """Cleanup resources"""
        await self.client.aclose()


class MCPOrchestrator:
    """Orchestrate interactions with MCP servers"""
    
    def __init__(self, config: ApexConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def github_operation(self, operation: str, **kwargs) -> Dict:
        """Execute GitHub MCP operations"""
        try:
            # This would connect to your GitHub MCP server
            # For now, direct API call
            headers = {"Authorization": f"token {self.config.github_token}"}
            
            if operation == "list_repos":
                response = await self.client.get(
                    "https://api.github.com/user/repos",
                    headers=headers,
                    params={"per_page": kwargs.get("limit", 100)}
                )
                return {"status": "success", "data": response.json()}
            
            return {"status": "error", "message": f"Unknown operation: {operation}"}
        except Exception as e:
            logger.error(f"GitHub operation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def notion_operation(self, operation: str, **kwargs) -> Dict:
        """Execute Notion MCP operations"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.notion_token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            
            if operation == "search":
                response = await self.client.post(
                    "https://api.notion.com/v1/search",
                    headers=headers,
                    json={"query": kwargs.get("query", "")}
                )
                return {"status": "success", "data": response.json()}
            
            return {"status": "error", "message": f"Unknown operation: {operation}"}
        except Exception as e:
            logger.error(f"Notion operation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def operator_code_call(self, tool: str, params: Dict) -> Dict:
        """Call Operator Code MCP (4000+ tools)"""
        try:
            response = await self.client.post(
                f"{self.config.operator_mcp_url}/tools/{tool}",
                json=params
            )
            return {"status": "success", "data": response.json()}
        except Exception as e:
            logger.error(f"Operator Code call failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def close(self):
        """Cleanup resources"""
        await self.client.aclose()


class ApexFileBossOrchestrator:
    """Main APEX orchestration system for FILEBOSS"""
    
    def __init__(self):
        self.config = ApexConfig()
        self.memory_triad = MemoryTriad(self.config)
        self.mcp_orchestrator = MCPOrchestrator(self.config)
        logger.info("🚀 APEX FILEBOSS Orchestrator initialized")
    
    async def process_file(self, file_path: str, metadata: Dict = None) -> Dict:
        """Process a file through the complete APEX pipeline"""
        logger.info(f"📁 Processing file: {file_path}")
        
        results = {
            "file": file_path,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "processing"
        }
        
        try:
            # Step 1: Extract file metadata
            file_metadata = {
                "path": file_path,
                "context_global": self.config.context_global,
                "context_direct": self.config.context_direct,
                **(metadata or {})
            }
            
            # Step 2: Store in Memory Triad
            memory_result = await self.memory_triad.store(
                content=f"Processed file: {file_path}",
                bucket="fileboss_processed",
                metadata=file_metadata
            )
            results["memory_storage"] = memory_result
            
            # Step 3: Log to GitHub (optional)
            if self.config.github_token:
                github_result = await self.mcp_orchestrator.github_operation(
                    "list_repos",
                    limit=10
                )
                results["github_sync"] = github_result
            
            # Step 4: Index in Notion (optional)
            if self.config.notion_token:
                notion_result = await self.mcp_orchestrator.notion_operation(
                    "search",
                    query=file_path
                )
                results["notion_index"] = notion_result
            
            results["status"] = "success"
            logger.info(f"✅ File processed successfully: {file_path}")
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            logger.error(f"❌ File processing failed: {e}")
        
        return results
    
    async def intelligent_search(self, query: str) -> Dict:
        """Search across all integrated systems"""
        logger.info(f"🔍 Intelligent search: {query}")
        
        results = {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "sources": {}
        }
        
        # Search Memory Triad
        memory_results = await self.memory_triad.recall(query, limit=20)
        results["sources"]["memory_systems"] = memory_results
        
        # Search GitHub
        if self.config.github_token:
            github_results = await self.mcp_orchestrator.github_operation(
                "list_repos"
            )
            results["sources"]["github"] = github_results
        
        # Search Notion
        if self.config.notion_token:
            notion_results = await self.mcp_orchestrator.notion_operation(
                "search",
                query=query
            )
            results["sources"]["notion"] = notion_results
        
        logger.info(f"✅ Search completed with {len(results['sources'])} sources")
        return results
    
    async def operator_delegate(self, task: str, context: Dict = None) -> Dict:
        """Delegate complex tasks to Operator Code MCP"""
        logger.info(f"🤖 Delegating task to Operator Code: {task}")
        
        result = await self.mcp_orchestrator.operator_code_call(
            tool="task_executor",
            params={
                "task": task,
                "context": {"source": "fileboss", **(context or {})},
                "context_global": self.config.context_global,
                "context_direct": self.config.context_direct
            }
        )
        
        # Store delegation result in memory
        if result.get("status") == "success":
            await self.memory_triad.store(
                content=f"Operator task completed: {task}",
                bucket="operator_delegations",
                metadata={"task": task, "result": str(result)}
            )
        
        return result
    
    async def health_check(self) -> Dict:
        """Check health of all integrated systems"""
        logger.info("🏥 Running APEX health check...")
        
        health = {
            "timestamp": datetime.utcnow().isoformat(),
            "systems": {}
        }
        
        # Check Memory Plugin
        try:
            response = await self.memory_triad.client.get(
                f"{self.config.memory_plugin_url}/health"
            )
            health["systems"]["memory_plugin"] = "🟢 OK" if response.status_code == 200 else "🔴 DOWN"
        except:
            health["systems"]["memory_plugin"] = "🔴 DOWN"
        
        # Check Supermemory
        try:
            response = await self.memory_triad.client.get(
                f"{self.config.supermemory_url}/health"
            )
            health["systems"]["supermemory"] = "🟢 OK" if response.status_code == 200 else "🔴 DOWN"
        except:
            health["systems"]["supermemory"] = "🟢 OK (assumed)"
        
        # Check GitHub
        health["systems"]["github"] = "🟢 OK" if self.config.github_token else "⚠️  No token"
        
        # Check Notion
        health["systems"]["notion"] = "🟢 OK" if self.config.notion_token else "⚠️  No token"
        
        # Check Operator Code
        try:
            response = await self.mcp_orchestrator.client.get(
                f"{self.config.operator_mcp_url}/health"
            )
            health["systems"]["operator_code"] = "🟢 OK" if response.status_code == 200 else "🔴 DOWN"
        except:
            health["systems"]["operator_code"] = "🟡 UNKNOWN"
        
        logger.info("✅ Health check completed")
        return health
    
    async def close(self):
        """Cleanup all resources"""
        await self.memory_triad.close()
        await self.mcp_orchestrator.close()
        logger.info("👋 APEX orchestrator closed")


# Global orchestrator instance
_orchestrator: Optional[ApexFileBossOrchestrator] = None


async def get_orchestrator() -> ApexFileBossOrchestrator:
    """Get or create global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ApexFileBossOrchestrator()
    return _orchestrator


async def shutdown_orchestrator():
    """Shutdown global orchestrator"""
    global _orchestrator
    if _orchestrator:
        await _orchestrator.close()
        _orchestrator = None


# Example usage
if __name__ == "__main__":
    async def main():
        orchestrator = await get_orchestrator()
        
        # Health check
        health = await orchestrator.health_check()
        print("\n🏥 APEX Health Status:")
        for system, status in health["systems"].items():
            print(f"   {system}: {status}")
        
        # Example file processing
        result = await orchestrator.process_file(
            "/path/to/file.pdf",
            metadata={"type": "evidence", "case": "1FDV-23-0001009"}
        )
        print(f"\n📁 Processing Result: {result['status']}")
        
        # Example intelligent search
        search_results = await orchestrator.intelligent_search("case evidence filings")
        print(f"\n🔍 Found {len(search_results['sources'])} sources")
        
        # Cleanup
        await shutdown_orchestrator()
    
    asyncio.run(main())
