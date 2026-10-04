# Correct with a different interface: shards first, a total capacity split across
# shards, and KeyError for a missing key.
import threading


class Cache:
    def __init__(self, shards=16, max_size=1024):
        per = max(1, max_size // shards)
        self._locks = [threading.RLock() for _ in range(shards)]
        self._maps = [dict() for _ in range(shards)]
        self._per = per

    def _i(self, key):
        return hash(key) % len(self._maps)

    def get(self, key):
        i = self._i(key)
        with self._locks[i]:
            value = self._maps[i].pop(key)  # KeyError when absent
            self._maps[i][key] = value       # reinsert as most recent
            return value

    def put(self, key, value):
        i = self._i(key)
        with self._locks[i]:
            m = self._maps[i]
            m.pop(key, None)
            m[key] = value
            if len(m) > self._per:
                del m[next(iter(m))]
