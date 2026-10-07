```python
from abc import ABC, abstractmethod

class Animal:
    def __init__(self, name, weight): self.name, self.weight = name, weight

class CanFly(ABC):
    wingspan: float
    def fly(self): return f"{self.name} flies with {self.wingspan}m wingspan"

class CanSwim(ABC):
    max_depth: float
    def swim(self): return f"{self.name} swims to {self.max_depth}m"

class Duck(Animal, CanFly, CanSwim):
    def __init__(self, name, weight, wingspan, max_depth):
        super().__init__(name, weight); self.wingspan, self.max_depth = wingspan, max_depth
```
These are mixins, i.e. composition of behaviours, and Duck no longer needs FlyingSwimmingAnimal. Test: Duck("D", 1, 0.9, 2).fly() == "D flies with 0.9m wingspan".
