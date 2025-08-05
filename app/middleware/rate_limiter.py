import time
from collections import defaultdict
from fastapi import HTTPException, Request
from app.config import Config

class RateLimiter:
    """Rate limiter to prevent API quota exhaustion"""
    
    def __init__(self):
        self.requests_per_minute = defaultdict(list)
        self.requests_per_day = defaultdict(list)
    
    def _clean_old_requests(self, requests_list: list, window_seconds: int):
        """Remove requests older than the window"""
        current_time = time.time()
        return [req_time for req_time in requests_list if current_time - req_time < window_seconds]
    
    def check_rate_limit(self, client_id: str = "default") -> bool:
        """Check if request is within rate limits"""
        if not Config.RATE_LIMIT_ENABLED:
            return True
        
        current_time = time.time()
        
        # Clean old requests
        self.requests_per_minute[client_id] = self._clean_old_requests(
            self.requests_per_minute[client_id], 60
        )
        self.requests_per_day[client_id] = self._clean_old_requests(
            self.requests_per_day[client_id], 86400  # 24 hours
        )
        
        # Check minute limit
        if len(self.requests_per_minute[client_id]) >= Config.MAX_REQUESTS_PER_MINUTE:
            return False
        
        # Check day limit
        if len(self.requests_per_day[client_id]) >= Config.MAX_REQUESTS_PER_DAY:
            return False
        
        # Add current request
        self.requests_per_minute[client_id].append(current_time)
        self.requests_per_day[client_id].append(current_time)
        
        return True
    
    def get_remaining_requests(self, client_id: str = "default") -> dict:
        """Get remaining requests for client"""
        current_time = time.time()
        
        # Clean old requests
        self.requests_per_minute[client_id] = self._clean_old_requests(
            self.requests_per_minute[client_id], 60
        )
        self.requests_per_day[client_id] = self._clean_old_requests(
            self.requests_per_day[client_id], 86400
        )
        
        return {
            "remaining_per_minute": max(0, Config.MAX_REQUESTS_PER_MINUTE - len(self.requests_per_minute[client_id])),
            "remaining_per_day": max(0, Config.MAX_REQUESTS_PER_DAY - len(self.requests_per_day[client_id])),
            "used_per_minute": len(self.requests_per_minute[client_id]),
            "used_per_day": len(self.requests_per_day[client_id])
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    if not rate_limiter.check_rate_limit():
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "limits": {
                    "requests_per_minute": Config.MAX_REQUESTS_PER_MINUTE,
                    "requests_per_day": Config.MAX_REQUESTS_PER_DAY
                }
            }
        )
    
    response = await call_next(request)
    return response 