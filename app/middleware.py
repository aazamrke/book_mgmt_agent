import time
import uuid
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
from app.logging_config import get_logger

logger = get_logger(__name__)

from starlette.middleware.base import BaseHTTPMiddleware

class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracking and performance monitoring"""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            # Add request ID to response headers
            response.headers["x-request-id"] = request_id
            return response
        finally:
            # Log request completion
            duration = time.time() - start_time
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "duration_ms": round(duration * 1000, 2)
                }
            )

async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global error handler for production"""
    
    request_id = getattr(request.state, "request_id", "unknown")
    
    if isinstance(exc, HTTPException):
        logger.warning(
            f"HTTP exception: {exc.detail}",
            extra={"request_id": request_id, "status_code": exc.status_code}
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "request_id": request_id,
                "status_code": exc.status_code
            }
        )
    
    # Log unexpected errors
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={"request_id": request_id},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "status_code": 500
        }
    )

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting application metrics"""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        self.request_count += 1
        
        try:
            response = await call_next(request)
            
            # Track response time
            duration = time.time() - start_time
            self.response_times.append(duration)
            
            # Keep only last 1000 response times
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
            
            return response
            
        except Exception as e:
            self.error_count += 1
            raise e
    
    def get_metrics(self) -> dict:
        """Get current metrics"""
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0
        )
        
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "recent_requests": len(self.response_times)
        }

# Global metrics instance
metrics_middleware = MetricsMiddleware

def get_metrics_data():
    """Get metrics from the middleware instance"""
    # This will be populated by the actual middleware instance
    return {
        "request_count": 0,
        "error_count": 0,
        "error_rate": 0,
        "avg_response_time_ms": 0,
        "recent_requests": 0
    }