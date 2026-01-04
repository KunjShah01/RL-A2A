"""
Storage abstractions
"""

import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from pathlib import Path


class Storage(ABC):
    """Abstract storage interface"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set value by key"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    def list_keys(self, prefix: str = "") -> list:
        """List all keys with optional prefix"""
        pass


class MemoryStorage(Storage):
    """In-memory storage implementation"""
    
    def __init__(self):
        """Initialize memory storage"""
        self._data: Dict[str, Any] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        return self._data.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set value by key"""
        self._data[key] = value
    
    def delete(self, key: str) -> bool:
        """Delete key"""
        if key in self._data:
            del self._data[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return key in self._data
    
    def list_keys(self, prefix: str = "") -> list:
        """List all keys with optional prefix"""
        if prefix:
            return [k for k in self._data.keys() if k.startswith(prefix)]
        return list(self._data.keys())
    
    def clear(self) -> None:
        """Clear all data"""
        self._data.clear()


class FileStorage(Storage):
    """File-based storage implementation"""
    
    def __init__(self, base_path: str):
        """
        Initialize file storage
        
        Args:
            base_path: Base directory for storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_path(self, key: str) -> Path:
        """Get file path for key"""
        # Sanitize key to be filesystem-safe
        safe_key = key.replace('/', '_').replace('\\', '_')
        return self.base_path / f"{safe_key}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        path = self._get_path(key)
        if not path.exists():
            return None
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value by key"""
        path = self._get_path(key)
        with open(path, 'w') as f:
            json.dump(value, f, indent=2)
    
    def delete(self, key: str) -> bool:
        """Delete key"""
        path = self._get_path(key)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return self._get_path(key).exists()
    
    def list_keys(self, prefix: str = "") -> list:
        """List all keys with optional prefix"""
        keys = []
        for path in self.base_path.glob("*.json"):
            key = path.stem.replace('_', '/')
            if not prefix or key.startswith(prefix):
                keys.append(key)
        return keys

