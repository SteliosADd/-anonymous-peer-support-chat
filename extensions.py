"""
Shared Flask extension instances.

Kept in their own module (instead of app.py) so blueprints can import and
decorate routes with them without a circular import.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# In-memory storage — resets on restart. Good enough for a single-process
# university project; swap in a `storage_uri` (e.g. Redis) for real deployments.
limiter = Limiter(key_func=get_remote_address)
