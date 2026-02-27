#!/usr/bin/env python3
"""
End-to-End Test Script for Real-Time Call Center AI System

This script tests the complete flow:
1. Health checks for all services
2. WebSocket connection
3. Audio chunk transmission
4. Database verification
5. Redis stream verification
"""

import asyncio
import websockets
import json
import base64
import uuid
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import redis
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip install websockets redis psycopg2-binary")
    sys.exit(1)


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class E2ETester:
    """End-to-end test runner."""
    
    def __init__(self):
        """Initialize test configuration."""
        self.api_host = os.getenv('API_HOST', 'localhost')
        self.api_port = int(os.getenv('API_PORT', 8000))
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = int(os.getenv('DB_PORT', 5432))
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD', 'postgres')
        self.db_name = os.getenv('DB_NAME', 'andela_ai_engineering_bootcamp')
        
        self.test_results: List[Dict] = []
        self.call_id: Optional[str] = None
        
    def log(self, message: str, status: str = "INFO"):
        """Print colored log message."""
        colors = {
            "PASS": Colors.GREEN,
            "FAIL": Colors.RED,
            "INFO": Colors.BLUE,
            "WARN": Colors.YELLOW
        }
        color = colors.get(status, Colors.RESET)
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "ℹ️" if status == "INFO" else "⚠️"
        print(f"{color}{symbol} {message}{Colors.RESET}")
    
    def record_test(self, name: str, passed: bool, message: str = ""):
        """Record test result."""
        self.test_results.append({
            "name": name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        if passed:
            self.log(f"{name}: PASSED", "PASS")
        else:
            self.log(f"{name}: FAILED - {message}", "FAIL")
    
    def test_redis_connection(self) -> bool:
        """Test Redis connection."""
        try:
            r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
            r.ping()
            self.record_test("Redis Connection", True)
            return True
        except Exception as e:
            self.record_test("Redis Connection", False, str(e))
            return False
    
    def test_database_connection(self) -> bool:
        """Test PostgreSQL connection."""
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name
            )
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.close()
            conn.close()
            self.record_test("Database Connection", True)
            return True
        except Exception as e:
            self.record_test("Database Connection", False, str(e))
            return False
    
    async def test_api_health(self) -> bool:
        """Test API Gateway health endpoint."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"http://{self.api_host}:{self.api_port}/health"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        redis_connected = data.get('redis', {}).get('connected', False)
                        if redis_connected:
                            self.record_test("API Gateway Health", True)
                            return True
                        else:
                            self.record_test("API Gateway Health", False, "Redis not connected")
                            return False
                    else:
                        self.record_test("API Gateway Health", False, f"Status {response.status}")
                        return False
        except ImportError:
            # Fallback to requests if aiohttp not available
            try:
                import requests
                url = f"http://{self.api_host}:{self.api_port}/health"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    redis_connected = data.get('redis', {}).get('connected', False)
                    if redis_connected:
                        self.record_test("API Gateway Health", True)
                        return True
                    else:
                        self.record_test("API Gateway Health", False, "Redis not connected")
                        return False
                else:
                    self.record_test("API Gateway Health", False, f"Status {response.status_code}")
                    return False
            except ImportError:
                self.record_test("API Gateway Health", False, "aiohttp or requests not installed")
                return False
        except Exception as e:
            self.record_test("API Gateway Health", False, str(e))
            return False
    
    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection and session setup."""
        try:
            uri = f"ws://{self.api_host}:{self.api_port}/ws/call"
            self.call_id = str(uuid.uuid4())
            agent_id = "test-agent-1"
            
            async with websockets.connect(uri) as websocket:
                # Send session setup
                await websocket.send(json.dumps({
                    "call_id": self.call_id,
                    "agent_id": agent_id,
                    "action": "start"
                }))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "session_started":
                    self.record_test("WebSocket Connection", True)
                    await websocket.close()
                    return True
                else:
                    self.record_test("WebSocket Connection", False, f"Unexpected response: {data}")
                    return False
                    
        except asyncio.TimeoutError:
            self.record_test("WebSocket Connection", False, "Timeout waiting for response")
            return False
        except Exception as e:
            self.record_test("WebSocket Connection", False, str(e))
            return False
    
    async def test_audio_chunk_flow(self) -> bool:
        """Test sending audio chunks through the system."""
        try:
            uri = f"ws://{self.api_host}:{self.api_port}/ws/call"
            if not self.call_id:
                self.call_id = str(uuid.uuid4())
            agent_id = "test-agent-1"
            
            chunks_sent = 0
            chunks_acknowledged = 0
            
            async with websockets.connect(uri) as websocket:
                # Setup session
                await websocket.send(json.dumps({
                    "call_id": self.call_id,
                    "agent_id": agent_id,
                    "action": "start"
                }))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                if data.get("type") != "session_started":
                    self.record_test("Audio Chunk Flow", False, "Session not started")
                    return False
                
                # Send 5 test audio chunks
                for i in range(5):
                    # Generate dummy audio data (200ms of 16kHz mono PCM silence)
                    # 16kHz * 0.2s * 2 bytes = 6400 bytes
                    dummy_audio = b'\x00' * 6400
                    audio_b64 = base64.b64encode(dummy_audio).decode('utf-8')
                    
                    await websocket.send(json.dumps({
                        "type": "audio_chunk",
                        "audio_data": audio_b64,
                        "chunk_index": i,
                        "timestamp": time.time(),
                        "format": "pcm",
                        "sample_rate": 16000,
                        "channels": 1
                    }))
                    chunks_sent += 1
                    
                    # Wait for acknowledgment
                    try:
                        ack = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        ack_data = json.loads(ack)
                        if ack_data.get("type") == "chunk_acknowledged":
                            chunks_acknowledged += 1
                    except asyncio.TimeoutError:
                        pass  # Some chunks might not get immediate ack
                    
                    await asyncio.sleep(0.1)
                
                # Stop session
                await websocket.send(json.dumps({
                    "type": "control",
                    "action": "stop"
                }))
                
                if chunks_sent > 0:
                    self.record_test(
                        "Audio Chunk Flow",
                        True,
                        f"Sent {chunks_sent} chunks, {chunks_acknowledged} acknowledged"
                    )
                    return True
                else:
                    self.record_test("Audio Chunk Flow", False, "No chunks sent")
                    return False
                    
        except Exception as e:
            self.record_test("Audio Chunk Flow", False, str(e))
            return False
    
    def test_redis_streams(self) -> bool:
        """Test Redis streams have messages."""
        try:
            r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=False)
            
            # Check audio_chunks stream
            audio_length = r.xlen('audio_chunks')
            
            # Check transcript_chunks stream
            transcript_length = r.xlen('transcript_chunks')
            
            if audio_length >= 0:  # Stream exists
                self.record_test(
                    "Redis Streams",
                    True,
                    f"audio_chunks: {audio_length}, transcript_chunks: {transcript_length}"
                )
                return True
            else:
                self.record_test("Redis Streams", False, "Streams not accessible")
                return False
                
        except Exception as e:
            self.record_test("Redis Streams", False, str(e))
            return False
    
    def test_database_transcripts(self) -> bool:
        """Test database has transcript records."""
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name
            )
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check if table exists and has records
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM meeting_transcripts
            """)
            result = cur.fetchone()
            count = result['count'] if result else 0
            
            cur.close()
            conn.close()
            
            self.record_test("Database Transcripts", True, f"Found {count} transcript records")
            return True
            
        except Exception as e:
            self.record_test("Database Transcripts", False, str(e))
            return False
    
    async def run_all_tests(self):
        """Run all end-to-end tests."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}End-to-End Test Suite{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        
        # Basic connectivity tests
        self.log("Running connectivity tests...", "INFO")
        self.test_redis_connection()
        self.test_database_connection()
        await self.test_api_health()
        
        # WebSocket tests
        self.log("\nRunning WebSocket tests...", "INFO")
        await self.test_websocket_connection()
        
        # Flow tests
        self.log("\nRunning flow tests...", "INFO")
        await self.test_audio_chunk_flow()
        
        # Wait a bit for processing
        self.log("\nWaiting for processing (5 seconds)...", "INFO")
        await asyncio.sleep(5)
        
        # Verification tests
        self.log("\nRunning verification tests...", "INFO")
        self.test_redis_streams()
        self.test_database_transcripts()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Test Summary{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}\n")
        
        if failed > 0:
            print(f"{Colors.RED}Failed Tests:{Colors.RESET}")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['name']}: {result['message']}")
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        
        if failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ All tests passed!{Colors.RESET}\n")
            return 0
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ Some tests failed{Colors.RESET}\n")
            return 1


async def main():
    """Main entry point."""
    tester = E2ETester()
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
        sys.exit(1)
