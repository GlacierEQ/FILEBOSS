"""Event Bus System for Inter-Module Communication"""

from typing import Dict, List, Callable, Any
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class EventBus:
    """Central event bus for plugin communication"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._max_history = 1000
        
        logger.info("📡 EventBus initialized")
    
    def subscribe(self, event_name: str, handler: Callable):
        """Subscribe to an event"""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        
        self._handlers[event_name].append(handler)
        logger.info(f"🔔 Subscribed to event: {event_name}")
    
    def unsubscribe(self, event_name: str, handler: Callable):
        """Unsubscribe from an event"""
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
                logger.info(f"🔕 Unsubscribed from event: {event_name}")
            except ValueError:
                logger.warning(f"⚠️ Handler not found for event: {event_name}")
    
    def emit(self, event_name: str, data: Any = None):
        """Emit an event to all subscribers"""
        logger.info(f"📡 Emitting event: {event_name}")
        
        # Record event in history
        self._record_event(event_name, data)
        
        # Call all handlers
        if event_name in self._handlers:
            for handler in self._handlers[event_name]:
                try:
                    # Handle both sync and async handlers
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.create_task(handler(data))
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"❌ Error in event handler for {event_name}: {e}")
        else:
            logger.debug(f"🔇 No handlers for event: {event_name}")
    
    async def emit_async(self, event_name: str, data: Any = None):
        """Emit an event asynchronously"""
        logger.info(f"📡 Emitting async event: {event_name}")
        
        # Record event in history
        self._record_event(event_name, data)
        
        # Call all handlers
        if event_name in self._handlers:
            tasks = []
            for handler in self._handlers[event_name]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        tasks.append(handler(data))
                    else:
                        # Run sync handler in thread pool
                        tasks.append(asyncio.get_event_loop().run_in_executor(None, handler, data))
                except Exception as e:
                    logger.error(f"❌ Error preparing handler for {event_name}: {e}")
            
            # Wait for all handlers to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def _record_event(self, event_name: str, data: Any):
        """Record event in history"""
        event_record = {
            "event_name": event_name,
            "timestamp": datetime.now().isoformat(),
            "data_type": type(data).__name__,
            "has_data": data is not None
        }
        
        self._event_history.append(event_record)
        
        # Trim history if too long
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
    
    def get_subscribers(self, event_name: str) -> int:
        """Get number of subscribers for an event"""
        return len(self._handlers.get(event_name, []))
    
    def get_all_events(self) -> List[str]:
        """Get list of all events with subscribers"""
        return list(self._handlers.keys())
    
    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent event history"""
        return self._event_history[-limit:]
    
    def clear_history(self):
        """Clear event history"""
        self._event_history.clear()
        logger.info("🗑️ Cleared event history")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            "total_events": len(self._handlers),
            "total_subscribers": sum(len(handlers) for handlers in self._handlers.values()),
            "events_emitted": len(self._event_history),
            "event_types": list(self._handlers.keys())
        }