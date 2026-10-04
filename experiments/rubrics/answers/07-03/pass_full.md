```python
from dataclasses import dataclass
from typing import Protocol

class Flyer(Protocol):
    def fly(self, name: str) -> str: ...
class Swimmer(Protocol):
    def swim(self, name: str) -> str: ...
class Diver(Protocol):
    def dive(self, name: str) -> str: ...

@dataclass
class Flying:
    wingspan: float
    def fly(self, name): return f"{name} flies with {self.wingspan}m wingspan"

@dataclass
class Swimming:
    max_depth: float
    def swim(self, name): return f"{name} swims to {self.max_depth}m"

@dataclass
class Diving:
    dive_speed: float
    def dive(self, name): return f"{name} dives at {self.dive_speed}m/s"

class Animal:
    def __init__(self, name, weight, flying: Flyer | None = None, swimming: Swimmer | None = None,
                 diving: Diver | None = None):
        self.name, self.weight = name, weight
        self._flying, self._swimming, self._diving = flying, swimming, diving
    def fly(self):
        if not self._flying: raise AttributeError(f"{self.name} cannot fly")
        return self._flying.fly(self.name)
    def swim(self):
        if not self._swimming: raise AttributeError(f"{self.name} cannot swim")
        return self._swimming.swim(self.name)
    def dive(self):
        if not self._diving: raise AttributeError(f"{self.name} cannot dive")
        return self._diving.dive(self.name)

def make_duck(name="Duck", weight=1.2):
    return Animal(name, weight, flying=Flying(0.9), swimming=Swimming(2))

def make_diving_bird(name, weight, wingspan, max_depth, dive_speed):
    return Animal(name, weight, Flying(wingspan), Swimming(max_depth), Diving(dive_speed))
```
Tests:
```python
def test_parity():
    duck = make_duck()
    assert duck.fly() == "Duck flies with 0.9m wingspan" and duck.swim() == "Duck swims to 2m"
    gannet = make_diving_bird("Gannet", 3, 1.8, 20, 24)
    assert gannet.fly() == "Gannet flies with 1.8m wingspan"
    assert gannet.swim() == "Gannet swims to 20m"
    assert gannet.dive() == "Gannet dives at 24m/s"
    assert all(len(cls.__bases__) == 1 for cls in (Animal, Flying, Swimming, Diving))
```
