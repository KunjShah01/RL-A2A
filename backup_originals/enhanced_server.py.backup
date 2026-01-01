"""
Enhanced RL-A2A Server with Live Features
========================================

Enhanced version of the main server integrating:
- Agent Marketplace
- Advanced Analytics  
- Plugin System
- Live Dashboard
- Real-time monitoring

Author: KUNJ SHAH
Version: 3.1.0 Enhanced Live
"""

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# FastAPI and dependencies
from fastapi import FastAPI, WebSocket, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import live integration
from live_integration import LiveIntegration, create_live_api_routes

class EnhancedRLA2AServer:
    """Enhanced RL-A2A Server with live features"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.app = FastAPI(
            title="RL-A2A Enhanced Server",
            description="Agent-to-Agent Communication with Live Features",
            version="3.1.0"
        )
        
        # Live integration
        self.live_integration = LiveIntegration(config)
        
        # WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()
        self._setup_static_files()
        
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_static_files(self):
        """Setup static file serving"""
        # Create static directories if they don't exist
        Path("static").mkdir(exist_ok=True)
        Path("frontend").mkdir(exist_ok=True)
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        self.app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return await self.live_integration.health_check()
        
        # Main page
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Serve main page"""
            try:
                with open("index.html", "r") as f:
                    return HTMLResponse(content=f.read())
            except FileNotFoundError:
                return HTMLResponse(content="""
                <html>
                    <head><title>RL-A2A Server</title></head>
                    <body>
                        <h1>RL-A2A Enhanced Server</h1>
                        <p>Server is running successfully!</p>
                        <p><a href="/dashboard">Go to Dashboard</a></p>
                        <p><a href="/docs">API Documentation</a></p>
                    </body>
                </html>
                """)
        
        # Dashboard
        @self.app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard():
            """Serve live dashboard"""
            try:
                with open("frontend/dashboard.html", "r") as f:
                    return HTMLResponse(content=f.read())
            except FileNotFoundError:
                return HTMLResponse(content="""
                <html>
                    <head><title>Dashboard Not Found</title></head>
                    <body>
                        <h1>Dashboard Not Available</h1>
                        <p>The dashboard file is not found. Please check the deployment.</p>
                        <p><a href="/">Back to Home</a></p>
                    </body>
                </html>
                """)
        
        # WebSocket endpoint for real-time updates
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication"""
            await self.connect_websocket(websocket)
            try:
                while True:
                    # Wait for messages from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle different message types
                    response = await self.handle_websocket_message(message)
                    
                    # Send response back
                    await websocket.send_text(json.dumps(response))
                    
            except Exception as e:
                print(f"WebSocket error: {e}")
            finally:
                await self.disconnect_websocket(websocket)
        
        # Agent interaction endpoint
        @self.app.post("/api/agents/interact")
        async def agent_interact(request: Dict[str, Any]):
            """Handle agent interactions"""
            try:
                agent_id = request.get("agent_id")
                user_id = request.get("user_id", "anonymous")
                session_id = request.get("session_id", str(uuid.uuid4()))
                message = request.get("message", "")
                
                # Track interaction
                interaction_data = {
                    "message": message,
                    "response_time": 0.5,  # Simulated
                    "success": True
                }
                
                await self.live_integration.track_agent_interaction(
                    agent_id, user_id, session_id, interaction_data
                )
                
                # Simulate agent response
                response = {
                    "agent_id": agent_id,
                    "response": f"Agent {agent_id} processed: {message}",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id
                }
                
                # Broadcast to WebSocket clients
                await self.broadcast_to_websockets({
                    "type": "agent_interaction",
                    "data": response
                })
                
                return response
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Create live API routes
        create_live_api_routes(self.app, self.live_integration)
        
        # Additional utility endpoints
        @self.app.get("/api/status")
        async def get_status():
            """Get server status"""
            return {
                "status": "running",
                "version": "3.1.0",
                "timestamp": datetime.now().isoformat(),
                "features": {
                    "marketplace": True,
                    "analytics": True,
                    "plugins": True,
                    "live_dashboard": True
                },
                "active_connections": len(self.active_connections)
            }
        
        @self.app.post("/api/export/{data_type}")
        async def export_data(data_type: str):
            """Export system data"""
            try:
                data = await self.live_integration.export_data(data_type)
                return {"data": data, "timestamp": datetime.now().isoformat()}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def connect_websocket(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send welcome message with current dashboard data
        dashboard_data = await self.live_integration.get_live_dashboard_data()
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "data": dashboard_data
        }))
    
    async def disconnect_websocket(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def handle_websocket_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming WebSocket messages"""
        message_type = message.get("type")
        
        if message_type == "get_dashboard":
            data = await self.live_integration.get_live_dashboard_data()
            return {"type": "dashboard_data", "data": data}
        
        elif message_type == "search_marketplace":
            query = message.get("query", "")
            category = message.get("category", "")
            tags = message.get("tags", [])
            
            results = await self.live_integration.search_marketplace(query, category, tags)
            return {"type": "marketplace_results", "data": results}
        
        elif message_type == "plugin_action":
            action = message.get("action")
            plugin_name = message.get("plugin_name")
            
            if action == "load":
                success = await self.live_integration.load_plugin(plugin_name)
            elif action == "unload":
                success = await self.live_integration.unload_plugin(plugin_name)
            else:
                success = False
            
            return {"type": "plugin_action_result", "data": {"success": success, "action": action, "plugin": plugin_name}}
        
        else:
            return {"type": "error", "data": {"message": "Unknown message type"}}
    
    async def broadcast_to_websockets(self, message: Dict[str, Any]):
        """Broadcast message to all connected WebSocket clients"""
        if self.active_connections:
            message_str = json.dumps(message)
            for connection in self.active_connections.copy():
                try:
                    await connection.send_text(message_str)
                except:
                    # Remove disconnected clients
                    self.active_connections.remove(connection)
    
    async def start_background_tasks(self):
        """Start background tasks"""
        # Initialize live integration
        await self.live_integration.initialize()
        
        # Start real-time update task
        asyncio.create_task(self.real_time_update_task())
    
    async def real_time_update_task(self):
        """Background task for real-time updates"""
        while True:
            try:
                # Get latest dashboard data
                dashboard_data = await self.live_integration.get_live_dashboard_data()
                
                # Broadcast to all connected clients
                await self.broadcast_to_websockets({
                    "type": "dashboard_update",
                    "data": dashboard_data
                })
                
                # Wait 30 seconds before next update
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"Real-time update error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Run the enhanced server"""
        print(f"""
🚀 RL-A2A Enhanced Server Starting...
=====================================

🌐 Server URL: http://{host}:{port}
📊 Dashboard: http://{host}:{port}/dashboard
📚 API Docs: http://{host}:{port}/docs
🔌 WebSocket: ws://{host}:{port}/ws

Features Enabled:
✅ Agent Marketplace
✅ Advanced Analytics
✅ Plugin System
✅ Live Dashboard
✅ Real-time Updates

Ready for production use! 🎉
        """)
        
        # Start background tasks
        asyncio.create_task(self.start_background_tasks())
        
        # Run server
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            **kwargs
        )

# CLI interface
def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RL-A2A Enhanced Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    
    args = parser.parse_args()
    
    # Create and run server
    server = EnhancedRLA2AServer()
    
    server.run(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )

if __name__ == "__main__":
    main()