#!/usr/bin/env python3
"""
Smile-Activated Robot Controller
WebSocket server that receives smile detection events and triggers robot movements
"""

import asyncio
import websockets
import json
import time
import threading
import os
from datetime import datetime
from pylx16a.lx16a import *
from config import ALL_SERVOS, REVERSED

# ===== CONFIGURATION =====
WEBSOCKET_PORT = 8765
ROBOT_PORT = "COM6"  # Update with your serial port

# Robot action sequences (define your movements here)
ROBOT_SEQUENCES = {
    'wave': 'wave.csv',
    'nod': 'nod.csv', 
    'dance': 'dance.csv',
    'happy': 'happy.csv',
    'custom': 'custom.csv'
}

# ===========================

class RobotController:
    """Handles robot servo control and movement sequences"""
    
    def __init__(self):
        self.servos = {}
        self.is_moving = False
        self.current_action = None
        self.connected = False
        
    def connect(self):
        """Connect to robot servos"""
        try:
            print(f"🤖 Connecting to robot on {ROBOT_PORT}...")
            LX16A.initialize(ROBOT_PORT)
            
            for sid in ALL_SERVOS:
                try:
                    s = LX16A(sid)
                    s.enable_torque()
                    self.servos[sid] = s
                    print(f"  ✅ Servo {sid} connected")
                except Exception as e:
                    print(f"  ⚠️ Servo {sid} failed: {e}")
            
            self.connected = len(self.servos) > 0
            if self.connected:
                print(f"🎯 Robot ready! ({len(self.servos)} servos connected)")
                self.set_home_position()
            else:
                print("❌ No servos connected!")
            
            return self.connected
            
        except Exception as e:
            print(f"❌ Robot connection failed: {e}")
            self.connected = False
            return False
    
    def set_home_position(self):
        """Move robot to home/neutral position"""
        if not self.connected:
            return
        
        print("🏠 Setting home position...")
        for sid, servo in self.servos.items():
            try:
                servo.move(120)  # Center position
            except:
                pass
    
    def play_sequence(self, sequence_name):
        """Play a pre-recorded movement sequence"""
        if not self.connected or self.is_moving:
            return False
        
        # Check if sequence file exists
        seq_file = os.path.join("poses", ROBOT_SEQUENCES.get(sequence_name, f"{sequence_name}.csv"))
        
        if not os.path.exists(seq_file):
            print(f"⚠️ Sequence file not found: {seq_file}")
            return False
        
        # Start movement in separate thread to avoid blocking
        thread = threading.Thread(target=self._play_sequence_thread, args=(seq_file, sequence_name))
        thread.daemon = True
        thread.start()
        
        return True
    
    def _play_sequence_thread(self, seq_file, name):
        """Thread function to play sequence without blocking"""
        try:
            self.is_moving = True
            self.current_action = name
            print(f"▶️ Playing sequence: {name}")
            
            # Load sequence from CSV
            import csv
            frames = {}
            
            with open(seq_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    frame = int(row['frame'])
                    sid = int(row['servo_id'])
                    angle = float(row['angle'])
                    
                    if sid in REVERSED:
                        angle = 240 - angle
                    
                    if frame not in frames:
                        frames[frame] = {}
                    frames[frame][sid] = angle
            
            # Play frames with simple interpolation
            frame_numbers = sorted(frames.keys())
            
            for i, frame_num in enumerate(frame_numbers):
                frame_data = frames[frame_num]
                
                # Move all servos for this frame
                for sid, angle in frame_data.items():
                    if sid in self.servos:
                        try:
                            self.servos[sid].move(angle)
                        except:
                            pass
                
                # Wait between frames (adjust for speed)
                if i < len(frame_numbers) - 1:
                    time.sleep(0.5)  # 500ms between frames
            
            print(f"✅ Sequence '{name}' completed")
            
            # Return to home position after sequence
            time.sleep(0.5)
            self.set_home_position()
            
        except Exception as e:
            print(f"❌ Error playing sequence: {e}")
        finally:
            self.is_moving = False
            self.current_action = None
    
    def simple_wave(self):
        """Perform a simple wave motion (no CSV needed)"""
        if not self.connected or self.is_moving:
            return
        
        try:
            self.is_moving = True
            self.current_action = "wave"
            print("👋 Performing wave...")
            
            # Simple wave motion (adjust servo IDs and angles as needed)
            # This is an example - modify based on your robot configuration
            
            # Assuming servo 1 is shoulder, servo 2 is elbow
            if 1 in self.servos:
                self.servos[1].move(180)  # Raise arm
            if 2 in self.servos:
                self.servos[2].move(90)   # Bend elbow
            
            time.sleep(0.3)
            
            # Wave motion
            for _ in range(3):
                if 2 in self.servos:
                    self.servos[2].move(60)
                time.sleep(0.3)
                if 2 in self.servos:
                    self.servos[2].move(120)
                time.sleep(0.3)
            
            # Return to home
            time.sleep(0.5)
            self.set_home_position()
            
            print("✅ Wave completed")
            
        except Exception as e:
            print(f"❌ Wave error: {e}")
        finally:
            self.is_moving = False
            self.current_action = None
    
    def simple_nod(self):
        """Perform a simple nod motion"""
        if not self.connected or self.is_moving:
            return
        
        try:
            self.is_moving = True
            self.current_action = "nod"
            print("🙆 Performing nod...")
            
            # Assuming servo 3 controls head tilt
            if 3 in self.servos:
                for _ in range(3):
                    self.servos[3].move(100)  # Tilt down
                    time.sleep(0.3)
                    self.servos[3].move(140)  # Tilt up
                    time.sleep(0.3)
                
                self.servos[3].move(120)  # Center
            
            print("✅ Nod completed")
            
        except Exception as e:
            print(f"❌ Nod error: {e}")
        finally:
            self.is_moving = False
            self.current_action = None
    
    def simple_dance(self):
        """Perform a simple dance motion"""
        if not self.connected or self.is_moving:
            return
        
        try:
            self.is_moving = True
            self.current_action = "dance"
            print("💃 Performing dance...")
            
            # Simple dance - move multiple servos rhythmically
            positions = [
                {1: 100, 2: 100, 3: 100},
                {1: 140, 2: 140, 3: 140},
                {1: 100, 2: 140, 3: 100},
                {1: 140, 2: 100, 3: 140},
            ]
            
            for _ in range(2):  # Repeat twice
                for pos in positions:
                    for sid, angle in pos.items():
                        if sid in self.servos:
                            try:
                                self.servos[sid].move(angle)
                            except:
                                pass
                    time.sleep(0.4)
            
            # Return to home
            self.set_home_position()
            
            print("✅ Dance completed")
            
        except Exception as e:
            print(f"❌ Dance error: {e}")
        finally:
            self.is_moving = False
            self.current_action = None
    
    def emergency_stop(self):
        """Emergency stop - disable all servos"""
        print("🛑 EMERGENCY STOP!")
        self.is_moving = False
        
        for servo in self.servos.values():
            try:
                servo.disable_torque()
            except:
                pass
        
        # Re-enable after 1 second
        time.sleep(1)
        for servo in self.servos.values():
            try:
                servo.enable_torque()
            except:
                pass
    
    def disconnect(self):
        """Disconnect from robot"""
        print("🔌 Disconnecting robot...")
        
        for servo in self.servos.values():
            try:
                servo.disable_torque()
            except:
                pass
        
        try:
            LX16A._controller.close()
        except:
            pass
        
        self.connected = False
        print("✅ Robot disconnected")


class SmileRobotServer:
    """WebSocket server for smile-activated robot control"""
    
    def __init__(self):
        self.robot = RobotController()
        self.clients = set()
        self.stats = {
            'total_smiles': 0,
            'total_movements': 0,
            'start_time': datetime.now(),
            'last_smile': None
        }
    
    async def handle_client(self, connection):
        """Handle WebSocket client connections.

        Note: newer `websockets` versions call the handler with a single
        ServerConnection-like object. We accept that object here and treat it
        similarly to the older `websocket` name used elsewhere.
        """
        # Add client to set
        self.clients.add(connection)
        client_addr = getattr(connection, "remote_address", None)
        print(f"📱 Client connected: {client_addr}")

        # Send initial status
        await self.send_status(connection)

        try:
            async for message in connection:
                await self.process_message(connection, message)

        except websockets.exceptions.ConnectionClosed:
            print(f"📱 Client disconnected: {client_addr}")
        except Exception as e:
            print(f"❌ Client error: {e}")
        finally:
            try:
                self.clients.remove(connection)
            except KeyError:
                pass
    
    async def process_message(self, connection, message):
        """Process incoming WebSocket messages"""
        try:
            data = json.loads(message)
            command = data.get('command')
            
            print(f"📨 Received: {command}")
            
            if command == 'smile_detected':
                await self.handle_smile(connection, data)
                
            elif command == 'test_action':
                await self.handle_test_action(connection, data)
                
            elif command == 'get_status':
                await self.send_status(connection)
                
            else:
                await connection.send(json.dumps({
                    'error': f'Unknown command: {command}'
                }))
                
        except json.JSONDecodeError:
            await connection.send(json.dumps({
                'error': 'Invalid JSON'
            }))
        except Exception as e:
            print(f"❌ Message processing error: {e}")
            await connection.send(json.dumps({
                'error': str(e)
            }))
    
    async def handle_smile(self, connection, data):
        """Handle smile detection event"""
        smile_score = data.get('smile_score', 0)
        action = data.get('action', 'wave')
        
        self.stats['total_smiles'] += 1
        self.stats['last_smile'] = datetime.now()
        
        print(f"😊 Smile detected! Score: {smile_score:.1f}%, Action: {action}")
        
        # Trigger robot action if not already moving
        if not self.robot.is_moving:
            success = await self.trigger_robot_action(action)
            
            if success:
                self.stats['total_movements'] += 1
                
                # Send confirmation to all clients
                response = {
                    'message': f'Robot performing: {action}',
                    'status': 'Moving',
                    'smile_score': smile_score,
                    'total_movements': self.stats['total_movements']
                }
            else:
                response = {
                    'message': 'Robot is busy or action failed',
                    'status': 'Busy'
                }
        else:
            response = {
                'message': 'Robot is already moving',
                'status': 'Busy'
            }
        
        # Send response to all connected clients
        await self.broadcast(json.dumps(response))
    
    async def handle_test_action(self, connection, data):
        """Handle test action request"""
        action = data.get('action', 'wave')
        
        print(f"🧪 Test action requested: {action}")
        
        if action == 'stop':
            self.robot.emergency_stop()
            response = {
                'message': 'Emergency stop activated',
                'status': 'Stopped'
            }
        else:
            success = await self.trigger_robot_action(action)

            if success:
                response = {
                    'message': f'Testing: {action}',
                    'status': 'Moving'
                }
            else:
                response = {
                    'message': f'Failed to perform: {action}',
                    'status': 'Error'
                }

        await connection.send(json.dumps(response))
    
    async def trigger_robot_action(self, action):
        """Trigger robot action based on type"""
        if not self.robot.connected:
            print("⚠️ Robot not connected!")
            return False
        
        # Run robot action in separate thread to avoid blocking
        def run_action():
            if action == 'wave':
                # Try CSV sequence first, fall back to simple motion
                if not self.robot.play_sequence('wave'):
                    self.robot.simple_wave()
                    
            elif action == 'nod':
                if not self.robot.play_sequence('nod'):
                    self.robot.simple_nod()
                    
            elif action == 'dance':
                if not self.robot.play_sequence('dance'):
                    self.robot.simple_dance()
                    
            elif action == 'custom':
                self.robot.play_sequence('custom')
                
            else:
                # Try to play as sequence name
                self.robot.play_sequence(action)
        
        thread = threading.Thread(target=run_action)
        thread.daemon = True
        thread.start()
        
        return True
    
    async def send_status(self, connection):
        """Send current status to client"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        status = {
            'robot_connected': self.robot.connected,
            'is_moving': self.robot.is_moving,
            'current_action': self.robot.current_action,
            'total_smiles': self.stats['total_smiles'],
            'total_movements': self.stats['total_movements'],
            'uptime': uptime,
            'servos_connected': len(self.robot.servos)
        }
        
        await connection.send(json.dumps({
            'message': 'Status update',
            'status': status
        }))
    
    async def broadcast(self, message):
        """Broadcast message to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )
    
    async def start_server(self):
        """Start the WebSocket server"""
        print("\n" + "="*60)
        print("🚀 SMILE-ACTIVATED ROBOT SERVER")
        print("="*60)
        
        # Connect to robot
        if not self.robot.connect():
            print("\n⚠️ WARNING: Robot not connected!")
            print("Server will run but robot actions won't work.")
            print("Check your serial port and robot connection.\n")
        
        # Start WebSocket server
        print(f"🌐 Starting WebSocket server on port {WEBSOCKET_PORT}...")
        
        async with websockets.serve(self.handle_client, 'localhost', WEBSOCKET_PORT):
            print(f"✅ Server running at ws://localhost:{WEBSOCKET_PORT}")
            print("\n📱 Open 'smile_robot_control.html' in your browser")
            print("😊 Smile to make the robot move!")
            print("\nPress Ctrl+C to stop the server\n")
            print("-"*60 + "\n")
            
            # Keep server running
            await asyncio.Future()  # run forever
    
    def cleanup(self):
        """Cleanup on shutdown"""
        print("\n🛑 Shutting down server...")
        self.robot.disconnect()
        print("✅ Server stopped")


async def main():
    """Main entry point"""
    server = SmileRobotServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        print("\n⏹️ Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
    finally:
        server.cleanup()


if __name__ == "__main__":
    # Run the server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")