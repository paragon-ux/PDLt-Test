```python
from __future__ import annotations
from typing import Protocol

# Original entities (verbatim) -------------------------------------------------
class Animal:
    def __init__(self, name: str, weight: float):
        self.name = name
        self.weight = weight

class FlyingAnimal(Animal):
    def __init__(self, name: str, weight: float, wingspan: float):
        super().__init__(name, weight)
        self.wingspan = wingspan
    def fly(self) -> str:
        return f"{self.name} flies with {self.wingspan}m wingspan"

class SwimmingAnimal(Animal):
    def __init__(self, name: str, weight: float, max_depth: float):
        super().__init__(name, weight)
        self.max_depth = max_depth
    def swim(self) -> str:
        return f"{self.name} swims to {self.max_depth}m"

class FlyingSwimmingAnimal(FlyingAnimal, SwimmingAnimal):
    def __init__(self, name: str, weight: float, wingspan: float, max_depth: float):
        FlyingAnimal.__init__(self, name, weight, wingspan)
        SwimmingAnimal.__init__(self, name, weight, max_depth)

class DivingBird(FlyingSwimmingAnimal):
    def __init__(self, name: str, weight: float, wingspan: float, max_depth: float, dive_speed: float):
        super().__init__(name, weight, wingspan, max_depth)
        self.dive_speed = dive_speed
    def dive(self) -> str:
        return f"{self.name} dives at {self.dive_speed}m/s"

# Refactored design using composition and Protocols --------------------------
class Flyable(Protocol):
    def fly(self) -> str: ...

class Swimmable(Protocol):
    def swim(self) -> str: ...

class FlyingBehavior:
    def __init__(self, wingspan: float):
        self.wingspan = wingspan
    def fly(self, owner_name: str) -> str:
        return f"{owner_name} flies with {self.wingspan}m wingspan"

class SwimmingBehavior:
    def __init__(self, max_depth: float):
        self.max_depth = max_depth
    def swim(self, owner_name: str) -> str:
        return f"{owner_name} swims to {self.max_depth}m"

class RefactoredAnimal:
    def __init__(self, name: str, weight: float):
        self.name = name
        self.weight = weight

class RefactoredDuck(RefactoredAnimal, Flyable, Swimmable):
    def __init__(self, name: str, weight: float, wingspan: float, max_depth: float):
        super().__init__(name, weight)
        self._fly_behavior = FlyingBehavior(wingspan)
        self._swim_behavior = SwimmingBehavior(max_depth)
    def fly(self) -> str:
        return self._fly_behavior.fly(self.name)
    def swim(self) -> str:
        return self._swim_behavior.swim(self.name)

class RefactoredDivingBird(RefactoredAnimal, Flyable, Swimmable):
    def __init__(self, name: str, weight: float, wingspan: float, max_depth: float, dive_speed: float):
        super().__init__(name, weight)
        self._fly_behavior = FlyingBehavior(wingspan)
        self._swim_behavior = SwimmingBehavior(max_depth)
        self.dive_speed = dive_speed
    def fly(self) -> str:
        return self._fly_behavior.fly(self.name)
    def swim(self) -> str:
        return self._swim_behavior.swim(self.name)
    def dive(self) -> str:
        return f"{self.name} dives at {self.dive_speed}m/s"

# Unit tests ------------------------------------------------------------------
import unittest

class TestParity(unittest.TestCase):
    def test_duck(self):
        # Original hierarchy
        duck_orig = FlyingAnimal('Daffy', 5.0, 0.5)
        # Add swimming capability via inheritance simulation
        class DuckOriginal(FlyingAnimal, SwimmingAnimal):
            def __init__(self, name, weight, wingspan, max_depth):
                FlyingAnimal.__init__(self, name, weight, wingspan)
                SwimmingAnimal.__init__(self, name, weight, max_depth)
        duck_orig = DuckOriginal('Daffy', 5.0, 0.5, 1.0)
        # Refactored hierarchy
        duck_ref = RefactoredDuck('Daffy', 5.0, 0.5, 1.0)
        self.assertEqual(duck_orig.fly(), duck_ref.fly())
        self.assertEqual(duck_orig.swim(), duck_ref.swim())

    def test_diving_bird(self):
        bird_orig = DivingBird('Albatross', 10.0, 2.0, 30.0, 3.5)
        bird_ref = RefactoredDivingBird('Albatross', 10.0, 2.0, 30.0, 3.5)
        self.assertEqual(bird_orig.fly(), bird_ref.fly())
        self.assertEqual(bird_orig.swim(), bird_ref.swim())
        self.assertEqual(bird_orig.dive(), bird_ref.dive())

if __name__ == '__main__':
    unittest.main()
```
