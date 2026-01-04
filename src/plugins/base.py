"""
Plugin base classes
Compatible with existing plugin system
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

# Re-export from existing plugin system for compatibility
try:
    from plugins.plugin_system import PluginInterface, PluginMetadata, PluginContext
except ImportError:
    # Fallback definitions if plugin system not available
    @dataclass
    class PluginMetadata:
        """Plugin metadata structure"""
        name: str
        version: str
        description: str
        author: str
        dependencies: list
        entry_point: str
        permissions: list
        category: str
        tags: list
        min_rla2a_version: str = "2.0.0"
        enabled: bool = True
    
    class PluginInterface(ABC):
        """Base interface for all plugins"""
        
        @abstractmethod
        async def initialize(self, context: Dict[str, Any]) -> bool:
            """Initialize the plugin"""
            pass
        
        @abstractmethod
        async def execute(self, *args, **kwargs) -> Any:
            """Execute plugin functionality"""
            pass
        
        @abstractmethod
        async def cleanup(self) -> bool:
            """Cleanup plugin resources"""
            pass
        
        @property
        @abstractmethod
        def metadata(self) -> PluginMetadata:
            """Plugin metadata"""
            pass
    
    class PluginContext:
        """Plugin execution context"""
        def __init__(self, plugin_manager=None):
            self.plugin_manager = plugin_manager
            self.shared_data = {}



