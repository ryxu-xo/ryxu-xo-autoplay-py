"""
HTTP utilities for making requests with connection pooling and retries.
"""

import asyncio
import aiohttp
import ssl
from typing import Optional, Dict, Any
from .autoplay_apis import fast_fetch


class HTTPClient:
    """HTTP client with connection pooling and retry logic."""
    
    def __init__(self, timeout: int = 5000, max_sockets: int = 3, max_free_sockets: int = 1):
        self.timeout = aiohttp.ClientTimeout(total=timeout / 1000)
        self.connector = aiohttp.TCPConnector(
            limit=max_sockets,
            limit_per_host=max_sockets,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=ssl.create_default_context()
        )
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=self.timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
                'Accept': 'text/html,application/json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str, options: Optional[Dict[str, Any]] = None, attempt: int = 0) -> str:
        """Fetch a page with retry logic and redirect support."""
        if not self.session:
            raise RuntimeError("HTTPClient not initialized. Use async context manager.")
        
        options = options or {}
        headers = options.get('headers', {})
        
        try:
            async with self.session.get(url, headers=headers, allow_redirects=True) as response:
                if response.status >= 300 and response.status < 400:
                    location = response.headers.get('location')
                    if location:
                        return await self.fetch_page(location, options, attempt)
                
                if response.status != 200:
                    if attempt < 1:  # Reduced retries for performance
                        await asyncio.sleep(0.1 * (attempt + 1))  # Reduced delay
                        return await self.fetch_page(url, options, attempt + 1)
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"Request failed with status: {response.status}"
                    )
                
                return await response.text()
                
        except asyncio.TimeoutError:
            if attempt < 1:
                await asyncio.sleep(0.1 * (attempt + 1))
                return await self.fetch_page(url, options, attempt + 1)
            raise TimeoutError("Request timed out")
        except Exception as e:
            if attempt < 1:
                await asyncio.sleep(0.1 * (attempt + 1))
                return await self.fetch_page(url, options, attempt + 1)
            raise e


# Global HTTP client instance
_http_client: Optional[HTTPClient] = None


async def get_http_client() -> HTTPClient:
    """Get or create the global HTTP client."""
    global _http_client
    if _http_client is None:
        _http_client = HTTPClient()
    return _http_client


async def fetch_page(url: str, options: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to fetch a page using the global HTTP client."""
    async with HTTPClient() as client:
        return await client.fetch_page(url, options)
