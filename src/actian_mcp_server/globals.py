from contextvars import ContextVar

# Define a global context variable to store the extracted database username.
# It is "Async Safe" - different requests won't overwrite each other.
# Default value is None.
current_username: ContextVar[str | None] = ContextVar("current_username", default=None)