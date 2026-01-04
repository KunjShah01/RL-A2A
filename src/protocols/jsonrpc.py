"""
JSON-RPC 2.0 Handler
Implementation of JSON-RPC 2.0 specification
"""

import json
import logging
from typing import Dict, Any, Optional, Union, Callable
from enum import Enum


class JSONRPCErrorCode(int, Enum):
    """JSON-RPC 2.0 error codes"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR = -32000


class JSONRPCError(Exception):
    """JSON-RPC 2.0 error"""
    
    def __init__(self, code: JSONRPCErrorCode, message: str, data: Any = None):
        """
        Initialize JSON-RPC error
        
        Args:
            code: Error code
            message: Error message
            data: Optional error data
        """
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to JSON-RPC error object"""
        error = {
            "code": self.code.value,
            "message": self.message,
        }
        if self.data is not None:
            error["data"] = self.data
        return error


class JSONRPCRequest:
    """JSON-RPC 2.0 request"""
    
    def __init__(self, method: str, params: Optional[Dict[str, Any]] = None, id: Optional[Union[str, int]] = None):
        """
        Initialize JSON-RPC request
        
        Args:
            method: Method name
            params: Method parameters
            id: Request ID
        """
        self.jsonrpc = "2.0"
        self.method = method
        self.params = params or {}
        self.id = id
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JSONRPCRequest":
        """Create request from dictionary"""
        if data.get("jsonrpc") != "2.0":
            raise JSONRPCError(JSONRPCErrorCode.INVALID_REQUEST, "Invalid JSON-RPC version")
        
        return cls(
            method=data.get("method", ""),
            params=data.get("params", {}),
            id=data.get("id"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary"""
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params,
        }
        if self.id is not None:
            result["id"] = self.id
        return result


class JSONRPCResponse:
    """JSON-RPC 2.0 response"""
    
    def __init__(self, result: Any = None, error: Optional[JSONRPCError] = None, id: Optional[Union[str, int]] = None):
        """
        Initialize JSON-RPC response
        
        Args:
            result: Result data (for success)
            error: Error object (for failure)
            id: Request ID
        """
        self.jsonrpc = "2.0"
        self.result = result
        self.error = error
        self.id = id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        response = {
            "jsonrpc": self.jsonrpc,
        }
        
        if self.error:
            response["error"] = self.error.to_dict()
        else:
            response["result"] = self.result
        
        if self.id is not None:
            response["id"] = self.id
        
        return response
    
    def to_json(self) -> str:
        """Convert response to JSON string"""
        return json.dumps(self.to_dict())


class JSONRPCHandler:
    """
    JSON-RPC 2.0 Handler
    
    Handles JSON-RPC 2.0 requests and routes to method handlers
    """
    
    def __init__(self):
        """Initialize JSON-RPC handler"""
        self._methods: Dict[str, Callable] = {}
        self._logger = logging.getLogger(__name__)
    
    def register_method(self, method_name: str, handler: Callable) -> None:
        """
        Register a method handler
        
        Args:
            method_name: Method name
            handler: Handler function (async or sync)
        """
        self._methods[method_name] = handler
        self._logger.debug(f"Registered JSON-RPC method: {method_name}")
    
    def unregister_method(self, method_name: str) -> None:
        """
        Unregister a method handler
        
        Args:
            method_name: Method name
        """
        if method_name in self._methods:
            del self._methods[method_name]
            self._logger.debug(f"Unregistered JSON-RPC method: {method_name}")
    
    async def handle_request(self, request_data: Union[str, Dict[str, Any]]) -> JSONRPCResponse:
        """
        Handle a JSON-RPC request
        
        Args:
            request_data: Request data (JSON string or dict)
            
        Returns:
            JSON-RPC response
        """
        # Parse request
        try:
            if isinstance(request_data, str):
                data = json.loads(request_data)
            else:
                data = request_data
            
            request = JSONRPCRequest.from_dict(data)
        except json.JSONDecodeError:
            return JSONRPCResponse(
                error=JSONRPCError(JSONRPCErrorCode.PARSE_ERROR, "Parse error"),
                id=None
            )
        except JSONRPCError as e:
            return JSONRPCResponse(error=e, id=data.get("id"))
        except Exception as e:
            return JSONRPCResponse(
                error=JSONRPCError(JSONRPCErrorCode.INVALID_REQUEST, str(e)),
                id=data.get("id") if isinstance(data, dict) else None
            )
        
        # Handle notification (no id)
        if request.id is None:
            await self._handle_notification(request)
            return None  # Notifications don't return responses
        
        # Find handler
        handler = self._methods.get(request.method)
        if not handler:
            return JSONRPCResponse(
                error=JSONRPCError(JSONRPCErrorCode.METHOD_NOT_FOUND, f"Method not found: {request.method}"),
                id=request.id
            )
        
        # Call handler
        try:
            import asyncio
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**request.params)
            else:
                result = handler(**request.params)
            
            return JSONRPCResponse(result=result, id=request.id)
        
        except TypeError as e:
            return JSONRPCResponse(
                error=JSONRPCError(JSONRPCErrorCode.INVALID_PARAMS, f"Invalid parameters: {str(e)}"),
                id=request.id
            )
        except Exception as e:
            self._logger.error(f"Error handling method {request.method}: {e}", exc_info=True)
            return JSONRPCResponse(
                error=JSONRPCError(JSONRPCErrorCode.INTERNAL_ERROR, f"Internal error: {str(e)}"),
                id=request.id
            )
    
    async def _handle_notification(self, request: JSONRPCRequest) -> None:
        """
        Handle a notification (request without ID)
        
        Args:
            request: JSON-RPC request
        """
        handler = self._methods.get(request.method)
        if handler:
            try:
                import asyncio
                if asyncio.iscoroutinefunction(handler):
                    await handler(**request.params)
                else:
                    handler(**request.params)
            except Exception as e:
                self._logger.error(f"Error handling notification {request.method}: {e}", exc_info=True)
    
    async def handle_batch(self, batch_data: Union[str, list]) -> list:
        """
        Handle a batch of JSON-RPC requests
        
        Args:
            batch_data: Batch request data (JSON string or list)
            
        Returns:
            List of JSON-RPC responses (None for notifications)
        """
        try:
            if isinstance(batch_data, str):
                requests_data = json.loads(batch_data)
            else:
                requests_data = batch_data
            
            if not isinstance(requests_data, list):
                # Single request, not a batch
                response = await self.handle_request(requests_data)
                return [response] if response else []
            
            # Process batch
            responses = []
            for request_data in requests_data:
                response = await self.handle_request(request_data)
                if response:
                    responses.append(response)
            
            return responses
        
        except Exception as e:
            self._logger.error(f"Error handling batch: {e}", exc_info=True)
            return [
                JSONRPCResponse(
                    error=JSONRPCError(JSONRPCErrorCode.PARSE_ERROR, str(e)),
                    id=None
                )
            ]



