# Wrong: a lock around a deque, which the prompt rules out.
import threading
from collections import deque


class SPSCQueue:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = deque()
        self.lock = threading.Lock()

    def push(self, item):
        with self.lock:
            if len(self.items) == self.capacity:
                return False
            self.items.append(item)
            return True

    def pop(self):
        with self.lock:
            return self.items.popleft() if self.items else None
