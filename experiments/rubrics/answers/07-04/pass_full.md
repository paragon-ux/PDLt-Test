```python
import os
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class DbConfig:
    host: str = "localhost"
    port: int = 5432
    @classmethod
    def from_env(cls, env=os.environ):            # the only place the environment is read
        return cls(env.get("DB_HOST", "localhost"), int(env.get("DB_PORT", "5432")))
    def url(self): return f"postgresql://{self.host}:{self.port}/mydb"

class Database(Protocol):
    def execute(self, sql: str) -> str: ...

class FakeUrlDatabase:
    def __init__(self, config: DbConfig): self.config = config
    def execute(self, sql): return f"[result of '{sql}' from {self.config.url()}]"

class QueryService:
    def __init__(self, db: Database, config: DbConfig):
        self.db, self.config = db, config
        self._cache, self._requests = {}, 0
    def query(self, sql):
        self._requests += 1
        if sql in self._cache:
            return self._cache[sql]
        result = self.db.execute(sql)
        self._cache[sql] = result
        return result
    def get_stats(self):
        return {'requests': self._requests, 'cache_size': len(self._cache), 'host': self.config.host}
    def reset(self):
        self._cache, self._requests = {}, 0
```
Tests:
```python
from unittest.mock import Mock
def test_query_with_mock_db():
    db = Mock(); db.execute.return_value = "ROWS"
    svc = QueryService(db, DbConfig("testhost", 1))
    assert svc.query("SELECT 1") == "ROWS" and svc.query("SELECT 1") == "ROWS"
    db.execute.assert_called_once_with("SELECT 1")
    assert svc.get_stats() == {'requests': 2, 'cache_size': 1, 'host': 'testhost'}
    svc.reset(); assert svc.get_stats()['requests'] == 0
```
