from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from starlette.responses import JSONResponse


class RequestGuard:
    """Single-process per-client limits and bounded actual request bodies.

    Forwarded headers are deliberately ignored. Production needs a trusted ingress
    and shared limiter before scaling to multiple workers.
    """
    def __init__(self, app, limit: int, body_limit: int):
        self.app, self.limit, self.body_limit = app, limit, body_limit
        self.requests = defaultdict(deque)
        self.lock = Lock()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope.get("path", "").startswith("/api"):
            return await self.app(scope, receive, send)
        if scope["path"] != "/api/health":
            now = monotonic()
            client = scope.get("client")
            key = client[0] if client else "unknown"
            with self.lock:
                queue = self.requests[key]
                while queue and queue[0] <= now - 60:
                    queue.popleft()
                exceeded = len(queue) >= self.limit
                if not exceeded:
                    queue.append(now)
                if len(self.requests) > 10000:
                    for old_key in list(self.requests)[:1000]:
                        if self.requests[old_key] and self.requests[old_key][-1] <= now - 60:
                            del self.requests[old_key]
            if exceeded:
                return await JSONResponse({"detail": "Request limit reached. Please try again in a minute."}, status_code=429, headers={"Retry-After": "60"})(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.body_limit:
                return await JSONResponse({"detail": "Request body is too large."}, status_code=413)(scope, receive, send)
            if not message.get("more_body", False):
                break
        sent = False

        async def bounded_receive():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)

