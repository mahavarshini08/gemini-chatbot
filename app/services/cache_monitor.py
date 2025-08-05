import threading
import time
import logging
from typing import Dict
from app.services.api_service import ApiService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheHealthMonitor:
    """Background service for monitoring and maintaining cache health"""
    
    def __init__(self, api_service: ApiService, check_interval: int = 3600):  # Check every hour
        self.api_service = api_service
        self.check_interval = check_interval
        self.running = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start the background cache monitoring"""
        if self.running:
            logger.info("Cache monitor is already running")
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Cache health monitor started")
    
    def stop_monitoring(self):
        """Stop the background cache monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Cache health monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._check_cache_health()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Cache monitor error: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _check_cache_health(self):
        """Check cache health and take automatic actions"""
        try:
            health_status = self.api_service.get_cache_health_status()
            
            if health_status["overall_health"] == "needs_attention":
                logger.warning(f"Cache health issues detected: {health_status['problematic_batches']}")
                # Automatically fix cache issues
                self.api_service.auto_validate_cache()
            
            elif health_status["overall_health"] == "healthy":
                logger.info(f"Cache health is good: {health_status['healthy_batches']}/{health_status['total_batches']} batches healthy")
            
            elif health_status["overall_health"] == "empty":
                logger.warning("Cache is empty, will be populated on next request")
                
        except Exception as e:
            logger.error(f"Error checking cache health: {str(e)}")
    
    def get_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "cache_health": self.api_service.get_cache_health_status() if self.running else None
        }

# Global cache monitor instance
_cache_monitor = None

def start_cache_monitoring(api_service: ApiService, check_interval: int = 3600):
    """Start the global cache monitoring service"""
    global _cache_monitor
    if _cache_monitor is None:
        _cache_monitor = CacheHealthMonitor(api_service, check_interval)
        _cache_monitor.start_monitoring()
    return _cache_monitor

def stop_cache_monitoring():
    """Stop the global cache monitoring service"""
    global _cache_monitor
    if _cache_monitor:
        _cache_monitor.stop_monitoring()
        _cache_monitor = None

def get_cache_monitor_status() -> Dict:
    """Get the status of the cache monitoring service"""
    global _cache_monitor
    if _cache_monitor:
        return _cache_monitor.get_status()
    return {"running": False, "message": "Cache monitor not initialized"} 