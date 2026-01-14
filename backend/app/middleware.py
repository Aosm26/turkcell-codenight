from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from logging_config import get_request_logger
import time
import uuid


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Her HTTP request/response'u logla"""

    async def dispatch(self, request: Request, call_next):
        # Unique request ID oluştur
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Request logger
        logger = get_request_logger(request_id)

        # Request bilgilerini logla
        logger.info(
            f"➡️  {request.method} {request.url.path}",
            extra={
                "extra_data": {
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.query_params),
                    "client_ip": request.client.host if request.client else None,
                }
            },
        )

        # Request'i işle ve süreyi ölç
        start_time = time.time()

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Response logla
            log_method = logger.info if response.status_code < 400 else logger.warning
            log_method(
                f"⬅️  {request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)",
                extra={
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            # Response header'a request_id ekle
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"❌ {request.method} {request.url.path} - Error: {str(e)}",
                extra={
                    "duration_ms": round(duration_ms, 2),
                    "extra_data": {"error": str(e)},
                },
                exc_info=True,
            )
            raise
