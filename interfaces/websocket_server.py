"""
WebSocket server for real-time agent communication
"""
import asyncio
import json
from typing import Set, Dict, Any
import websockets
from websockets.server import WebSocketServerProtocol
from core.events import event_bus, EventType, Event
from agents.orchestrator import orchestrator
from tools.registry import registry
from utils import get_logger
from app_config import config

logger = get_logger(__name__)


class WebSocketServer:
    """WebSocket server for Nexus EVO"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.client_subscriptions: Dict[WebSocketServerProtocol, Set[str]] = {}
        
        # Subscribe to all events
        for event_type in EventType:
            event_bus.subscribe_async(event_type, self.broadcast_event)
        
        logger.info(f"WebSocket server initialized on {host}:{port}")
    
    async def broadcast_event(self, event: Event):
        """Broadcast event to all connected clients"""
        if not self.clients:
            return
        
        message = json.dumps({
            "type": "event",
            "event": event.to_dict()
        })
        
        # Send to all clients (or filtered by subscription)
        disconnected = set()
        for client in self.clients:
            try:
                # Check if client subscribed to this event type
                subscriptions = self.client_subscriptions.get(client, set())
                if not subscriptions or event.type.value in subscriptions:
                    await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Clean up disconnected clients
        self.clients -= disconnected
        for client in disconnected:
            self.client_subscriptions.pop(client, None)
    
    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Handle individual client connection"""
        client_id = id(websocket)
        logger.info(f"Client connected: {client_id}")
        
        # Register client
        self.clients.add(websocket)
        self.client_subscriptions[websocket] = set()
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connected",
            "message": "Connected to Nexus EVO",
            "tools": len(registry.list_tools())
        }))
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        finally:
            self.clients.discard(websocket)
            self.client_subscriptions.pop(websocket, None)
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "execute_task":
                await self.execute_task(websocket, data)
            
            elif msg_type == "get_status":
                await self.send_status(websocket)
            
            elif msg_type == "get_tools":
                await self.send_tools(websocket)
            
            elif msg_type == "get_history":
                await self.send_history(websocket, data)
            
            elif msg_type == "subscribe":
                self.subscribe_client(websocket, data.get("events", []))
            
            elif msg_type == "unsubscribe":
                self.unsubscribe_client(websocket, data.get("events", []))
            
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": f"Unknown message type: {msg_type}"
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "error": "Invalid JSON"
            }))
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "error": str(e)
            }))
    
    async def execute_task(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Execute a task and stream updates"""
        task = data.get("task")
        if not task:
            await websocket.send(json.dumps({
                "type": "error",
                "error": "No task provided"
            }))
            return
        
        # Send acknowledgment
        await websocket.send(json.dumps({
            "type": "task_accepted",
            "task": task
        }))
        
        # Execute task (events will be broadcast automatically)
        try:
            result = orchestrator.execute(task)
            
            # Send final result
            await websocket.send(json.dumps({
                "type": "task_result",
                "task": task,
                "result": result
            }))
            
        except Exception as e:
            await websocket.send(json.dumps({
                "type": "task_error",
                "task": task,
                "error": str(e)
            }))
    
    async def send_status(self, websocket: WebSocketServerProtocol):
        """Send agent status"""
        status = orchestrator.get_status()
        await websocket.send(json.dumps({
            "type": "status",
            "status": status
        }))
    
    async def send_tools(self, websocket: WebSocketServerProtocol):
        """Send available tools"""
        tools = registry.get_all_tools_info()
        await websocket.send(json.dumps({
            "type": "tools",
            "tools": tools
        }))
    
    async def send_history(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Send event history"""
        limit = data.get("limit", 100)
        event_type_str = data.get("event_type")
        
        event_type = None
        if event_type_str:
            try:
                event_type = EventType(event_type_str)
            except ValueError:
                pass
        
        history = event_bus.get_history(event_type, limit)
        
        await websocket.send(json.dumps({
            "type": "history",
            "events": [e.to_dict() for e in history]
        }))
    
    def subscribe_client(self, websocket: WebSocketServerProtocol, events: list):
        """Subscribe client to specific event types"""
        if websocket in self.client_subscriptions:
            self.client_subscriptions[websocket].update(events)
    
    def unsubscribe_client(self, websocket: WebSocketServerProtocol, events: list):
        """Unsubscribe client from event types"""
        if websocket in self.client_subscriptions:
            self.client_subscriptions[websocket] -= set(events)
    
    async def start(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever
    
    def run(self):
        """Run the server (blocking)"""
        asyncio.run(self.start())


# Global WebSocket server instance
websocket_server = WebSocketServer()


# Convenience function to run in background thread
def run_websocket_server_thread():
    """Run WebSocket server in a separate thread"""
    import threading
    thread = threading.Thread(target=websocket_server.run, daemon=True)
    thread.start()
    logger.info("WebSocket server started in background thread")
    return thread
