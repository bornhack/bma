"""Define a ContextVar to hold the current request to make it accessible from everywhere.

To use the request object when it isn't available:

    from utils.request import context_request
    request = context_request.get()
    print(request.user) # or whatever

Highly experimental code. May blow up at any time.
"""
import contextvars
context_request = contextvars.ContextVar('request', default=None)
