"""Shared rate limiter for the API.

Lives in its own module to avoid a circular import: routes need the limiter
to decorate handlers, and main.py needs it to wire the exception handler +
middleware. Importing from here breaks the cycle (main imports routes, routes
import the limiter, but the limiter imports nothing from the app).

In-memory store (single instance). Multi-instance deployment would need a
shared backend (redis) — out of scope for the prototype.
"""

from slowapi import Limiter
from slowapi.util import get_ipaddr, get_remote_address


def client_key(request) -> str:
    """Resolve the rate-limit key for a request.

    Behind a reverse proxy / load balancer the raw peer address is the proxy's
    IP, so every client would share one limit and the limiter would be
    effectively disabled. Trust ``X-Forwarded-For`` when the proxy set it
    (configure your proxy to overwrite, not append, the header), and fall back
    to the direct peer for local dev / direct connections.
    """
    return get_ipaddr(request) or get_remote_address(request)


limiter = Limiter(key_func=client_key)
