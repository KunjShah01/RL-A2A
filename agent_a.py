"""
Agent A - Example implementation for A2A Protocol
Demonstrates autonomous agent behavior with the A2A communication system
"""

import asyncio
import websockets
import msgpack
import requests
import json
import time
import random
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque

@dataclass
class AgentState:
    """Represents the current state of the agent"""
    agent_id: str
    position: Dict[str, float]
    velocity: Dict[str, float]
    emotion: str
    energy: float = 100.0
    last_action: str = "idle"
    timestamp: float = 0.0

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class AgentClient:
    """Client for interacting with A2A server"""
    
    def __init__(self, agent_id: str, server_url: str = "http://localhost:8000", max_retries: int = 3):
        self.agent_id = agent_id
        self.server_url = server_url
        self.ws_url = server_url.replace("http", "ws")
        self.max_retries = max_retries
        self.session_id: Optional[str] = None
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        
        # Agent state
        self.state = AgentState(
            agent_id=agent_id,
            position={"x": float(random.uniform(-10, 10)), "y": float(random.uniform(-10, 10)), "z": 0.0},
            velocity={"x": 0.0, "y": 0.0, "z": 0.0},
            emotion="neutral"
        )
        
        # Learning and performance tracking
        self.action_history: deque = deque(maxlen=100)
        self.reward_history: deque = deque(maxlen=100)
        self.message_count = 0
        self.total_reward = 0.0
        self.is_running = False
        
        # Available actions
        self.actions = ["move_forward", "turn_left", "turn_right", "communicate", "observe"]
        
        print(f"🤖 Agent {self.agent_id} initialized")
    
    async def register(self) -> str:
        """Register agent with the A2A server"""
        try:
            print(f"📡 Registering {self.agent_id} with server...")
            
            response = requests.post(
                f"{self.server_url}/register",
                params={"agent_id": self.agent_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data["session_id"]
                print(f"✅ Registered successfully! Session ID: {self.session_id}")
                return self.session_id
            else:
                raise Exception(f"Registration failed: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to server: {e}")
    
    async def connect_websocket(self):
        """Connect to WebSocket for real-time communication"""
        if not self.session_id:
            raise Exception("Must register before connecting to WebSocket")
        
        ws_url = f"{self.ws_url}/ws/{self.session_id}"
        print(f"🔌 Connecting to WebSocket: {ws_url}")
        
        for attempt in range(self.max_retries):
            try:
                self.websocket = await websockets.connect(
                    ws_url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10
                )
                print(f"✅ WebSocket connected successfully")
                return
                
            except Exception as e:
                print(f"❌ WebSocket connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise Exception(f"Failed to connect to WebSocket after {self.max_retries} attempts")
    
    async def send_observation(self) -> Dict[str, Any]:
        """Send current observation to server and receive action"""
        if not self.websocket:
            raise Exception("WebSocket not connected")
        
        # Update timestamp
        self.state.timestamp = time.time()
        
        # Create observation message
        observation = {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "position": self.state.position,
            "velocity": self.state.velocity,
            "emotion": self.state.emotion,
            "energy": self.state.energy,
            "timestamp": self.state.timestamp,
            "message_count": self.message_count
        }
        
        try:
            # Send observation
            await self.websocket.send(json.dumps(observation, cls=NumpyEncoder))
            self.message_count += 1
            
            # Receive response
            response_data = await asyncio.wait_for(
                self.websocket.recv(), 
                timeout=5.0
            )
            response = json.loads(response_data)
            
            return response
            
        except asyncio.TimeoutError:
            raise Exception("Timeout waiting for server response")
        except Exception as e:
            raise Exception(f"Error in observation communication: {e}")
    
    def execute_action(self, action_command: str) -> float:
        """Execute the given action and return a reward"""
        reward = 0.0
        
        if action_command == "move_forward":
            # Move forward in current direction
            speed = 1.0
            self.state.position["x"] += speed * np.cos(np.radians(self.state.velocity.get("angle", 0)))
            self.state.position["y"] += speed * np.sin(np.radians(self.state.velocity.get("angle", 0)))
            self.state.energy -= 2.0
            reward = 0.1  # Small positive reward for action
            
        elif action_command == "turn_left":
            # Turn left
            current_angle = self.state.velocity.get("angle", 0)
            self.state.velocity["angle"] = (current_angle - 45) % 360
            self.state.energy -= 1.0
            reward = 0.05
            
        elif action_command == "turn_right":
            # Turn right
            current_angle = self.state.velocity.get("angle", 0)
            self.state.velocity["angle"] = (current_angle + 45) % 360
            self.state.energy -= 1.0
            reward = 0.05
            
        elif action_command == "communicate":
            # Communication action
            self.state.emotion = random.choice(["happy", "excited", "neutral"])
            self.state.energy -= 0.5
            reward = 0.2  # Higher reward for communication
            
        elif action_command == "observe":
            # Observation action (rest and recharge)
            self.state.energy += 5.0
            self.state.emotion = "calm"
            reward = 0.15
            
        else:
            # Unknown action
            reward = -0.1
        
        # Ensure energy stays within bounds
        self.state.energy = max(0.0, min(100.0, self.state.energy))
        
        # Boundary constraints (optional)
        if abs(self.state.position["x"]) > 20:
            self.state.position["x"] = np.sign(self.state.position["x"]) * 20
            reward -= 0.1
        if abs(self.state.position["y"]) > 20:
            self.state.position["y"] = np.sign(self.state.position["y"]) * 20
            reward -= 0.1
        
        # Energy penalty
        if self.state.energy < 10:
            reward -= 0.2
            self.state.emotion = "tired"
        
        # Update state
        self.state.last_action = action_command
        
        return reward
    
    async def send_feedback(self, reward: float, action_id: str, context: Optional[Dict] = None):
        """Send feedback to server for reinforcement learning"""
        if context is None:
            context = {
                "emotion": self.state.emotion,
                "energy": self.state.energy,
                "position": self.state.position
            }
        
        feedback_data = {
            "agent_id": self.agent_id,
            "action_id": action_id,
            "reward": reward,
            "context": context
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/feedback",
                json=feedback_data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"📊 Feedback sent: reward={reward:.3f}")
                return True
            else:
                print(f"❌ Feedback failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error sending feedback: {e}")
            return False
    
    async def run(self, iterations: int = 10):
        """Run the agent's main loop"""
        print(f"🚀 Starting {self.agent_id} for {iterations} iterations...")
        self.is_running = True
        
        try:
            # Register with server
            await self.register()
            
            # Connect to WebSocket
            await self.connect_websocket()
            
            # Main agent loop
            for i in range(iterations):
                if not self.is_running:
                    break
                
                print(f"\\n🔄 Iteration {i + 1}/{iterations}")
                
                try:
                    # Send observation and get action
                    response = await self.send_observation()
                    
                    if "command" in response:
                        action_command = response["command"]
                        action_id = response.get("action_id", f"action_{int(time.time())}")
                        
                        print(f"   📨 Received command: {action_command}")
                        
                        # Execute action
                        reward = self.execute_action(action_command)
                        
                        # Track performance
                        self.action_history.append(action_command)
                        self.reward_history.append(reward)
                        self.total_reward += reward
                        
                        print(f"   ⚡ Executed: {action_command}, Reward: {reward:.3f}")
                        print(f"   📍 Position: ({self.state.position['x']:.1f}, {self.state.position['y']:.1f})")
                        print(f"   😊 Emotion: {self.state.emotion}, Energy: {self.state.energy:.1f}")
                        
                        # Send feedback
                        await self.send_feedback(reward, action_id)
                        
                        # Print pending messages if any
                        if "pending_message" in response:
                            print(f"   💬 Pending message: {response['pending_message']}")
                    
                    # Small delay between iterations
                    await asyncio.sleep(1.0)
                    
                except Exception as e:
                    print(f"❌ Error in iteration {i + 1}: {e}")
                    continue
            
            print(f"\\n✅ {self.agent_id} completed {iterations} iterations")
            
        except Exception as e:
            print(f"❌ Agent run failed: {e}")
        
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up connections and resources"""
        print(f"🧹 Cleaning up {self.agent_id}...")
        
        if self.websocket:
            try:
                await self.websocket.close()
                print("✅ WebSocket connection closed")
            except Exception as e:
                print(f"⚠️ Error closing WebSocket: {e}")
        
        self.is_running = False
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze agent performance"""
        if not self.reward_history:
            return {"message": "No performance data available"}
        
        rewards = list(self.reward_history)
        actions = list(self.action_history)
        
        performance = {
            "total_reward": self.total_reward,
            "average_reward": np.mean(rewards),
            "std_reward": np.std(rewards),
            "max_reward": np.max(rewards),
            "min_reward": np.min(rewards),
            "total_actions": len(actions),
            "action_distribution": {action: actions.count(action) for action in set(actions)},
            "final_position": dict(self.state.position),
            "final_energy": self.state.energy,
            "final_emotion": self.state.emotion
        }
        
        return performance
    
    def stop(self):
        """Stop the agent"""
        print(f"🛑 Stopping {self.agent_id}...")
        self.is_running = False

# Example usage and execution
async def main():
    """Main function to run the agent"""
    agent = AgentClient("AgentA", "http://localhost:8000")
    
    try:
        # Run agent for specified iterations
        await agent.run(iterations=5)
        
        # Analyze performance
        performance = agent.analyze_performance()
        print(f"\\n📊 [{agent.agent_id} Performance Report]")
        print("=" * 50)
        print(f"Total Reward: {performance.get('total_reward', 0):.3f}")
        print(f"Average Reward: {performance.get('average_reward', 0):.3f}")
        print(f"Total Actions: {performance.get('total_actions', 0)}")
        print(f"Final Position: {performance.get('final_position', {})}")
        print(f"Final Energy: {performance.get('final_energy', 0):.1f}")
        print(f"Final Emotion: {performance.get('final_emotion', 'unknown')}")
        
        if "action_distribution" in performance:
            print("\\nAction Distribution:")
            for action, count in performance["action_distribution"].items():
                print(f"  {action}: {count}")
        
    except KeyboardInterrupt:
        print("\\n🛑 Agent stopped by user")
        agent.stop()
    except Exception as e:
        print(f"❌ Agent failed: {e}")
    
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    print("🎯 A2A Agent Client - Example Implementation")
    print("=" * 50)
    print("Make sure the A2A server is running before starting this agent!")
    print("Start server with: python a2a_server.py")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n👋 Goodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
