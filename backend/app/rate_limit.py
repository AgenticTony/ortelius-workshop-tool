"""Shared rate limiter for the API.

Lives in its own module to avoid a circular import: routes need the limiter
to decorate handlers, and main.py needs it to wire the exception handler +
middleware. Importing from here breaks the cycle (main imports routes, routes
import the limiter, but the limiter imports nothing from the app).

In-memory store (single instance). Multi-instance deployment would need a
shared backend (redis) — out of scope for the prototype.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
