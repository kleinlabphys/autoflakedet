import time
from functools import wraps

def wait_until_ready(max_cycles=20, cycle_wait=0.5):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            for _ in range(max_cycles):
                ready = func(self, *args, **kwargs)
                if ready:
                    return ready
                time.sleep(cycle_wait)
        return wrapper
    return decorator

