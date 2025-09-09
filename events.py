"""
Event system for the autoplay package.
"""

import asyncio
from typing import Dict, Any, Callable, Optional
from .types import AutoplayResult, LavalinkTrackInfo


class AutoplayEventEmitter:
    """Event emitter for autoplay events."""
    
    def __init__(self):
        self._listeners: Dict[str, list] = {}
    
    def on(self, event: str, callback: Callable) -> None:
        """Register an event listener."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
    
    def off(self, event: str, callback: Callable) -> None:
        """Remove an event listener."""
        if event in self._listeners:
            try:
                self._listeners[event].remove(callback)
            except ValueError:
                pass
    
    def emit(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all listeners."""
        if event in self._listeners:
            for callback in self._listeners[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(*args, **kwargs))
                    else:
                        callback(*args, **kwargs)
                except Exception as e:
                    print(f"[Event Error] {event}: {str(e)}")
    
    def remove_all_listeners(self, event: Optional[str] = None) -> None:
        """Remove all listeners for an event or all events."""
        if event:
            self._listeners.pop(event, None)
        else:
            self._listeners.clear()
