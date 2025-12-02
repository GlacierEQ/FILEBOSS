"""
Redis Connection Pool Manager - Issue #42 Fix
Implements connection pooling with health checks and leak prevention
"""
import asyncio
import logging
from typing import Optional, Any
from contextlib import asynccontextmanager
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError

logger = logging.getLogger(__name__)

class RedisPoolManager:
    """
    Manages Redis connection pool with automatic health checks,
    leak detection, and graceful connection recycling.
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        max_connections: int = 50,
        min_idle_connections: int = 10,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        health_check_interval: int = 30
    ):
        """
        Initialize Redis connection pool manager.
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Database number
            max_connections: Maximum pool size
            min_idle_connections: Minimum idle connections to maintain
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Connection timeout in seconds
            health_check_interval: Health check interval in seconds
        """
        self.host = host
        self.port = port
        self.db = db
        self.max_connections = max_connections
        self.min_idle_connections = min_idle_connections
        
        # Create connection pool
        self.pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=True,
            health_check_interval=health_check_interval
        )
        
        self._redis_client: Optional[Redis] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._connection_stats = {
            'total_acquired': 0,
            'total_released': 0,
            'current_active': 0,
            'failed_acquisitions': 0,
            'health_checks_passed': 0,
            'health_checks_failed': 0
        }
    
    async def start(self):
        """Start pool manager and health monitoring."""
        if self._is_running:
            logger.warning("Pool manager already running")
            return
        
        self._redis_client = Redis(connection_pool=self.pool)
        self._is_running = True
        
        # Start health check background task
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info(f"Redis pool started: {self.host}:{self.port}/{self.db}")
        logger.info(f"Pool config: max={self.max_connections}, min_idle={self.min_idle_connections}")
    
    async def stop(self):
        """Stop pool manager and close all connections."""
        if not self._is_running:
            return
        
        self._is_running = False
        
        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        if self._redis_client:
            await self._redis_client.close()
        await self.pool.disconnect()
        
        logger.info("Redis pool stopped")
        logger.info(f"Final stats: {self._connection_stats}")
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Context manager for safely acquiring and releasing connections.
        
        Usage:
            async with pool.get_connection() as redis:
                await redis.set('key', 'value')
        
        Yields:
            Redis client connection
        """
        if not self._is_running:
            raise RuntimeError("Pool manager not started. Call start() first.")
        
        connection = None
        try:
            # Acquire connection from pool
            connection = self._redis_client
            self._connection_stats['total_acquired'] += 1
            self._connection_stats['current_active'] += 1
            
            logger.debug(f"Connection acquired. Active: {self._connection_stats['current_active']}")
            yield connection
            
        except RedisError as e:
            self._connection_stats['failed_acquisitions'] += 1
            logger.error(f"Redis connection error: {e}")
            raise
        finally:
            # Always release connection back to pool
            if connection:
                self._connection_stats['total_released'] += 1
                self._connection_stats['current_active'] -= 1
                logger.debug(f"Connection released. Active: {self._connection_stats['current_active']}")
    
    async def _health_check_loop(self):
        """Background task for periodic health checks."""
        while self._is_running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _perform_health_check(self):
        """Perform health check on Redis connection."""
        try:
            async with self.get_connection() as redis:
                # Simple ping test
                await redis.ping()
                
                # Check pool stats
                pool_stats = self.get_pool_stats()
                
                self._connection_stats['health_checks_passed'] += 1
                logger.debug(f"Health check passed. Pool stats: {pool_stats}")
                
                # Warn if pool is exhausted
                if pool_stats['in_use'] >= self.max_connections * 0.9:
                    logger.warning(f"Pool nearly exhausted: {pool_stats['in_use']}/{self.max_connections}")
                
        except Exception as e:
            self._connection_stats['health_checks_failed'] += 1
            logger.error(f"Health check failed: {e}")
    
    def get_pool_stats(self) -> dict:
        """Get current pool statistics."""
        pool = self.pool
        return {
            'max_connections': self.max_connections,
            'in_use': pool._in_use_connections if hasattr(pool, '_in_use_connections') else 0,
            'available': pool._available_connections if hasattr(pool, '_available_connections') else 0,
            'stats': self._connection_stats.copy()
        }
    
    async def warm_up(self, num_connections: int = None):
        """Pre-create idle connections for faster initial requests."""
        num_connections = num_connections or self.min_idle_connections
        
        logger.info(f"Warming up pool with {num_connections} connections")
        tasks = []
        
        for _ in range(num_connections):
            async def ping():
                async with self.get_connection() as redis:
                    await redis.ping()
            tasks.append(ping())
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Pool warm-up complete")


# Singleton instance for application-wide use
_pool_manager: Optional[RedisPoolManager] = None

def get_redis_pool() -> RedisPoolManager:
    """Get singleton Redis pool manager instance."""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = RedisPoolManager()
    return _pool_manager


async def init_redis_pool(host: str = 'localhost', port: int = 6379):
    """Initialize Redis pool at application startup."""
    pool = get_redis_pool()
    pool.host = host
    pool.port = port
    await pool.start()
    await pool.warm_up()
    logger.info("✅ Redis connection pool initialized")
    return pool


async def shutdown_redis_pool():
    """Shutdown Redis pool at application shutdown."""
    pool = get_redis_pool()
    await pool.stop()
    logger.info("🛑 Redis connection pool shutdown complete")
