"""
Event Bus System
Event-driven architecture for internal communication
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Event type enumeration"""
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_PROCESSED = "message.processed"
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    HITL_APPROVAL_REQUIRED = "hitl.approval_required"
    HITL_APPROVED = "hitl.approved"
    HITL_REJECTED = "hitl.rejected"
    RL_REWARD = "rl.reward"
    RL_MODEL_UPDATED = "rl.model_updated"
    FRL_AGGREGATION = "frl.aggregation"
    MANIFEST_UPDATED = "manifest.updated"


@dataclass
class Event:
    """
    Event data structure
    
    Attributes:
        event_type: Type of event
        payload: Event payload data
        timestamp: Event timestamp
        source: Source of the event
        correlation_id: Correlation ID for event tracking
    """
    
    event_type: EventType
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_type": self.event_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "correlation_id": self.correlation_id,
        }


class EventBus:
    """
    Event Bus for pub/sub communication
    
    Provides event-driven architecture for loose coupling between components
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._logger = logging.getLogger(__name__)
        self._event_history: List[Event] = []
        self._max_history: int = 1000
    
    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: Type of event to subscribe to
            callback: Callback function to invoke when event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            self._logger.debug(f"Subscribed to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Unsubscribe from an event type
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to remove
        """
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                self._logger.debug(f"Unsubscribed from {event_type.value}")
    
    async def emit(self, event: Event) -> None:
        """
        Emit an event to all subscribers
        
        Args:
            event: Event to emit
        """
        # Store event in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Get subscribers for this event type
        subscribers = self._subscribers.get(event.event_type, [])
        
        if not subscribers:
            self._logger.debug(f"No subscribers for {event.event_type.value}")
            return
        
        self._logger.debug(f"Emitting {event.event_type.value} to {len(subscribers)} subscribers")
        
        # Invoke all subscribers
        tasks = []
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(event))
                else:
                    callback(event)
            except Exception as e:
                self._logger.error(f"Error in event subscriber: {e}", exc_info=True)
        
        # Wait for async callbacks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def emit_sync(self, event: Event) -> None:
        """
        Emit an event synchronously (for non-async contexts)
        
        Args:
            event: Event to emit
        """
        # Store event in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Get subscribers
        subscribers = self._subscribers.get(event.event_type, [])
        
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                self._logger.error(f"Error in event subscriber: {e}", exc_info=True)
    
    def get_event_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """
        Get event history
        
        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        events = self._event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()



