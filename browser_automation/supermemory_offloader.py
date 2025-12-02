#!/usr/bin/env python3
"""Supermemory offloader with pooled sessions and resilient retries."""

import asyncio
import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp


class SupermemoryContextOffloader:
    """Offload context to Supermemory cloud and return lightweight handles."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://api.supermemory.ai/v1",
        max_connections: int = 50,
        request_timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key or os.getenv("SUPERMEMORY_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.offload_threshold = 1000  # characters
        self._timeout = aiohttp.ClientTimeout(total=request_timeout)
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector_limit = max_connections
        self._max_retries = max_retries

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create a pooled HTTP session for low-latency calls."""

        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                connector=aiohttp.TCPConnector(
                    limit=self._connector_limit, ttl_dns_cache=300
                ),
            )
        return self._session

    def generate_ref_id(self, data: Any) -> str:
        """Generate a deterministic lightweight reference ID."""

        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    async def _request(self, method: str, path: str, *, payload: Optional[Dict] = None) -> Dict:
        if not self.api_key:
            raise RuntimeError("SUPERMEMORY_API_KEY is required for offloading")

        session = await self._get_session()
        url = f"{self.base_url}{path}"
        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries):
            try:
                async with session.request(
                    method,
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                ) as response:
                    if 200 <= response.status < 300:
                        return await response.json()
                    last_error = RuntimeError(
                        f"Unexpected status {response.status}: {await response.text()}"
                    )
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_error = exc

            if attempt < self._max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))

        raise RuntimeError(f"Supermemory request failed: {last_error}")

    async def offload_immediately(self, context_data: Dict) -> Dict:
        """Offload context immediately and return a reference handle."""

        ref_id = self.generate_ref_id(context_data)
        payload = {
            "context_id": ref_id,
            "data": context_data,
            "timestamp": datetime.now().isoformat(),
            "priority": "high",
            "retention": "permanent",
            "metadata": {
                "source": "browser_automation",
                "type": context_data.get("type", "general"),
            },
        }

        result = await self._request("POST", "/memory/store", payload=payload)

        return {
            "ref_id": ref_id,
            "stored": True,
            "size_saved": len(json.dumps(context_data)),
            "cloud_location": result.get("storage_id"),
            "status": result,
        }

    async def retrieve_on_demand(self, ref_id: str) -> Optional[Dict]:
        """Retrieve previously offloaded context."""

        try:
            return await self._request("GET", f"/memory/retrieve/{ref_id}")
        except Exception as exc:  # noqa: BLE001 - surfaced for observability
            print(f"Error retrieving {ref_id}: {exc}")
            return None

    async def batch_offload(self, data_list: list) -> list:
        """Offload multiple contexts in parallel."""

        tasks = [self.offload_immediately(data) for data in data_list]
        return await asyncio.gather(*tasks)

    async def close(self) -> None:
        """Release pooled HTTP resources."""

        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None


# Global instance for easy access
offloader = SupermemoryContextOffloader()


if __name__ == "__main__":
    # Test the offloader
    async def test():
        if not offloader.api_key:
            print("SUPERMEMORY_API_KEY not set; skipping live offload test.")
            return

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
