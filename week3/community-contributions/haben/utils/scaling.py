"""
Utilities for horizontal scaling of workers.
"""

import os
import logging
import redis
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)


class WorkerRegistry:
    """Registry for tracking worker instances for load balancing."""
    
    def __init__(self):
        """Initialize worker registry."""
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        self.registry_key = os.getenv('WORKER_REGISTRY_KEY', 'workers:registry')
        self.heartbeat_interval = int(os.getenv('WORKER_HEARTBEAT_INTERVAL', '30'))  # seconds
        self.worker_ttl = int(os.getenv('WORKER_TTL', '60'))  # seconds
    
    def register_worker(self, worker_id: str, worker_type: str, capacity: int = 1):
        """
        Register a worker instance.
        
        Args:
            worker_id: Unique worker identifier
            worker_type: Type of worker (audio_processor, llm_processor)
            capacity: Worker capacity (concurrent calls)
        """
        try:
            worker_data = {
                'id': worker_id,
                'type': worker_type,
                'capacity': capacity,
                'status': 'active',
                'registered_at': str(os.getenv('WORKER_START_TIME', ''))
            }
            
            key = f"{self.registry_key}:{worker_type}:{worker_id}"
            self.redis_client.hset(key, mapping=worker_data)
            self.redis_client.expire(key, self.worker_ttl)
            
            logger.info(f"Registered worker: {worker_id} ({worker_type})")
        except Exception as e:
            logger.error(f"Error registering worker: {e}")
    
    def update_heartbeat(self, worker_id: str, worker_type: str):
        """Update worker heartbeat to indicate it's alive."""
        try:
            key = f"{self.registry_key}:{worker_type}:{worker_id}"
            self.redis_client.hset(key, 'last_heartbeat', str(os.getenv('CURRENT_TIME', '')))
            self.redis_client.expire(key, self.worker_ttl)
        except Exception as e:
            logger.error(f"Error updating heartbeat: {e}")
    
    def get_active_workers(self, worker_type: str) -> List[Dict]:
        """
        Get list of active workers of a specific type.
        
        Args:
            worker_type: Type of worker
            
        Returns:
            List of worker dictionaries
        """
        try:
            pattern = f"{self.registry_key}:{worker_type}:*"
            keys = self.redis_client.keys(pattern)
            
            workers = []
            for key in keys:
                worker_data = self.redis_client.hgetall(key)
                if worker_data:
                    workers.append(worker_data)
            
            return workers
        except Exception as e:
            logger.error(f"Error getting active workers: {e}")
            return []
    
    def unregister_worker(self, worker_id: str, worker_type: str):
        """Unregister a worker instance."""
        try:
            key = f"{self.registry_key}:{worker_type}:{worker_id}"
            self.redis_client.delete(key)
            logger.info(f"Unregistered worker: {worker_id}")
        except Exception as e:
            logger.error(f"Error unregistering worker: {e}")


class LoadBalancer:
    """Simple load balancer for distributing work across workers."""
    
    def __init__(self, worker_type: str):
        """
        Initialize load balancer.
        
        Args:
            worker_type: Type of workers to balance
        """
        self.worker_type = worker_type
        self.registry = WorkerRegistry()
        self.current_worker_index = 0
    
    def get_next_worker(self) -> Dict:
        """
        Get next available worker using round-robin.
        
        Returns:
            Worker dictionary or None
        """
        workers = self.registry.get_active_workers(self.worker_type)
        
        if not workers:
            return None
        
        # Round-robin selection
        worker = workers[self.current_worker_index % len(workers)]
        self.current_worker_index += 1
        
        return worker
    
    def get_least_loaded_worker(self) -> Dict:
        """
        Get worker with least current load.
        
        Returns:
            Worker dictionary or None
        """
        workers = self.registry.get_active_workers(self.worker_type)
        
        if not workers:
            return None
        
        # Sort by capacity (assuming lower capacity = less loaded)
        # In production, track actual load metrics
        workers.sort(key=lambda w: int(w.get('capacity', 1)))
        
        return workers[0]


def get_worker_id() -> str:
    """Generate unique worker ID."""
    import socket
    import os
    hostname = socket.gethostname()
    pid = os.getpid()
    return f"{hostname}_{pid}"
