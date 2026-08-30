from slowapi import Limiter
from slowapi.util import get_remote_address

# Keys rate limits by client IP address — this is the incoming-request
# throttle (protects your server from any single visitor/bot flooding it),
# separate from the outgoing Groq-quota throttle in generator.py.
limiter = Limiter(key_func=get_remote_address)