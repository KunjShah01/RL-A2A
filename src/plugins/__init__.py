"""
Plugins module - Plugin system for extensibility
"""

from .base import PluginInterface, PluginMetadata, PluginContext
from .cpa_plugin import CrossProtocolAdapterPlugin

__all__ = [
    "PluginInterface",
    "PluginMetadata",
    "PluginContext",
    "CrossProtocolAdapterPlugin",
]

